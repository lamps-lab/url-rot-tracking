from crossref.restful import Works
import csv
import pandas as pd
import datetime as dt
import time
import subprocess
import socket
import re
import os
import xml.etree.ElementTree as ET

#Scan XML files to find dates of publication


def is_connected_via_wifi(): #Check if machine is properly connected to the internet along with has_internet_connection and is_fully_connected (unnecessary if internet connection is guaranteed)
    try:
        output = subprocess.check_output("netsh wlan show interfaces", shell=True, text=True, stderr=subprocess.DEVNULL)
        match = re.search(r"^\s*State\s*:\s*(\w+)", output, re.MULTILINE)
        if match:
            return match.group(1).lower() == "connected"
        return False
    except subprocess.CalledProcessError:
        return False
    
def has_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """
    Attempts to connect to a public DNS server to verify internet access.
    Default is Google DNS at 8.8.8.8:53.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False
    
def is_fully_connected():
    return has_internet_connection() and is_connected_via_wifi()

def retrieve_date(filename, doi): #Retrieve publication dates via Crossref
    global failed
    while not is_connected_via_wifi():
        time.sleep(0.5)
    try:
        works = Works()
        info = works.doi(doi)
        title = info['title'][0]
        issued_date = info['issued']['date-parts'][0]
        created_date = info['created']['date-parts'][0]
        dataframe = pd.DataFrame({"File": [filename], "Title": [title], "IssuedDate": [issued_date], "CreatedDate": [created_date]})
        return dataframe
    except Exception as e:
        print(e)
        dataframe = pd.DataFrame({"File": [filename], "Title": [e], "IssuedDate": [{}], "CreatedDate": [{}]})
        failed += 1
        return dataframe


count = 0
failed = 0
temp = 0
csv_file_name = 'PLoSDates2.csv'
dois_file = 'D:/pmcs0/PLoSDOIs.csv'


if __name__ == '__main__':
    root_path = 'D:/pmcs0/allofplos'
    files = [os.path.join(root_path, f) for f in os.listdir(root_path) if os.path.isfile(os.path.join(root_path, f))]
    years_dict = {}
    count = 0
    failed = 0
    for file in files:
        if count%1000 == 0:
            print(f"[{dt.datetime.now().time()}] {count} files scanned")
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            ppub = root.find(".//pub-date[@pub-type='ppub']")
            if ppub is not None:
                pmonth = ppub.find('month').text if ppub.find('month') is not None else 0
                pyear = ppub.find('year').text if ppub.find('year') is not None else 0
            else:
                pmonth = 0
                pyear = 0
            epub = root.find(".//pub-date[@pub-type='epub']")
            if epub is not None:
                eday = epub.find('day').text if epub.find('day') is not None else 0
                emonth = epub.find('month').text if epub.find('month') is not None else 0
                eyear = epub.find('year').text if epub.find('year') is not None else 0
            else:
                eday = 0
                emonth = 0
                eyear = 0
            if str(eyear) not in years_dict.keys():
                years_dict[eyear] = 1
            else:
                years_dict[eyear] += 1
        except:
            failed += 1
            pass
        count += 1
    print([count, failed])
    print(years_dict)


    