from pyalex import Topics
import csv
import pandas as pd
import datetime as dt
import time
import subprocess
import socket
import re

#Simply collects all the Topics in OpenAlex via API

def is_connected_via_wifi(): #Check if machine is properly connected to the internet along with has_internet_connection and is_fully_connected (unnecessary if internet connection is guaranteed)
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
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False
    
def is_fully_connected():
    return has_internet_connection() and is_connected_via_wifi()


def collectData(topic):
    global failed
    try:
        topic_info = [topic['display_name'], topic['id'], topic['works_count'], topic['cited_by_count']]
    except Exception as e:
        print(e)
        topic_info = [e]
        failed += 1
    try:
        subfield_info = [topic['subfield']['display_name'], topic['subfield']['id']]
    except Exception as e:
        print(e)
        subfield_info = [e]
        failed += 1
    try:
        field_info = [topic['field']['display_name'], topic['field']['id']]
    except Exception as e:
        print(e)
        field_info = [e]
        failed += 1
    try:
        domain_info = [topic['domain']['display_name'], topic['domain']['id']]
    except Exception as e:
        print(e)
        domain_info = [e]
        failed += 1
    dataframe = pd.DataFrame({'Domain': [domain_info], 'Field': [field_info], 'Subfield': [subfield_info], 'Topic': [topic_info]})
    return dataframe

count = 0
failed = 0
csv_file_name = "openAlexTopics.csv"
if __name__ == '__main__':
    for i in range(1, 24):
        topics = Topics().get(per_page=200, page=i)
        for i in range(len(topics)):
            if count%1000 == 0:
                print(f"[{dt.datetime.now().time()}] {count} topics retrieved")
            dataframe = collectData(topics[i])
            dataframe.to_csv(csv_file_name, mode='a', header=False, index=False)
            count += 1
    print(f"{failed} failures")
    print(f"[{dt.datetime.now().time()}] {count} topics retrieved")
