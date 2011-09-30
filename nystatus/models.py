# Python imports
import subprocess
from helpers import reSTify
import datetime

# Django imports
from django.db import models
from settings import SVN_PATH

class ZopeInstance(models.Model):
    instance_name = models.CharField(max_length=30)
    # slash ended:
    url = models.URLField(help_text=("Please enter an URL to any portal site "
                                     "installed on your zope instance"))
    private_key = models.CharField('Edw productsinfo key', max_length=80,
         help_text=("Log into ZMI and in Root click the Properties Tab. "
                    "Copy and paste here the edw-productsinfo-key for auth purposes."))
    date_added = models.DateField(auto_now_add=True)
    # last time the instance has been queried for info
    date_checked = models.DateTimeField(null=True, blank=True)
    # revisit interval in days
    revisit = models.PositiveIntegerField("Revisit (days) [not used]",default=1)
    products = models.ManyToManyField('Product', through='OnlineProduct')
    no_products = models.PositiveSmallIntegerField('Product Count', default=0)
    up_to_date = models.BooleanField(default=True)
    status = models.CharField(max_length=100, default='Just added')

    def __unicode__(self):
        return self.instance_name # + ' [' + str(self.pk) + ']'

class Product(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    origin = models.CharField(
                 max_length=1, 
                 choices=(('z','Zope',), ('n','Naaya'),
                         ('o','Other'), ('u','Unknown')),
                 default='u'
                )
    my_notes = models.TextField('Notes', blank=True)
    latest_found_version = models.CharField(max_length=15, blank=True)
    use_count = models.PositiveIntegerField(default=0)
    repo_type = models.CharField(max_length='3', default='svn',
                                 choices=(('svn', 'Subversion'),))
    repo_path = models.CharField(max_length=255, null=True, blank=True,
                                 default=None,
                                 help_text='For now, only Subversion URI paths, e.g. https://svn.eionet.europa.eu/repositories/Naaya/trunk/eggs/naaya-survey/')

    def __unicode__(self):
        return self.name # + ' [' + str(self.pk) + ']'

    def save(self):
        if self.repo_path and not self.repo_path.endswith('/'):
            self.repo_path += '/'
        super(Product, self).save()

    class Meta:
        ordering = ('name', )

class OnlineProduct(models.Model):
    """Many-to-many relation between ZopeInstance and Product"""
    zopeinstance = models.ForeignKey(ZopeInstance)
    product = models.ForeignKey(Product)
    version = models.CharField('Installed version', max_length=15, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_checked = models.DateTimeField(auto_now=True)
    latest_version = models.BooleanField(default=True)

    def __unicode__(self):
        return str(self.zopeinstance) + ' - ' + str(self.product)

class Portal(models.Model):
    """Describes a portal site inside Zope instance"""
    portal_name = models.CharField(max_length=30)
    # slash ended:
    url = models.URLField(db_index=True)
    parent_instance = models.ForeignKey(ZopeInstance)
    date_added = models.DateField(auto_now_add=True)
    date_checked = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=100, default='Just added')
    no_errors = models.PositiveIntegerField('Error count', default=0)

    def __unicode__(self):
        return self.portal_name[0].upper() + self.portal_name[1:]

class Error(models.Model):
    """One error out of an error log"""
    # model key is (error_id, portal)
    error_hash = models.CharField(max_length=32, db_index=True, unique=True)
    error_type = models.CharField(max_length=20, db_index=True)
    error_name = models.CharField(max_length=200)
    count = models.PositiveIntegerField('Occurrences', default=1)
    portal = models.ForeignKey(Portal, db_index=True)
    date = models.DateTimeField()
    url = models.URLField()
    solved = models.BooleanField(default=False, db_index=True)
    traceback = models.TextField()

class Error_id(models.Model):
    """one error may have multiple occurrences, save them here"""
    error = models.ForeignKey(Error, db_index=True)
    err_id = models.CharField(max_length=40, db_index=True)

    def url_clickable(self):
        return "<a href='%s' target='_blank'>%s</a>" % (self.url, self.url)
    url_clickable.allow_tags = True

    def __unicode__(self):
        return self.err_id

class Release(models.Model):
    """
    Information about a release, including extended changelog, last revision.
    Key is (product, version)

    """
    product = models.ForeignKey(Product, db_index=True, null=True)
    version = models.CharField(max_length=15, default='', db_index=True)
    # datev is None for unreleased
    datev = models.DateField('Version Release Date', null=True, blank=True,
                             default=None)
    changelog = models.TextField(help_text='This is mirrored with package changelog')

    # Repository related fields:
    number = models.CharField('Last Revision', max_length=40, db_index=True,
                              default='r',
                              help_text='Revision number or commit id')
    author = models.CharField(max_length=16, db_index=True)
    message = models.TextField('Commit Message')
    datec = models.DateTimeField('Date Commited', null=True)

    # _THIS_ is actual extra changelog
    obs = models.TextField('Detailed Information',
                           help_text=('Write here any changes with external behavior. '
                                      'Use reStructured text format.'))
    #record_type = models.CharField('Type', max_length=1, default='o',
    #                               choices=(('f', 'Feature'), ('b', 'Bug fix'),
    #                                        ('r', 'Refactoring'), ('o', 'Other')
    #                                       ),
    #                               db_index=True)
    also_affects = models.ManyToManyField(Product, null=True, blank=True,
                                          verbose_name='Other affected products',
                                          db_index=True, related_name='affected')
    doc_update = models.BooleanField('Documentation Updated', default=False,
                                 help_text='Check if documentation was updated',
                                 db_index=True)
    requires_update = models.BooleanField('Requires Update', default=False,
                              help_text='Check if update procedure is required',
                              db_index=True)
    update_info = models.TextField('Update Manual', blank=True, null=True,
                   help_text=('If `requires update`, provide full info here: '
                              'scripts, procedures, tracebacks, common issues.'
                              ' Use reStructured text format.'))

    # Model specific
    date = models.DateTimeField('Last updated', auto_now=True)


def Release_update_or_add(product, version, datev, changelog):
    (rel, c) = Release.objects.get_or_create(product=product, version=version)
    rel.datev = datev
    rel.changelog = changelog
    rel.save()
    return c
