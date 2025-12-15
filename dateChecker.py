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


count = 0
failed = 0
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



    
