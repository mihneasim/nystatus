import os.path
import sys
from datetime import date
import re
import logging
from docutils.utils import new_document
from docutils.parsers.rst import Parser
from docutils.frontend import OptionParser
import subprocess

# Django connection
crt = os.path.dirname(os.path.realpath(__file__))
DJANGO_PATH = crt[:crt.rfind('/')]
if DJANGO_PATH not in sys.path:
    sys.path.append(DJANGO_PATH)
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db.transaction import commit_on_success

from nystatus.models import Release, Release_update_or_add, Product
from nystatus.templatetags.pversion import unpversion, pversion

# CONSTANTS
CHANGELOG_NAME = 'CHANGELOG.rst'

# Pretty rotating logger
LOG_FILENAME = os.path.join(settings.ABS_ROOT, 'var' + os.path.sep + 'changelog_client.log')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=1000000, backupCount=5)
formatter = logging.Formatter('%(levelname)s %(asctime)s: %(message)s', '%d %b %H:%M')
handler.setFormatter(formatter)
logger.addHandler(handler)

class EmptyChangelog(Exception):
    pass

class MalformedChangelog(Exception):
    pass

class MalformedHeader(MalformedChangelog):
    pass

class ChangelogClient(object):

    def __init__(self, product):
        self.product = product
        self.changelog = None
        self.blame = {}
        if self.product.repo_path:
            data = re.compile(r' +([0-9]+) +\S+ (.*)')
            p = subprocess.Popen(('svn blame %s/%s' %
                                  (self.product.repo_path, CHANGELOG_NAME)),
                                 shell=True,
                                 stderr=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 close_fds=True)
            blame = p.communicate('\n')[0]
            chunks = []
            for (lineno, line) in enumerate(blame.split('\n')):
                if not line:
                    continue
                m = data.search(line)
                revision = m.groups()[0]
                chunks.append(m.groups()[1])
                self.blame[lineno] = revision

            self.changelog = '\n'.join(chunks)

    def _get_sortable_version(self, headerline):
        """
        Returns '0001.0002.0003' out of '1.2.3 (2011-09-10|unreleased)'

        """
        if '(' not in headerline:
            raise MalformedHeader("No '(' char found in headerline")
        version = headerline[:headerline.find('(')].strip()
        if version.endswith("-dev"):
            version = version[:-4]
        ints = map(int, version.split("."))
        return ".".join(["%0.4d" % i for i in ints])

    def _get_date(self, headerline):
        """
        Returns datetime.date or None if unreleased
        out of '1.2.3 (2011-09-10|unreleased)'

        """
        pat = re.compile(r'\( *(\d{4}-\d{2}-\d{2}) *\)|\( *(unreleased) *\)',
                         re.I)
        m = pat.search(headerline)
        if m is None:
            raise MalformedHeader("Can not match date or `unreleased`")
        (udate, ureleased) = m.groups()
        if ureleased:
            return None
        else:
            r_date = map(int, udate.split("-"))
            return date(r_date[0], r_date[1], r_date[2])

    def update_changelog(self, changelog):
        """
        Updates changelog in db for wrapped product
        with given `changelog` multiline string

        """
        docsettings = OptionParser(components=(Parser,)).get_default_values()
        document = new_document(u'Changelog Document Instance', docsettings)
        parser = Parser()
        parser.parse(changelog, document)
        if not len(document.children):
            raise EmptyChangelog()

        releases = {}
        for block in document.children:
            headline = block[0].astext()
            r_date = self._get_date(headline)
            version = self._get_sortable_version(headline)
            text = ''
            if len(block) == 1:
                # must be unreleased
                assert(r_date is None)
            else:
                # TODO: figure out a better way to get rst of doctree
                entries = block[1].astext().split(block.child_text_separator)
                text = '* ' + '\n* '.join([e.replace('\n', ' ') for e in entries])
            releases[version] = {'datev': r_date, 'changelog': text}

        found_versions = releases.keys()
        found_versions.sort()
        last_released = Release.objects.filter(product=self.product, datev__isnull=False)
        last_released = last_released.order_by('-datev')

        try:
            last_released = last_released[0]
            last_released_version = last_released.version
        except:
            last_released_version = ''
        after_last_released = False

        needs_blame = []
        for version in found_versions:
            # walk versions in new changelog, from oldest to newest
            if after_last_released:
                needs_blame.append(pversion(version))
                # this is unreleased in db, probably totally changed in changelog
                # update 1 on 1, regardless of version
                (unreleased, c) = Release.objects.get_or_create(product=self.product, datev__isnull=True)
                unreleased.version = version
                unreleased.datev = releases[version]['datev']
                unreleased.changelog = releases[version]['changelog']
                unreleased.save()
                after_last_released = False
            else:
                # either exists in db, either totally new
                added = Release_update_or_add(self.product, version,
                                              releases[version]['datev'],
                                              releases[version]['changelog'])
                if added:
                    needs_blame.append(pversion(version))
                if version == last_released_version:
                    after_last_released = True

        self.update_commit_info(needs_blame)

    def update_commit_info(self, versions):
        """ `versions` is list of versions that need to be rechecked """
        if not self.changelog:
            return
        revisions = {}
        for v in versions:
            for (index, line) in enumerate(self.changelog.split('\n')):
                if line.startswith(v + ' '):
                    revisions[v] = self.blame[index]

        for (version, revision) in revisions.items():
            release = Release.objects.get(product=self.product,
                                          version=unpversion(version))
            # get commit info from svn
            p = subprocess.Popen('svn log %s -r%s' % (self.product.repo_path, revision),
                                 shell=True,
                                 stderr=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 close_fds=True)
            output=p.communicate('\n')[0]
            lines = output.split('\n')
            firstline = lines[1]
            chunks = firstline.split("|")

            # update commit info in db
            release.number = 'r' + str(revision)
            release.author = chunks[1].strip()
            release.message = lines[3]
            release.datec = ' '.join(chunks[2].strip().split(' ')[:2])
            release.save()

    @commit_on_success
    def update(self):
        try:
            self.update_changelog(self.changelog)
        except Exception, e:
            logger.exception("Error in updating product %s" % self.product)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        products = Product.objects.all().exclude(repo_path__isnull=True)
        products = products.exclude(repo_path='')
        for product in products:
            cl = ChangelogClient(product)
            cl.update()
    else:
        product = Product.objects.get(pk=int(sys.argv[1]))
        cl = ChangelogClient(product)
        cl.update()
