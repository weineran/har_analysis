from har import *
import os
#import json
import argparse
from aqualab.plot.mCdf import keyedCdf

def parse_args():
    parser = argparse.ArgumentParser(
            description='Compares .hars that were loaded with ads to .hars loaded without ads \
                         (i.e. without ad-blocker and with ad-blocker)')

    parser.add_argument('data_path', type=str,
        help="The path of the directory containing the har data to analyze. Data files should \
              be in subdirectories using [Network]-[Location]-[isBlockingAds] naming scheme.")
    parser.add_argument('--plot_only', type=str,
        help="Set to 'True' if the comparisons_dict has already been built.")

    return parser.parse_args()

def get_key_stats(har_obj):
    key_stats = {}

    urls = []
    hostnames = []
    dns_times = []
    total_times = []
    sizes = []
    contentSizes = []

    for entry in har_obj.entries:
            
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

    key_stats['onload_time']    = har_obj.pages[0]['pageTimings']['onLoad']
    key_stats['total_dns_time'] = sum([x for x in dns_times if x >= 0])
    key_stats['total_time']     = sum(total_times)
    non_negative_sizes          = [this_size if this_size >=0 else 0 for this_size in sizes]
    size                        = sum(non_negative_sizes)
    key_stats['bodySize']       = size
    key_stats['contentSize']    = sum(contentSizes)
    key_stats['num_hosts']      = len(hosts)         # "num domains"
    key_stats['num_urls']       = len(urls)          # "num objs"

    return key_stats


def compare_hars(h_yesBlock, h_noBlock, dirname_yesBlock, dirname_noBlock, data_path, network):
    title_noBlock = h_noBlock.pages[0]['title']
    title_yesBlock = h_yesBlock.pages[0]['title']
    print(title_noBlock + '\t' + title_yesBlock)

    results = {'network': network}


    keyStats_noBlock = get_key_stats(h_noBlock)
    keyStats_yesBlock = get_key_stats(h_yesBlock)

    if title_noBlock == 'http://news.yahoo.com/':
        print(title_noBlock)
        print(str(keyStats_noBlock))
        print(str(keyStats_yesBlock))

    for attr in keyStats_noBlock:
        try:
            results[attr] = keyStats_noBlock[attr] - keyStats_yesBlock[attr]
            try:
                results[attr+"_%"] = (float(results[attr]) / float(keyStats_noBlock[attr]))*100
            except ZeroDivisionError as zde:
                print("FAILED percent comparison: "+str(attr+"_%")+str(results[attr])+', '+str(keyStats_noBlock[attr]))
        except TypeError as e:
            print("FAILED comparison of : "+str(attr)+str(keyStats_noBlock[attr])+', '+str(keyStats_yesBlock[attr]))
    
    #comparisons_dict[title_noBlock] = results
    return results


def get_network_from_dirname(dirname):
    network = ""
    if dirname[0:4].upper() == "WIFI": network = "WiFi"
    elif dirname[0:5].upper() == "WIRED": network = "wired"
    elif dirname[0:2].upper() == "4G": network = "4G"
    else: network = "Other"

    return network

def get_location_from_dirname(dirname):
    location = ""
    if "ANDREWHOME" in dirname.upper(): location = "AndrewHome"
    elif "JAMESHOME" in dirname.upper(): location = "JamesHome"
    elif "NU" in dirname.upper(): location = "NU"
    else: location = "Other"

    return location


def find_matching_yesBlock_file(title_noBlock, fname_noBlock, file_list_yesBlock, data_path, dirname_yesBlock, yesBlock_failures, yesBlock_finder):
    for fname_yesBlock in file_list_yesBlock:
    # do linear search on filenames
        # If we already know the har can't be loaded, skip it
        if fname_yesBlock in yesBlock_failures:
            #print('skipped yesBlock ' + fname_yesBlock + '. Previously failed to parse har.')
            continue

        full_path_yesBlock = os.path.join(data_path,dirname_yesBlock,fname_yesBlock)

        # get har for yesBlock file
        try:
            h_yesBlock = Har(full_path_yesBlock)
        except Exception as e:
            #print 'skipped yesBlock ' + fname_yesBlock + '. ' + str(e)
            yesBlock_failures[fname_yesBlock] = True
        else:
            title_yesBlock =  h_yesBlock.pages[0]['title']
            yesBlock_finder[title_yesBlock] = fname_yesBlock     # store in dict for future searches
            if title_yesBlock == title_noBlock or fname_yesBlock == fname_noBlock:
                return h_yesBlock

    # if we search every file and no match found
    #print("No match found for noBlock page: "+title_noBlock)
    return False

