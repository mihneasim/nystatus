# Python imports
import simplejson as json
import urllib2
from urllib import quote
import re
import sys
import os.path
import datetime
import hashlib

# Django connection
crt = os.path.dirname(os.path.realpath(__file__))
DJANGO_PATH = crt[:crt.rfind('/')]
if DJANGO_PATH not in sys.path:
    sys.path.append(DJANGO_PATH)
from django.core.management import setup_environ
import settings
setup_environ(settings)

# Django imports
from nystatus.models import *
from django.db.models import Q

class Client(object):
    """Our json client for grabing info"""
    rpc_getInstanceInfo = 'products.info/'
    rpc_getPortals = 'portals.info/'
    rpc_getErrors = 'portal.errors/'

    def update_info(self, instance_id):
        """Downloads current status of installed products
        Updates database if successful

        """
        instance = ZopeInstance.objects.get(pk=instance_id)
        (products, success) = self.grab_json(instance)
        if success:
            self.update_products(instance,products)
        # grab_json handles error if not successful
        # and saves error log in instance.status, no action required here

    def grab_json(self, instance):
        """Returns (Products,Boolean) where Boolean
        states whether the Product list should be saved by update_products

        Some grabs could return fake empty products results
        e.g. when key auth fails, so always check Boolean

        """
        if instance.url[-1:] != '/':
            instance.url += '/'
        try:
            h = urllib2.urlopen(instance.url + quote(self.rpc_getInstanceInfo +
                                                     instance.private_key))
        except Exception, e:
            instance.status = 'Can not connect to remote website: ' + str(e)
            instance.date_checked = datetime.datetime.now()
            instance.save()
            return ([], False)

        products = json.loads(h.read())

        if isinstance(products,dict):
            message = products.popitem()
            instance.status= 'Error: ' + str(message[1])
            instance.date_checked = datetime.datetime.now()
            instance.save()
            return ([], False)
        else:
            # we have logged in and page returned json output
            return (products, True)

    def update_products(self, instance, products):
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
                latest_version = self.later_version(
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
                if (p['latest_version'] != relation.latest_version or
                    p['version'] != relation.version):
                    # must update latest version status
                    relation.latest_version = p['latest_version']
                    relation.version = p['version']
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
        instance.date_checked = datetime.datetime.now()
        instance.save()

    def cmp_versions(self, v1, v2):
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

    def later_version(self, v1, v2):
        """return the later version"""
        compare = self.cmp_versions(v1,v2)
        if compare == 1:
            return v1
        else:
            return v2

    def update_portals(self, instance, json_str=''):
        """Grabs existing products on a zope instance
        and updates database
        Always do it after at least one update_products
        which normalizes instance url

        """
        if not json_str:
            url = instance.url + self.rpc_getPortals + \
                  quote(instance.private_key)
            try:
                h = urllib2.urlopen(url)
            except Exception:
                return
            json_str = h.read()
        portals = json.loads(json_str)
        if isinstance(portals, dict):
            return
        u = instance.url
        # portals = [ u[:u[:-1].rfind('/') + 1] + p + '/' for p in portals ]
        portals = [ u + 'aq_parent/' + p + '/' for p in portals ]
        # delete portals not found anymore
        Portal.objects.filter(parent_instance=instance).exclude(url__in=portals).delete()
        current = Portal.objects.filter(parent_instance=instance)
        # exclude portals already in db
        for c in current:
            try:
                exists = portals.index(c.url)
                portals.pop(exists)
            except ValueError:
                pass
        # insert new found portals
        for p in portals:
            p_obj = Portal(portal_name=p[p[:-1].rfind('/')+1:-1], url=p,
                           parent_instance=instance)
            p_obj.save()

    def update_errors(self, instance, portal=None, json_str=''):
        """Grabs errors from all portals belonging to instance
        and syncs with errors in database
        Always do it after at least one update_portals

        """
        if not json_str:
           portals = Portal.objects.filter(parent_instance=instance)
        else:
            portals = [portal]
        for portal in portals:
            try:
                if not json_str:
                    h = urllib2.urlopen(portal.url + self.rpc_getErrors +
                                        quote(instance.private_key))
                    json_str_ret = h.read()
                else:
                    json_str_ret = json_str
            except Exception, e:
                portal.status = 'Can not connect to remote site: ' + str(e)
                portal.date_checked = datetime.datetime.now()
                portal.save()
                continue
            errors = json.loads(json_str_ret)
            if isinstance(errors, dict):
                message = errors.popitem()
                portal.status = 'Error: ' + str(message[1])
                portal.date_checked = datetime.datetime.now()
                portal.save()
            else:
                hashes = {}
                for e in errors:
                    # for backwards compat with edw.productsinfo 0.3
                    if 'traceback' not in e.keys():
                        e['traceback'] = ''
                    e['error_hash'] = hashlib.md5('|'.join([str(portal.pk),
                                                           e['error_type'],
                                                           e['error_name'],
                                                           e['traceback']
                                                           ])
                                                 ).hexdigest()
                    if e['error_hash'] in hashes.keys():
                        hashes[e['error_hash']].append(e)
                    else:
                        hashes[e['error_hash']] = [e]
                existing = [e.error_hash for e in
                            Error.objects.filter(error_hash__in=hashes.keys(),
                            portal=portal)]
                to_insert = list(set(hashes.keys()) - set(existing))

                for hash in to_insert:
                    new_er = Error(error_hash=hash,
                                   error_name=hashes[hash][0]['error_name'],
                                   error_type=hashes[hash][0]['error_type'],
                                   portal=portal,
                                   url=portal.url + hashes[hash][0]['url'],
                                   date=datetime.datetime.fromtimestamp(float(hashes[hash][0]['date'])),
                                   traceback=hashes[hash][0]['traceback'],
                                   count=len(hashes[hash])
                                   )
                    new_er.save()
                    for e in hashes[hash]:
                        new_err_id = Error_id(error=new_er,
                                              err_id=e['id'])
                        new_err_id.save()

                for hash in existing:
                    base_error = Error.objects.get(error_hash=hash)
                    existing_ids = [e.err_id for e in
                                    Error_id.objects.filter(error=base_error)]
                    got_ids = [ e['id'] for e in hashes[hash] ]
                    to_insert = list(set(got_ids) - set(existing_ids))
                    base_error.count += len(to_insert)
                    for e in hashes[hash]:
                        if e['id'] in to_insert:
                            new_err_id = Error_id(error=base_error,
                                                  err_id=e['id'])
                            new_err_id.save()

                portal.status = 'OK'
                portal.no_errors += len(to_insert)
                portal.date_checked = datetime.datetime.now()
                portal.save()

if __name__ == "__main__":
    client = Client()
    if len(sys.argv) < 2:
        # check instances ready for product update
        instances = ZopeInstance.objects.filter(
                    Q(date_checked__lte=datetime.datetime.now() - datetime.timedelta(0.9))
                    | Q(date_checked__isnull=True))
        # 0.9 - haven't been checked for almost a day - include some delay
        for i in instances:
            # update Products' Versions info
            client.update_info(i.pk)
            # update Portals running in instance
            client.update_portals(i)
            # update logs from error logs for each portal in instance
            client.update_errors(i)
    else:
        try:
            # force update of particular instance
            instance_id = int(sys.argv[1])
            try:
                i = ZopeInstance.objects.get(pk=instance_id)
                client.update_info(instance_id)
                client.update_portals(i)
                client.update_errors(i)
            except ZopeInstance.DoesNotExist:
                print "Instance pk=" + i + " does not exist"
        except ValueError:
            if sys.argv[1] == 'errors':
                instances = ZopeInstance.objects.all()
                for inst in instances:
                    client.update_errors(inst)
