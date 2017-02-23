from lxml import etree
import urllib2
import urllib
from bs4 import BeautifulSoup, NavigableString
import re
from unidecode import unidecode
from . import worker
import math

'''
    Initialized with a list of query objects, as part of the config
    object, and it writes a list of videos to the Muse server to be downloaded
'''

_DEBUG = False
search_url = 'https://www.youtube.com/results?search_query=%s'
page_search_url = 'https://www.youtube.com/results?search_query=%s&page=%d'

class scout(worker.worker):
    def __init__(self, *args):
        super(scout, self).__init__(*args)
        self._did_num_in_mult = False

    def process(self, query, prog_cb):
        if not self._did_num_in_mult and self._num_in > 0:
            self._num_in = 0
            for q in self.config.getQueries():
                self._num_in += 20 * q.getNum()
            self._did_num_in_mult = True
        prog_cb('Performing Queries')
        for result in self.ScrapeYT(query, prog_cb):
            yield result

    def simScrapeYT(self, query):
        return query

    def ScrapeYT(self, query, prog_cb):
        parser = etree.XMLParser(recover=True)
        #(query_str, q_type, pages) = query.asTuple()
        query_str = query.getQuery()
        q_terms = query.getTerms()
        pages = query.getNum()
        enc_query_str = query.getURLQuery()
        count = 0
        for page in xrange(1, pages+1):
            target = None
            if page == 1:
                target = search_url % (enc_query_str)
            else:
                target = page_search_url % (enc_query_str, page)
            response = urllib2.urlopen(target)
            html = response.read()
            soup = BeautifulSoup(html, 'lxml')
            itercount = 0
            for maindiv in soup.find_all('div', {'class':'yt-lockup-content'}):
                self.eprint('iter'+str(itercount)+'page'+str(page))
                itercount += 1
                title = None
                duration = None # in seconds
                link = None
                uploader = (None, None) # uploader name and link
                age = None
                views = None
                description = None
                checksum = 0
                try:
                    for mainchild in maindiv.children:
                        if mainchild.name == 'h3' and 'yt-lockup-title' in mainchild['class']:
                            title_link = filter(lambda x: 'a' == x.name, mainchild.children)
                            duration_span = filter(lambda x: 'span' == x.name, mainchild.children)
                            assert(len(title_link) is 1)
                            assert(len(duration_span) is 1)
                            title_link = title_link[0]
                            duration_span = duration_span[0]
                            title = title_link.string
                            link = title_link['href']
                            m = re.search('((\d+:)?\d+:\d{2})', duration_span.string)
                            if m is None:
                                continue
                            duration_str = m.group(0)
                            dur = duration_str.split(':')[::-1]
                            if len(dur) < 3:
                                dur.append(u'0')
                            duration = int(dur[0]) + int(dur[1]) * 60 + int(dur[2]) * 3600
                            checksum = checksum ^ int('0001', 2)

                        elif mainchild.name == 'div' and 'yt-lockup-byline' in mainchild['class']:
                            # uploader name
                            upl_name_link = mainchild.contents[0]
                            if isinstance(upl_name_link, NavigableString):
                                continue
                            uploader = (upl_name_link.string, upl_name_link['href'])
                            checksum = checksum ^ int('0010', 2)
                        
                        elif mainchild.name == 'div' and 'yt-lockup-meta' in mainchild['class']:
                            # upload date | play count
                            assert(len(mainchild.contents) is 1 and mainchild.contents[0].name == 'ul')
                            meta_ul = mainchild.contents[0]
                            if (len(meta_ul.contents) is 1):
                                continue # Weird playlist result
                            assert(len(meta_ul.contents) is 2)
                            upl_date_li = meta_ul.contents[0]
                            play_count_li = meta_ul.contents[1]
                            
                            m = re.search('(\d+) (\w+) ago', upl_date_li.string)
                            if m is None:
                                continue
                            (amt, unit) = m.groups()
                            amt = int(amt)
                            if re.match('minute|minutes', unit) is not None:
                                age = amt
                            elif re.match('hour|hours', unit) is not None:
                                age = amt * 60
                            elif re.match('day|days', unit) is not None:
                                age = amt * 24 * 60
                            elif re.match('week|weeks', unit) is not None:
                                age = amt * 7 * 24 * 60
                            elif re.match('month|months', unit) is not None:
                                age = amt * 30 * 24 * 60
                            elif re.match('year|years', unit) is not None:
                                age = amt * 265 * 24 * 60
                            else:
                                raise Exception("Unknown Upload Age")

                            m = re.search('([\d,]+) views', play_count_li.string)
                            if m is None:
                                continue
                            views = int(m.group(1).replace(',',''))
                            checksum = checksum ^ int('0100', 2)

                        elif mainchild.name == 'div' and 'yt-lockup-description' in mainchild['class']:
                            # description
                            try:
                                description = reduce(lambda prev, y: prev + y.string, mainchild.children, '')
                            except TypeError:
                                continue
                            checksum = checksum ^ int('1000', 2)
                except KeyError as err:
                    self.eprint('KeyError - '+str(err))
                    continue

                if checksum != int('1111', 2):
                    self.eprint('checksum failure')
                    continue
                
                count += 1
                
                if _DEBUG:
                    print '---'
                    print title
                    print '%d seconds' % duration
                    print 'https://www.youtube.com%s' % link
                    print uploader
                    print '%d minutes ago' % age
                    print '%d views' % views
                    print description

                if len(title) == 0:
                    self.eprint('title len failure')
                    continue

                if int(duration) > 7 * 60:
                    self.eprint('duration exceeded failure')
                    continue
                
                (upl_name, upl_link) = uploader
                encoded_title = title.encode('utf-8')
                title = unidecode(title)
                upl_name = unidecode(upl_name)
                encoded_description = description.encode('utf-8')
                description = unidecode(description)
                res_id = urllib.unquote_plus(link[link.find('v=')+2:])
                res = {'query_terms':query.getTerms(), 'query':query.getQuery(), 'query_num_pages':query.getNum(), 'candidate':{'title':title, 'encoded_title': encoded_title, 'duration':duration, 'link':link, 'id': res_id, 'uploader_name':upl_name, 'uploader_link':upl_link, 'age':age, 'views':views, 'description':description, 'encoded_description':encoded_description}}
                pct = math.atan(3.0*(count+1)/(20*pages+1))*100.0/math.pi*2
                prog_cb('Searching for Video Candidates (%01.2f%%)' % pct)
                yield res

