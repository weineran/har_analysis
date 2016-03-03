from har import *
import os
import json
import argparse

def parse_args():
    parser = argparse.ArgumentParser(
            description='Not sure yet!')

    parser.add_argument('data_path', type=str,
        help="The path of the directory containing the har data to analyze")
    parser.add_argument('-n', '--network', type=str,
        help="choices are {4G, WiFi, wired}")
    parser.add_argument('-l', '--location', type=str,
        help="the location where the data was collected from")
    parser.add_argument('-b', '--isBlockingAds', type=str,
        help="True or False to indicate whether ad-blocker was enabled during measurements")

    return parser.parse_args()

def get_hostname(url):
    
    if url.startswith('https'):
        url = url[8:]
    elif url.startswith('http'):
        url = url[7:]
    else:
        return None

    return url.split('/', 1)[0]    


if __name__ == '__main__':
    args = parse_args()
    data_path = args.data_path
    network = args.network
    location = args.location
    isBlockingAds = args.isBlockingAds
    if isBlockingAds is None:
        pass
    elif isBlockingAds.upper() == "FALSE":
        isBlockingAds = False
    elif isBlockingAds.upper() == "TRUE":
        isBlockingAds = True
    else:
        isBlockingAds = "Other"
    

    print 'hostname\tbodySize (bytes)\tcontentSize (bytes)\tonload (ms)\ttotal dns time (ms)\ttotal time (ms) \tdns percentage\tnum domains\tnum objs\tnetwork\tlocation\tisBlockingAds\tfilename'

    for fname in os.listdir(data_path):
        # flagged a few files to ignore
        if fname.startswith('0'):
            continue
        
        full_path = os.path.join(data_path, fname)

        try:
            h = Har(full_path)
        except Exception as e:
            print 'skipped ' + fname + '.  error info: ' + str(e)
            continue
        page_name = h.pages[0]['title']
        onContentLoad = h.pages[0]['pageTimings']['onContentLoad']
        onLoad = h.pages[0]['pageTimings']['onLoad']

        urls = []
        hostnames = []
        dns_times = []
        total_times = []
        sizes = []          # "bodySize"
        contentSizes = []
        
        
        for entry in h.entries:
            
            #not checking for redirects at this point
            if entry.response.status != 200: continue

            urls.append(entry.request.url)
            hostnames.append(get_hostname(entry.request.url))

            dns_times.append(entry.timings.dns)
            total_times.append(entry.timings.all())

            sizes.append(entry.response.bodySize)
            contentSizes.append(entry.response.contentSize)

        #get host set
        hosts = set()
        for host in hostnames:
            hosts.add(host)

        if "NU" in fname: location = "NU"
        elif "Home" in fname: location  = "Home"
        elif location is not None: location = location
        else: location = "Other"

        if "4G" in fname: network = "4G"
        elif "WiFi" in fname: network = "WiFi"
        elif "wired" in fname: network = "wired"
        elif network is not None: network = network
        else: network = "Other"

        if "NoBlock" in fname: isBlockingAds = False
        elif "YesBlock" in fname: isBlockingAds = True
        elif isBlockingAds is not None: isBlockingAds = isBlockingAds
        else: isBlockingAds = "Other"

        total_dns = sum([x for x in dns_times if x >= 0])
        total_time = sum(total_times)
        non_negative_sizes = [this_size if this_size >=0 else 0 for this_size in sizes]
        size = sum(non_negative_sizes)
        bodySize = size
        contentSize = sum(contentSizes)
        print '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s'%(page_name, bodySize, contentSize, onLoad, total_dns,\
        total_time, (float(total_dns)/total_time),len(hosts), len(urls), network, location, isBlockingAds, \
        fname)

        



        
        #print hosts

        #for i in range(len(urls)):   
            #print " ", hostnames[i], dns_times[i], total_times[i]