if __name__ == '__main__':
    args = parse_args()
    dict_filename = "./comparisons_dict.txt"
    if args.plot_only == None or args.plot_only.upper() == "FALSE":
        data_path = args.data_path

        dir_pairs = {}
        num_matches = 0
        num_failed_matches = 0
        failed_match_list = []
        comparisons_dict = {}
        file_pairs_4g = {}
        file_pairs_wifi = {}
        file_pairs_wired = {}

        dir_list = os.listdir(data_path)
        
        # find pairs of files--with and without ads
        for dirname in dir_list:
            if "FALSE" in dirname.upper():
            # this directory contains data without ad-blocker enabled
            # find the matching directory with ad-blocker enabled
                target_dirname = dirname.upper().replace("FALSE", "TRUE")
                for dirname2 in dir_list:
                    if dirname2.upper() == target_dirname:
                        dir_pairs[dirname] = dirname2

        for dirname_noBlock in dir_pairs:
            dirname_yesBlock = dir_pairs[dirname_noBlock]
            #print('----'+dirname_noBlock+'\t'+dirname_yesBlock+'----')  # Print directory pairs to check that they look right

            network = get_network_from_dirname(dirname_noBlock)
            location = get_location_from_dirname(dirname_noBlock)

            file_list_noBlock = os.listdir(os.path.join(data_path,dirname_noBlock))
            file_list_yesBlock = os.listdir(os.path.join(data_path,dirname_yesBlock))

            yesBlock_finder = {}
            yesBlock_failures = {}

            # e.g. inside 4G-NU-false
            for file_noBlock in file_list_noBlock:
                if file_noBlock[0] == '0': continue

                full_path_noBlock = os.path.join(data_path,dirname_noBlock,file_noBlock)

                # get har for noBlock file
                try:
                    h_noBlock = Har(full_path_noBlock)
                except Exception as e:
                    #print 'skipped noBlock ' + file_noBlock + '.  error info: ' + str(e)
                    num_failed_matches += 1
                    failed_match_list.append(dirname_noBlock+'/'+file_noBlock)
                    continue

                title_noBlock = h_noBlock.pages[0]['title']

                # find matching yesBlock file
                print('Searching for a match for noBlock file: '+file_noBlock+", network: "+network)
                try:
                    # first look in our dictionary
                    file_yesBlock = yesBlock_finder[title_noBlock]
                except KeyError as e_key:
                    h_yesBlock = find_matching_yesBlock_file(title_noBlock, file_noBlock, file_list_yesBlock, data_path, dirname_yesBlock, yesBlock_failures, yesBlock_finder)
                else:
                    h_yesBlock = Har(os.path.join(data_path, dirname_yesBlock, file_yesBlock))
                
                if h_yesBlock == False:
                    # no match found
                    num_failed_matches += 1
                    failed_match_list.append(dirname_noBlock+'/'+file_noBlock)
                else:
                    comparisons_dict[title_noBlock+"_"+network+"_"+location] = compare_hars(h_yesBlock, h_noBlock, dirname_yesBlock, dirname_noBlock, data_path, network)
                    num_matches += 1

        print("num_matches: "+str(num_matches))
        print("num_failed_matches: "+str(num_failed_matches))

        print("List of failed matches: "+str(failed_match_list))

        f = open(dict_filename, 'w')
        f.write(json.dumps(comparisons_dict))
        f.close()
    # if plot_only != "TRUE" ends here


    comparisons_dict = json.load(open(dict_filename))

    #cdf_contentSize = keyedCdf(baseName='content_size_cdf', xlabel='contentSize_noBlock - contentSize_yesBlock (bytes)')

    cdf_list = []
    cdf_meta_info = {}

    for attr in comparisons_dict[comparisons_dict.keys()[0]]:
        attr = str(attr)    # convert from unicode
        if attr == 'network': continue  # skip network attribute
        cdf = keyedCdf(baseName=attr, xlabel=attr)

        cdf_meta_info[attr] = {'Wifi': [], '4G': [], 'wired': [], 'Other': []}

        count_wifi = 0
        count_4g = 0
        count_wired = 0
        count_other = 0

        print("RESULTS "+attr)
        for page_title in comparisons_dict:
            print(page_title)

            try:
                data_point = comparisons_dict[page_title][attr]
            except KeyError:
                print("FAILED to find comparisons_dict['"+page_title+"']['"+attr+"']")
                continue

            if str(comparisons_dict[page_title]['network']) == "WiFi":
                cdf.insert('WiFi', data_point)
                count_wifi += 1
                cdf_meta_info[attr]['Wifi'].append((page_title, data_point))
            elif str(comparisons_dict[page_title]['network']) == "4G":
                cdf.insert('4G', data_point)
                count_4g += 1
                cdf_meta_info[attr]['4G'].append((page_title, data_point))
            elif str(comparisons_dict[page_title]['network']) == "wired":
                cdf.insert('wired', data_point)
                count_wired += 1
                cdf_meta_info[attr]['wired'].append((page_title, data_point))
            else:
                cdf.inster('Other', data_point)
                count_other += 1
                cdf_meta_info[attr]['Other'].append((page_title, data_point))

            print(str(comparisons_dict[page_title]['network'])+" "+attr+ ": "+str(comparisons_dict[page_title][attr]))
        
        cdf_list.append(cdf)
        #cdf.plot('logscalex', plotdir='figs', xlim=[-1000000,1000000])
        plot_title = 'wifi n='+str(count_wifi)+', 4g n='+str(count_4g)+', wired n='+str(count_wired)
        cdf.plot(plotdir='figs', title=plot_title)

        print("wifi: "+str(count_wifi))
        print("4g: "+str(count_4g))
        print("wired: "+str(count_wired))
        print("Other: "+str(count_other))
        print(str(cdf_meta_info[attr]))



    


            





