from har import *
import os
import json

def get_hostname(url):
    
    if url.startswith('https'):
        url = url[8:]
    elif url.startswith('http'):
        url = url[7:]
    else:
        return None

    return url.split('/', 1)[0]    


if __name__ == '__main__':
    print 'hostname\tsize\tonload\ttotal dns time\ttotal time\tdns percentage\tnum domains\tnum objs'

    for fname in os.listdir('har_data'):
        #only want mobile data
        if not fname.startswith('4g'):
            continue
        
        try:
            h = Har('har_data/%s'%fname)
        except:
            continue
        page_name = h.pages[0]['title']
        onContentLoad = h.pages[0]['pageTimings']['onContentLoad']
        onLoad = h.pages[0]['pageTimings']['onLoad']

        urls = []
        hostnames = []
        dns_times = []
        total_times = []
        sizes = []
        
        
        for entry in h.entries:
            
            #not checking for redirects at this point
            if entry.response.status != 200: continue

            urls.append(entry.request.url)
            hostnames.append(get_hostname(entry.request.url))

            dns_times.append(entry.timings.dns)
            total_times.append(entry.timings.all())

            sizes.append(entry.response.bodySize)

        #get host set
        hosts = set()
        for host in hostnames:
            hosts.add(host)

        total_dns = sum([x for x in dns_times if x >= 0])
        total_time = sum(total_times)
        size = sum(sizes)
        print '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s'%(page_name, size, onLoad, total_dns,\
        total_time, (float(total_dns)/total_time),len(hosts), len(urls))

        
        #print hosts

        #for i in range(len(urls)):   
            #print " ", hostnames[i], dns_times[i], total_times[i]

