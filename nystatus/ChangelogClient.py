import os.path
import sys

# Django connection
crt = os.path.dirname(os.path.realpath(__file__))
DJANGO_PATH = crt[:crt.rfind('/')]
if DJANGO_PATH not in sys.path:
    sys.path.append(DJANGO_PATH)
from django.core.management import setup_environ
import settings
setup_environ(settings)


class ChangelogClient(object):

    def __init__(self, product):
        self.product = product

    def update_changelog(changelog):
        """
        Updates changelog in db for wrapped product
        with given `changelog` multiline string

        """
        pass
