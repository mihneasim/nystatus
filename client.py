# Python imports
import simplejson as json
from urllib import urlencode
import urllib2
import re
import sys
import os.path
from datetime import datetime, timedelta

# Django Connection
from django.core.management import setup_environ
import settings
setup_environ(settings)

# Django imports
from info.models import *
from django.db.models import Q

class Client(object):
    """Our json client for grabing info"""
    rpc_log_in = 'logged_in'
    rpc_getInstanceInfo = 'manage_getInstanceInfo'

    class MyHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
        """inner class used by urllib2 to keep cookies in redirection"""
        def http_error_302(self, req, fp, code, msg, headers):
            return urllib2.HTTPRedirectHandler.http_error_302(self,
                               req, fp, code, msg, headers)
        http_error_301 = http_error_303 = http_error_307 = http_error_302

    def updateInfo(self, instance_id):
        """Downloads current status of installed products
        Updates database if successful

        """
        instance = ZopeInstance.objects.get(pk=instance_id)
        (products, success) = self.grabJson(instance)
        if success:
            self.updateProducts(instance,products)
        # grabJson handles error if not successful
        # and saves error log in instance.status, no action required here
 
    def grabJson(self, instance):
        """Returns (Products,Boolean) where Boolean
        states whether the Product list should be saved by updateProducts

        Some grabs could return fake empty products results
        e.g. when logging in fails, so always check Boolean

        """
        if instance.url[-1:] != '/':
            instance.url += '/'
        cookieprocessor = urllib2.HTTPCookieProcessor()
        opener = urllib2.build_opener(self.MyHTTPRedirectHandler, cookieprocessor)
        urllib2.install_opener(opener)
        try:
            h = urllib2.urlopen(
                instance.url + self.rpc_log_in,
                urlencode({'submit': 'Login', '__ac_name': instance.user,
                    '__ac_password': instance.password, 'came_from':
                    instance.url + self.rpc_getInstanceInfo})
                )
        except Exception, e:
            instance.status = 'Can not connect to remote website: ' + str(e)
            instance.date_checked = datetime.now()
            instance.save()
            return ([], False)
        if not list(cookieprocessor.cookiejar):
            instance.status = ('Can not login. User/password incorrect or user'
                                   ' does not have manager role')
            instance.date_checked = datetime.now()
            instance.save()
            return ([], False)
        else:
            # we have logged in and page returned json output
            products = json.loads(h.read())
            return (products, True)

    def updateProducts(self, instance, products):
        """Receives a list of current installed products
        Must update database to be conform

        """
        # insert products and get products that exist in db
        # than add them to the many-to-many relation
        no_p = 0
        crt_set = []
        instance.up_to_date = True # initial supposition for instance
        for p in products:
            p['latest_version'] = True # initial suppositions
            p['origin'] = 'u' # Unkown
            if p['name'].lower().find('naaya') != -1:
                p['origin'] = 'n' # Naaya product
            elif p['name'].lower().find('zope') != -1:
                p['origin'] = 'z' # Zope product
            try:
                newp = Product.objects.get(name=p['name'])
                latest_version = self.laterVersion(
                        newp.latest_found_version, p['version'])
                if latest_version != newp.latest_found_version:
                    newp.latest_found_version = latest_version
                    newp.save()
                elif latest_version != p['version']:
                    p['latest_version'] = False
            except Product.DoesNotExist:
                # Product is not in Products table, add it
                newp = Product(name=p['name'],
                               latest_found_version=p['version'],
                               origin=p['origin'])
                newp.save()
            crt_set.append(newp)
            no_p += 1
            # check if product is already assigned to (installed in) instance
            # and then add it
            try:
                relation = OnlineProduct.objects.get(zopeinstance=instance,product=newp)
                # can not use instance.products.add(newp), i defined a through relation
                if not p['latest_version']:
                    # not latest version (anymore), probably must update
                    relation.latest_version = p['latest_version']
                    relation.save()
            except OnlineProduct.DoesNotExist:
                relation = OnlineProduct(version=p['version'],
                                        latest_version=p['latest_version'],
                                        product=newp,
                                        zopeinstance=instance)
                newp.use_count += 1
                newp.save()
                relation.save()
            # True only if all p['latest_version'] are true
            instance.up_to_date &= p['latest_version']
        instance.no_products = no_p
        # now we need to delete previous assigned products
        # that are no longer installed
        # -> objects in instance.products, but not in crt_set
        removed = instance.products.exclude(pk__in=[x.pk for x in crt_set])
        for p in removed:
            p.use_count -= 1
            p.save()
        OnlineProduct.objects.filter(zopeinstance=instance,
            product__in=removed).delete()
        instance.status = 'OK'
        instance.date_checked = datetime.now()
        instance.save()

    def cmpVersions(self, v1, v2):
        """Compares two strings representing
        software versions. Returns 1,-1, or 0
        for gt >, lt <, eq = relations between v1 and v2

        """
        any_separator = re.compile(r'[^A-Z0-9]',re.I)
        single_dashes = re.compile(r'-+')
        v1 = any_separator.sub('-',v1)
        v1 = single_dashes.sub('-',v1)
        v2 = any_separator.sub('-',v2)
        v2 = single_dashes.sub('-',v2)
        # We now have digits/letters
        # separated by single dashes in each version string
        # Represent versions as "words"
        v1w = v1.split('-')
        v2w = v2.split('-')
        for i in range(min(len(v1w),len(v2w))):
            if v1w[i] < v2w[i]:
                return -1
            elif v1w[i] > v2w[i]:
                return 1
        if len(v1w) > len(v2w):
            return 1
        elif len(v1w) < len(v2w):
            return -1
        else:
            return 0

    def laterVersion(self, v1, v2):
        """return the later version"""
        compare = self.cmpVersions(v1,v2)
        if compare == 1:
            return v1
        else:
            return v2

if __name__ == "__main__":
    client = Client()
    if len(sys.argv) < 2:
        # check instances ready for update
        instances =ZopeInstance.objects.filter(
                    Q(date_checked__lte=datetime.now() - timedelta(0.9))
                    | Q(date_checked__isnull=True))
        # 0.9 - haven't been checked for almost a day - include some delay
        for i in instances:
            client.updateInfo(i.pk)
    else:
        # force update of particular instance
        instance_id = sys.argv[1] 
        client.updateInfo(instance_id)
