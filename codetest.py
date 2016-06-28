import sys
from unidecode import unidecode
import urllib 
reload(sys)
sys.setdefaultencoding("utf-8")

for a in sys.argv:
    print a, len(a)
    a = unicode(a)
    print a, len(a)
    enc = a.encode('utf-8')
    print enc, len(enc)
    print urllib.quote_plus(a.encode('utf-8'))
