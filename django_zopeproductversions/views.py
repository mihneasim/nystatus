from django.shortcuts import render_to_response
from models import *
from client import Client

def admin_trigger(self, id):
    client = Client()
    # force update of particular instance
    i =  ZopeInstance.objects.get(pk=id)
    client.update_info(id)
    client.update_portals(i)
    client.update_errors(i)
    
    template = 'admin/trigger.html'
    return render_to_response(template, {'name': i.instance_name})

