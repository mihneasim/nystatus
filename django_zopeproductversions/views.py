from django.shortcuts import render_to_response
from models import *
from client import Client
import helpers

def admin_trigger(self, id):
    client = Client()
    # force update of particular instance
    i =  ZopeInstance.objects.get(pk=id)
    client.update_info(id)
    client.update_portals(i)
    client.update_errors(i)

    template = 'admin/trigger.html'
    return render_to_response(template, {'name': i.instance_name})

def index(self):
    max_per_page = 50
    commits = Commit.objects.order_by('-date')[:max_per_page]
    def put_rst(c):
        c.obs_rst = helpers.reSTify(c.obs)
    map(put_rst, commits)
    template = 'index.html'
    return render_to_response(template, {'commits': commits})
