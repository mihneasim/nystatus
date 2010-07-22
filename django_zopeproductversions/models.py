from django.db import models

class ZopeInstance(models.Model):
    instance_name = models.CharField(max_length=30)
    url = models.URLField()
    user = models.CharField(max_length=30)
    password = models.CharField(max_length=30)
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
    zopeinstance = models.ForeignKey(ZopeInstance)
    product = models.ForeignKey(Product)
    version = models.CharField('Installed version', max_length=15, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_checked = models.DateTimeField(auto_now=True)
    latest_version = models.BooleanField(default=True)

    def __unicode__(self):
        return str(self.zopeinstance) + ' - ' + str(self.product)
