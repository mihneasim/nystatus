# Python imports
from docutils import core
from docutils.writers.html4css1 import Writer, HTMLTranslator

from docutils.core import publish_string

def reSTify(string):
    
    class NoHeaderHTMLTranslator(HTMLTranslator):
        def __init__(self, document):
            HTMLTranslator.__init__(self, document)
            self.head = ['', '']
            self.head_prefix = ['', '', '', '', '']
            self.body_prefix = []
            self.body_suffix = []
            self.stylesheet = []

    #_w = Writer()
    #_w.translator_class = NoHeaderHTMLTranslator
    #import pdb; pdb.set_trace()
    #return core.publish_string(string, writer=_w)
    if not string:
        return ''
    return string
    html = publish_string(string, writer_name = 'html')
    return html[html.find('<body>')+6:html.find('</body>')].strip()
