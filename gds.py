#!/usr/bin/env python2.7

import os
import errno
import requests
import argparse
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

url = "https://github.com/bdunlap9/Geckodriver-for-windows/blob/master/geckodriver.exe?raw=true"
filename = "C:\\Python27\\Scripts\\geckodriver.exe"
directory = "C:\\Python27\\Scripts\\"

def make_sure_path_exists(directory):
	try: 
		os.makedirs(directory)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise

def download_file(filename, url):
    with open(filename, 'wb') as fout:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        # Write response data to file
        for block in response.iter_content(4096):
            fout.write(block)
			
def download_if_not_exists(filename, url):
    if not os.path.exists(filename):
        download_file(filename, url)
        return True
    return False
	
make_sure_path_exists(directory)
download_if_not_exists(filename, url)
	
# Check for args, print logo and usage
if not len(sys.argv[1:]):
    print """

To start using this tool please provide one or more command
line arguments and their corresponding value, where applicable.
To display all options available use -h or --help.

Example:
gds.exe -h
gds.exe -d inurl:show.php?id= --verbose\n"""
    
    sys.exit(0)


# Handle command line arguments
parser = argparse.ArgumentParser(description="Use this tool and google dorks to find vulnerable web applications.")
group = parser.add_mutually_exclusive_group()
group.add_argument("-d", "--dork", help="        specify the dork you wish to use\n")
group.add_argument("-l", "--list", help="        specify path to list with dorks\n")
parser.add_argument("-v", "--verbose", action="store_true", help="        toggle verbosity\n")
args = parser.parse_args()

dork_list = []

# Dork list processing
if args.list:
    print "\n[+]Reading in list from: " + args.list + "\n\n"    
    try:
        with open(args.list, "r") as ins:
            for line in ins:
                dork_list.append(line)
                
                if args.verbose == True:
                    print "[~]" + line 
                
    except IOError as e:
        print "\n[!]Could not read dork list"
        if args.verbose == True:
            print "\nAn IO Error was raised with the following error message: "
            print "\n %s" % e
            
else:
    dork_list.append(args.dork)

print "\nWould you like to use a proxy while using the search engine?"
query = raw_input("[Y]es/[N]o: ")

if query == 'y':
    IP = raw_input("\nPlease enter the proxy host IP: ")
    PORT = raw_input("\nPlease enter the proxy port: ")
    set_proxy = True
elif query == 'n':
    print "\nEstablishing unproxied connection..."
    set_proxy = False
else:
    print "\n[!]Unhandled option, defaulting to unproxied connection..."
    set_proxy = False


# Web Driver Proxy
def proxy(PROXY_HOST,PROXY_PORT):
    fp = webdriver.FirefoxProfile()
    print "Proxy host set to: " + PROXY_HOST
    print "Proxy port set to: " + PROXY_PORT
    print "\nEstablishing connection..."
    fp.set_preference("network.proxy.type", 1)
    fp.set_preference("network.proxy.http",PROXY_HOST)
    fp.set_preference("network.proxy.http_port",int(PROXY_PORT))
    fp.set_preference("general.useragent.override","'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'")
    fp.update_preferences()
    return webdriver.Firefox(firefox_profile=fp)

# Function to generate and process results based on input
def search():
    link_list = []
    
    if set_proxy == True:
        driver = proxy(IP, PORT)
    else:
		driver = webdriver.Firefox(directory)
    
    for int in range(1):
        try:
            driver.get("http://google.com")
        except Exception as e:
            print "\n[!]A connection could not be established"
            if args.verbose == True:
                print "An error was raised with the following error message: "
                print "\n %s" % e
            break
            driver.quit()
            sys.exit(0)

        assert "Google" in driver.title
        for items in dork_list:
            elem = driver.find_element_by_name("q")
            elem.clear()
            elem.send_keys(items)
            elem.send_keys(Keys.RETURN)
            time.sleep(1)
            
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "r")))
            except Exception as e:
                driver.quit()
                print "\n[!]Detecting page source elements failed/timed out.\n"
                
                if args.verbose == True:
                    print "An error was raised with the following error message: "
                    print "\n %s" % e
                
                time.sleep(1)
                continue    
                
                
            assert "No results found" not in driver.page_source
            if "No results found." in driver.page_source:
                driver.quit()
                continue

            links = driver.find_elements_by_xpath("//h3//a[@href]")
            for elem in links:
                link_list.append(elem.get_attribute("href"))
            
    driver.quit()
    return link_list

proc_one = search()

with open("results.log", "w") as outfile:
    for item in proc_one:
        outfile.write("%s\n" % item)

if args.verbose == True:        
    with open("results.log", "r") as infile:
        for line in infile:
            print "\n[~]" + line
        

print "\n\nDone. Results have been saved to a textfile, in the current directory as %s for further processing." % outfile