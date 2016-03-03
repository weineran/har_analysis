import json
from datetime import datetime, timedelta
import sys,os
from har import Har
from aqualab.plot.mCdf import keyedCdf
from dnshar import get_hostname

def plot_object_size_distribution():

    objs = []
    for fname in os.listdir('har_data'):
        print fname

        if not fname.startswith('4g'): continue
        
        site = Har('har_data/%s'%fname)
        
        onload = float(site.pages[0]['pageTimings']['onLoad'])
        page_start_time = datetime.strptime(site.pages[0]['startedDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        onload_time = page_start_time + timedelta(seconds=(onload/1000.0))
        
        request_count = 0
        page_size = 0

        for entry in site.entries:
            
            if entry.startedDateTime > onload_time:
                #print 'Started after onload', page_start_time, onload, onload_time, ent['starttime'], ent['url']
                continue
            if entry.response.bodySize == 0: continue

            request_count += 1
            page_size += entry.response.bodySize
            
            objs.append(entry.response.bodySize)

        print fname, request_count, page_size
        
    cdf = keyedCdf(baseName='obj_size_cdf', xlabel='Size (bytes)')
    for o in objs:
        cdf.insert('Request Size', o)
    cdf.plot('logscalex', plotdir='figs', xlim=[1,1000000])
        
def get_object_distribution():
    hosts = {} #[host] : (name, size)

    for fname in os.listdir('C:\Users\Andrew\OneDrive\Documents\Northwestern\Research\mobile_ads\ISE-project\data\4G-NU-false'):
        print fname
        if not fname.startswith('4g'): continue

        site = Har('har_data/%s'%fname)
        
        url = site.entries[0].request.url

        if url in hosts: continue

        hosts[url] = []
            
    
        onload = float(site.pages[0]['pageTimings']['onLoad'])
        page_start_time = datetime.strptime(site.pages[0]['startedDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        onload_time = page_start_time + timedelta(seconds=(onload/1000.0))
        
        request_count = 0
        page_size = 0


        for entry in site.entries:
            
            if entry.startedDateTime > onload_time:
                #print 'Started after onload', page_start_time, onload, onload_time, ent['starttime'], ent['url']
                continue
            #looking for ALL objects -- actually no
            if entry.response.bodySize == 0: continue

            #add (url, size) tuple
            hosts[url].append((entry.request.url, entry.response.bodySize))

    return hosts


if __name__ == '__main__':
    #plot_object_size_distribution()
    obj_dict = get_object_distribution()

    for host in obj_dict:
        hosts = set()
        for url, size in obj_dict[host]:
            hosts.add(get_hostname(url))
        print '%s\t%s\t%s\t%s' % (host, len(obj_dict[host]), sum([x[1] for x in \
        obj_dict[host]]), len(hosts))
