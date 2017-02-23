import urllib

QUERY_TYPES = ('Artist', 'Track', 'Album')

class query:
    def __init__(self, query_line, terms, num):
        self._query = query_line
        self._terms = terms
        self._terms_dict = dict(self._terms)
        self._num = num
        if type(self._num) == str:
            self._num = int(self._num)
        self._url_query = urllib.quote_plus(self._query.encode('utf-8'))
        #assert(len(raw_query) == 3)
        #self.q_term = raw_query[0]
        #self.q_type = raw_query[1]
        #self.q_pages = raw_query[2]
        #self.url_q_term = urllib.quote_plus(self.q_term.encode('utf-8'))

    def getURLQuery(self):
        return self._url_query

    def getQuery(self):
        return self._query

    def getTerms(self):
        return self._terms
    
    def getTermDict(self):
        return self._terms_dict

    def getNum(self):
        return self._num

    '''
    def stringify(self):
        return '%s:%s:%d' % (self.q_term, self.q_type, self.q_pages)

    def getTerm(self):
        return self.q_term

    def getURLTerm(self):
        return self.url_q_term

    def getType(self):
        return self.q_type

    def getNumPages(self):
        return self.q_pages

    def asTuple(self):
        return (self.q_term, self.q_type, self.q_pages)
    '''
