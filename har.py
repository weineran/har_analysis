import json
from datetime import datetime


def get_hostname(url):
    
    if url.startswith('https'):
        url = url[8:]
    elif url.startswith('http'):
        url = url[7:]
    else:
        return None

    return url.split('/', 1)[0]

class Har(object):
    '''
    entries
    version
    pages
    creator
    '''
    def __init__(self, filename):
        
        self.log = json.load(open(filename))['log']

        self.entries = [Entry(x) for x in self.log['entries']]
        self.version = self.log['version']
        self.pages = self.log['pages']
        self.creator = self.log['creator']

    def get_requests(self):
        
        reqs = []
        for ent in self.entries():
            d = {}
            d['url'] = ent['request']['url']
            d['length'] = float(ent['response']['bodySize'])

            d['type'] = ""
            for h in ent['response']['headers']:
                if h['name'] == 'Content-Type':
                    d['type'] = h['value']
                    break

            #2013-10-24T17:37:31.635Z 
            d['starttime'] = datetime.strptime(ent['startedDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            d['total_time'] = float(ent['time'])
            d['timings'] = ent['timings']

            reqs.append(d)

        return reqs

class Entry(object):
    
    def __init__(self, ent):
        self.entry = ent   # A JSON object
        
        self.startedDateTime = datetime.strptime(self.entry['startedDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        self.time = self.entry['time']

        self.request = Request(self.entry['request'])
        self.response = Response(self.entry['response'])

        self.cache = self.entry['cache']

        self.timings = Timings(self.entry['timings'])

        self.pageref = self.entry['pageref']
        

class Request(object):
    
    def __init__(self, req):
        self.request = req      # a JSON object
        
        self.method = self.request['method']
        self.url = self.request['url']
        self.httpVersion = self.request['httpVersion']
        self.headers = self.request['headers']
        self.queryString = self.request['queryString']
        self.cookies = self.request['cookies']

        self.headersSize = self.request['headersSize']
        self.bodySize = self.request['bodySize']



class Response(object):
    
    def __init__(self, resp):
        self.response = resp

        self.status = self.response['status']
        self.statusText = self.response['statusText']
        self.httpVersion = self.response['httpVersion']
        self.headers = self.response['headers']
        self.cookies = self.response['cookies']

        self.content = self.response['content']

        self.redirectURL = self.response['redirectURL']
        self.headersSize = self.response['headersSize']
        self.bodySize = self.response['bodySize']
        self.contentSize = self.content['size']     # Length of the returned content in bytes. Should be equal to response.bodySize if there is no compression and bigger when the content has been compressed.

class Timings(object):
    
    def __init__(self, tim):
        self.timings = tim      # A JSON Object

        self.blocked = self.timings['blocked']
        self.dns = self.timings['dns']
        self.connect = self.timings['connect']
        self.send = self.timings['send']
        self.wait = self.timings['wait']
        self.receive = self.timings['receive']
        self.ssl = self.timings['ssl']

    def all(self):
        tot = 0

        if self.blocked >= 0: tot += self.blocked
        if self.dns >= 0: tot += self.dns
        if self.connect >= 0: tot += self.connect
        if self.send >= 0: tot += self.send
        if self.wait >= 0: tot += self.wait
        if self.receive >= 0: tot += self.receive
        if self.ssl >= 0: tot += self.ssl

        return tot



