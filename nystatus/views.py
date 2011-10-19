import subprocess

from django.shortcuts import render_to_response
from django.template import RequestContext

from models import Release, ZopeInstance, Product
from client import Client
from ChangelogClient import ChangelogClient
import helpers
from settings import ABS_ROOT

def admin_trigger(request, id):
    client = Client()
    # force update of particular instance
    i =  ZopeInstance.objects.get(pk=id)
    client.update_info(id)
    client.update_portals(i)
    client.update_errors(i)

    template = 'admin/trigger.html'
    return render_to_response(template, {'name': i.instance_name})

def admin_product_trigger(request, id):
    # force update of particular product release and change log
    product =  Product.objects.get(pk=id)
    #client = ChangelogClient(product)
    #client.update()

    p = subprocess.Popen(('%s/bin/python %s/nystatus/ChangelogClient.py %s' %
			 (ABS_ROOT, ABS_ROOT, id)),
			 shell=True,
			 stderr=subprocess.PIPE,
			 stdout=subprocess.PIPE,
			 close_fds=True)
    #p.wait()
    template = 'admin/trigger.html'
    return render_to_response(template, {'name': product})

def index(request):
    max_per_page = 50
    releases = Release.objects.order_by('-version')[:max_per_page]
    def prepair(c):
        setattr(c, 'int_number', c.number[1:])
    map(prepair, releases)
    template = 'nystatus/index.html'
    return render_to_response(template, {'releases': releases},
                              context_instance=RequestContext(request))
