# Python imports
import sys
import os.path
from unittest import TestCase, TestSuite, main, makeSuite
import simplejson as json
                
crt = os.path.dirname(os.path.realpath(__file__))
DJANGO_PATH = crt[:crt.rfind('/')]
if DJANGO_PATH not in sys.path:
    sys.path.append(DJANGO_PATH)
from django.core.management import setup_environ
import settings
setup_environ(settings)

# Django imports
from django_zopeproductversions.models import *

# My imports
from client import Client

class ClientTestCase(TestCase):
    instance = 'xxxTesting Instancexxx'
    url = 'http://testing.test'
    json_str = ('[{"version": "0.0.0-1", "name": "Fictional prod 0"}, {"version":'
    '"1.0.1-2", "name": "Fictional prod 1"}, {"version": "2.0.2-3", "name":'
    '"Fictional prod 2"}, {"version": "3.0.3-4", "name": "Fictional prod 3"}]')
    pcount = 4
    ins = None
    cl = Client()

    def setUp(self):
        # will throw exception for first test case
        try:
            self.ins = ZopeInstance.objects.get(instance_name=self.instance)
        except Exception:
            pass

    def initial_setup(self):
        ins = ZopeInstance(instance_name=self.instance, url=self.url)
        ins.save()

    def test_0added_instance(self):
        # make sure it's clean
        self.clean_test_setup()
        self.initial_setup()
        ins = ZopeInstance.objects.get(instance_name=self.instance)
        self.cl.updateProducts(ins,json.loads(self.json_str))
        ins = ZopeInstance.objects.get(pk=ins.pk)
        self.assertEqual(ins.up_to_date,True)
        self.assertEqual(ins.status,'OK')
        self.assertEqual(ins.no_products,self.pcount)

    def test_1added_products(self):
        products = self.ins.products.all()
        self.assertEqual(len(products),self.pcount)
        self.assertEqual(products[0].use_count,1)

    def test_2changed_products(self):
        # Simulate we now have only one product
        # newer than the one existent
        only_one = '[{"version": "0.0.0-2", "name": "Fictional prod 0"}]'
        self.cl.updateProducts(self.ins,json.loads(only_one))
        ins = ZopeInstance.objects.get(pk=self.ins.pk)
        self.assertEqual(self.ins.no_products,1)
        prods = Product.objects.filter(name__startswith="Fictional prod") \
                               .order_by('name')
        # prod count must be unchanged - functional prod existed
        self.assertEqual(len(prods),self.pcount)
        self.assertEqual(prods[0].latest_found_version,"0.0.0-2")
        self.assertEqual(prods[0].use_count,1)
        self.assertEqual(prods[1].use_count,0)

    def test_3failed_grab(self):
        (p, success) = self.cl.grabJson(self.ins)
        self.assertFalse(success)
        self.ins = ZopeInstance.objects.get(pk=self.ins.pk)
        self.assertEqual(self.ins.status.find("Can not connect"),0)
        self.clean_test_setup()

    def assertVersion(self,v,v_latest):
        self.assertEqual(self.cl.laterVersion(v[0],v[1]),v_latest)

    def test_compare_versions(self):
        self.assertVersion(("0.0.0.1","0.0.0.0.1"),"0.0.0.1")
        self.assertVersion(("0.0.1","0.1"),"0.1")
        self.assertVersion(("0","0.1"),"0.1")
        self.assertVersion(("1-b","1"),"1-b")
        self.assertVersion(("22.34","22.33"),"22.34")
        self.assertVersion(("22.34","22"),"22.34")
        self.assertVersion(("22","22.33"),"22.33")

    def clean_test_setup(self):
        OnlineProduct.objects.filter(zopeinstance__instance_name__exact=self.instance).delete()
        Product.objects.filter(name__startswith="Fictional prod ").delete()
        ZopeInstance.objects.filter(instance_name__exact=self.instance).delete()

def test_suite():
    return TestSuite((makeSuite(ClientTestCase), ))

if __name__=='__main__':
    main(defaultTest='test_suite')
