import urllib

QUERY_TYPES = ('Artist', 'Track', 'Album', '*')

class TBTYQuery:
    def __init__(self, raw_query):
        assert(len(raw_query) == 3)
        self.q_term = raw_query[0]
        self.q_type = raw_query[1]
        self.q_pages = raw_query[2]
        self.url_q_term = urllib.quote_plus(self.q_term.encode('utf-8'))

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
