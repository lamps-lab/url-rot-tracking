import os
import pandas as pd
from lxml import etree

#Scan XML files to find DOIs

def findDOI(file_name):
    try:
        tree = etree.parse(file_name)
        root = tree.getroot()
        doi = root.find(".//article-id[@pub-id-type='doi']")
        dataframe = pd.DataFrame({"File": [file_name], "DOI": [doi.text]})
    except:
        dataframe = pd.DataFrame({"File": [file_name], "DOI": "None"})
    return dataframe

def scanFiles(root_path, output_file):
    files = [os.path.join(root_path, f) for f in os.listdir(root_path) if os.path.isfile(os.path.join(root_path,f))]
    numScanned = 0
    for file in files:
        if numScanned%1000 == 0:
            print(f"{numScanned} files scanned")
        findDOI(file).to_csv(output_file, mode='a', header=False, index=False)
        numScanned += 1


if __name__ == '__main__':
    root_path = "D:/pmcs0/allofplos"
    output_file = "PLoSDOIs.csv"
    scanFiles(root_path, output_file)

