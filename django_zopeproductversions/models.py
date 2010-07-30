from django.db import models

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

    def __unicode__(self):
        return self.name # + ' [' + str(self.pk) + ']'

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
    error_id = models.CharField(max_length=40, db_index=True)
    error_type = models.CharField(max_length=20, db_index=True)
    error_name = models.CharField(max_length=200)
    portal = models.ForeignKey(Portal, db_index=True)
    date = models.DateTimeField()
    url = models.URLField()
    solved = models.BooleanField(default=False, db_index=True)

    def url_clickable(self):
        return "<a href='%s' target='_blank'>%s</a>" % (self.url, self.url)
    url_clickable.allow_tags = True

    def __unicode__(self):
        return self.error_type
