import os
import requests
import time
import datetime as dt
from requests.exceptions import ConnectionError, Timeout, ProxyError
from urllib3.exceptions import NewConnectionError, MaxRetryError, ReadTimeoutError, ConnectTimeoutError
import threading
from nltk.tokenize import sent_tokenize
import multiprocessing
from multiprocessing import BoundedSemaphore
from functools import partial
import gc
import pandas as pd
import csv
import re
import socket
import subprocess


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

class AbsoluteTimeoutError(Exception):
    def __init__(self):
        super().__init__()
def kill_request():
    raise AbsoluteTimeoutError

def tryURL(url):
    while not is_fully_connected():
        time.sleep(0.5)
    with url_semaphore:
        try:
            response = requests.get(url, timeout=7.5)
            return False, response.status_code, ""
        except requests.exceptions.ConnectionError as e:
            if isinstance(e.__cause__, NewConnectionError):
                return True, 601, e
            elif isinstance(e.__cause__, MaxRetryError):
                return True, 602, e
            elif isinstance(e.__cause__, ReadTimeoutError):
                return True, 603, e
            elif isinstance(e.__cause__, ConnectTimeoutError):
                return True, 604, e
            else:
                return True, 605, e
        except requests.exceptions.Timeout as e:
            if isinstance(e.__cause__, ReadTimeoutError):
                return True, 701, e
            elif isinstance(e.__cause__, ConnectTimeoutError):
                return True, 702, e
            else:
                return True, 703, e
        except requests.exceptions.TooManyRedirects as e:
            return True, 800, e
        except AbsoluteTimeoutError:
            return True, 900, e
        except Exception as e:
            return True, 1000, e
        finally:
            gc.collect() 

def scanURL(row):
    if row:
        filename = row[0]
        url = row[1]
        status, code, error = tryURL(url)
        if status:   
            dataframe = pd.DataFrame({"File": [filename], "URL": [url], "Status": [code], "ErrorMessage": [error]})
        else:
            dataframe = pd.DataFrame({"File": [filename], "URL": [url], "Status": [code], "ErrorMessage": ""})
        return True, dataframe
    else:
        return False, pd.DataFrame()
        

def process_urls(root_path, core_count, csv_name):
    global numChecked
    absolute_start_time, update_start_time = time.time(), time.time()
    files = [os.path.join(root_path, f) for f in os.listdir(root_path) if os.path.isfile(os.path.join(root_path,f))] #set up files to be scanned
    numRows = 0
    for file in files:
        rows = []
        print(f"**********[{dt.datetime.now().time()}] Processing {file}")
        with open(file, 'r', encoding = 'utf-8') as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                rows.append(row)
            numRows += len(rows)
            with multiprocessing.Pool(processes = core_count) as pool:
                for status, dataframe in pool.imap_unordered(scanURL, rows):
                    if status:
                        dataframe.to_csv(f"{csv_name}.csv", index = False, mode = 'a', header = False)
                        numChecked += 1
                    if numChecked % 100 == 0:
                        print(f"[{dt.datetime.now().time()}] URLs {numChecked-99} - {numChecked} out of {numRows} tried in {round(time.time()-update_start_time, 5)} seconds; runtime so far: {round((time.time()-absolute_start_time)/3600, 5)} hours ({file})")
                        update_start_time = time.time()
        gc.collect()
        print(f"**********[{dt.datetime.now().time()}] {file} finished processing")
    print(f"**********[{dt.datetime.now().time()}] All files processed and {numRows} URLs tried after {round((time.time()-absolute_start_time)/3600, 5)} hours")
                
                


url_semaphore = BoundedSemaphore(8)
numChecked = 0
if __name__ == "__main__":
    core_count = 8
    root = "" #root path
    folder = "" #path to folder containing URLs
    file_path = os.path.join(root, folder)
    csv_file_name = "" #name of new file to store response codes
    process_urls(file_path, core_count, csv_file_name)
