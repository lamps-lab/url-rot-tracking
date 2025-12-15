#pip install pyalex required
import pandas as pd
import csv
from pyalex import Works, config
import subprocess
import socket
import re
import time
import datetime as dt
config.email = '_@_.com'

#Use OpenAlex API to collect Topic modules for PLoS works based on DOIs

def is_connected_via_wifi():
    try:
        output = subprocess.check_output("netsh wlan show interfaces", shell=True, text=True, stderr=subprocess.DEVNULL)
        # Check if "State" is "connected"
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

def retrieve_info(filename, doi):
    global failed
    while not is_fully_connected():
        time.sleep(0.5)
    try:
        work = Works()[f"https://doi.org/{doi}"]
        topics = work.get("topics")
        l = len(topics)
        dataframe = pd.DataFrame({"File": [filename], "Title": [work.get("title")], "Topic1": [topics[0] if l>0 else {}],
                                "Topic2": [topics[1] if l>1 else {}], "Topic3": [topics[2] if l>2 else {}]})
    except Exception as e:
        print(e)
        dataframe = pd.DataFrame({"File": [filename], "Error": [e], "Topic1": [{}], "Topic2": [{}], "Topic3": [{}]})
        failed += 1
    return dataframe

limit = 95000
failed = 0
csv_file_name = "PLoSDomains.csv"
domains_file = "D:/pmcs0/PLoSDOIs.csv"
start_index = 0 #use multiples of 100000 since OpenAlex has a limit of 100000 calls per day
if __name__ == '__main__':
    rows = []
    count = 0
    with open(domains_file, newline = '', encoding = 'utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            rows.append(row)
    for i in range(0, len(rows)-start_index):
        if count % 1000 == 0:
            print(f"[{dt.datetime.now().time()}] {count} domains collected so far")
        dataframe = retrieve_info(rows[start_index+i][0], rows[start_index+i][1].strip())
        dataframe.to_csv(csv_file_name, mode='a', header=False, index=False)
        count += 1
    print(f"{failed} requests failed")
    print(f"Crawl completed from index {start_index} to {start_index+limit} of {domains_file}")

    
