import os
import re
import time 
import datetime as dt
import requests
from requests.exceptions import ConnectionError, Timeout, ProxyError
from urllib3.exceptions import NewConnectionError, MaxRetryError, ReadTimeoutError, ConnectTimeoutError
import threading
import string
import pandas as pd
import fitz  # PyMuPDF
import PyPDF2
from bs4 import BeautifulSoup
from lxml import etree
from io import StringIO
import nltk
#nltk.download('punkt') #downloads only need to be done once
#nltk.download('punkt_tab') 
from nltk.tokenize import sent_tokenize
import multiprocessing
from multiprocessing import BoundedSemaphore
from functools import partial
import gc


# ----- URL Extraction Functions from URL-Xtractor.py -----

def extract_urls_and_sentences_from_text(text_content):
    url_pattern = re.compile(r'''(?xi)
    (?:(?:https?|ftp|sftp|file|data|javascript|mailto|tel|git|ssh|magnet):\/\/
      |www\d{0,3}[.]
      |[a-z0-9.\-]+[.][a-z]{2,4}\/)
    (?:\S+(?::\S*)?@)?
    (?:
        (?!(?:10|127)(?:\.\d{1,3}){3})
        (?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})
        (?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})
        (?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])
        (?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}
        (?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))
    |
        (?:
            [a-z0-9\u00a1-\uffff]
            [a-z0-9\u00a1-\uffff_-]{0,62}
        )?
        [a-z0-9\u00a1-\uffff]\.
        (?:[a-z\u00a1-\uffff]{2,}\.?)
    )
    (?::\d{2,5})?
    (?:[/?#][^\s]*)?
    (?:[^\s]*)
    ''', re.DOTALL)

    sentences = sent_tokenize(text_content)
    results = []
    for sentence in sentences:
        urls = url_pattern.findall(sentence)
        for url in urls:
            url = url.rstrip(string.punctuation.replace('/', ''))
            results.append((sentence, url))
            del url
    del sentences, text_content
    gc.collect()
    return results

def extract_urls_from_annotations(pdf_path):
    with open(pdf_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        urls = []
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            if "/Annots" in page:
                annotations = page["/Annots"]
                for annotation in annotations:
                    annotation_obj = annotation.get_object()
                    if "/A" in annotation_obj and "/URI" in annotation_obj["/A"]:
                        uri = annotation_obj["/A"]["/URI"]
                        urls.append(uri)
        return urls

def extract_hyperlinked_images_from_pdf(pdf_path):
    pdf_document = fitz.open(pdf_path)
    hyperlinked_urls = []
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        links = page.get_links()
        for link in links:
            if 'uri' in link and link['kind'] == fitz.LINK_URI:
                hyperlinked_urls.append(link['uri'])
    return hyperlinked_urls

# ----- Existing plosChecker.py Functions for XML/Text Files -----


def fileCheck(filename, root_path):
    startTime = time.time()
    urls = {}
    file_path = os.path.join(root_path, filename)
    try:
        tree = etree.parse(file_path)
        text_nodes = tree.xpath("//text()")
    except Exception as e:
        print(e)
        return {}
    plainText = "".join(text_nodes)
    sentences_and_urls = extract_urls_and_sentences_from_text(plainText) #get urls and sentences using xtractor
    for sentence, url in sentences_and_urls:
        identified = False 
        protocols = {'https': 0,'http': 0, 'ftp': 0, 'sftp': 0, 'file': 0, 'data': 0, 'javascript': 0, 'mailto': 0, 'tel': 0, 'git': 0, 'ssh': 0, 'magnet': 0}
        for protocol in protocols.keys():
            if url.lower().startswith(protocol):
                identified = True
                break
        if url.lower().startswith("www") and not identified: #reformat URIs if need be
            url = "http://" + url
            identified = True
        elif not identified:
            url = "http://www." + url
        urls[url] = []
        urls[url].append(sentence)
    endTime = time.time()
    startTime = time.time()
    for url in urls.keys():
        results = tryURL(url)
        urls[url].append(results[1])
        urls[url].append("" if not results[0] else results[2])
        del results
    endTime = time.time()
    avg_time = (endTime - startTime) / (len(urls.keys()) if urls else 1)
    print(f"Time to check {filename}: {round((endTime - startTime), 5)} seconds; average time per URL: {round(avg_time, 5)} seconds")
    del plainText, text_nodes, sentences_and_urls
    gc.collect()
    return urls


class AbsoluteTimeoutError(Exception):
    def __init__(self):
        super().__init__()
def kill_request():
    raise AbsoluteTimeoutError

def tryURL(url):
    timer = threading.Timer(75, kill_request)
    timer.start()
    with url_semaphore:
        try:
            response = requests.get(url, timeout=7.5)
            return False, response.status_code
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
            timer.cancel()
            del timer
            gc.collect() 

# ----- PDF Processing using URL-Xtractor Functions -----

def process_pdf_file(pdf_filename, root_path):
    full_path = os.path.join(root_path, pdf_filename)
    df = pd.DataFrame(columns=["File", "Source", "Sentence", "URL", "Status", "ErrorMessage"])
    try:
        pdf_document = fitz.open(full_path)
    except Exception as e:
        print(f"Error opening {pdf_filename}: {e}")
        return None



    # Extract URLs from the plain text content
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text_content = page.get_text("text")
        url_sentence_pairs = extract_urls_and_sentences_from_text(text_content)
        del text_content
        results = tryURL(url)
        for sentence, url in url_sentence_pairs:
            new_row = pd.DataFrame({
                "File": [pdf_filename],
                "Source": ["PlainText"],
                "Sentence": [sentence],
                "URL": [url],
                "Status": [results[1]],
                "ErrorMessage": ["" if not results[0] else results[2]]
            })
            df = pd.concat([df, new_row], ignore_index=True)

    # Extract URLs from annotations
    annotation_urls = extract_urls_from_annotations(full_path)
    for url in annotation_urls:
        results = tryURL(url)
        new_row = pd.DataFrame({
            "File": [pdf_filename],
            "Source": ["Annotation"],
            "Sentence": [""],
            "URL": [url],
            "Status": [results[1]],
            "ErrorMessage":["" if not results[0] else results[2]]
        })
        df = pd.concat([df, new_row], ignore_index=True)

    # Extract URLs from hyperlinked images
    hyperlinked_image_urls = extract_hyperlinked_images_from_pdf(full_path)
    for url in hyperlinked_image_urls:
        results = tryURL(url)
        new_row = pd.DataFrame({
            "File": [pdf_filename],
            "Source": ["Hyperlinked Image"],
            "Sentence": [""],
            "URL": [url],
            "Status": [results[1]],
            "ErrorMessage": ["" if not results[0] else results[2]]
        })
        df = pd.concat([df, new_row], ignore_index=True)
        del new_row
    pdf_document.close()
    gc.collect()
    return df

def process_text_file(filename, root_path):
    urls_dict = fileCheck(filename, root_path)
    
    df = pd.DataFrame(columns=["File", "URL", "Context", "Status", "ErrorMessage"])
    
    for url, data in urls_dict.items():
        new_row = pd.DataFrame({
            "File": [filename],
            "URL": [url],
            "Context": [data[0]],
            "Status": [data[1]],
            "ErrorMessage": [data[2]]
        })
        df = pd.concat([df, new_row], ignore_index=True)
        del new_row
    del urls_dict
    gc.collect()
    return df


# ----- Unified File Processing -----

def process_files(root_path, core_count, csv_name):
    global numChecked
    global numProcessed
    global unprocessed_files
    urlsFound = 0
    temp_url_count = 0
    absolute_start_time = time.time()
    update_start_time = time.time()

    with multiprocessing.Pool(processes=core_count) as pool:
        temp_time = time.time()
        print("Organizing and preparing files")
        files = [os.path.join(root_path, f) for f in os.listdir(root_path) if os.path.isfile(os.path.join(root_path,f))] #set up files to be scanned
        print(f"Time to organize and prepare files: {round((time.time()-temp_time)/60, 5)} minutes")


        chunksize = 1000
        scan_with_root = partial(scan_file, path = root_path) #set up partial scan_file method with path parameter filled in
        for dataframe, result, fname in pool.imap_unordered(scan_with_root, files): #use multiprocessing to find URLs, update results accordingly
            dataframe.to_csv(f"{csv_name}.csv", index = False, mode = 'a', header = False, chunksize = chunksize)
            urlsFound += len(dataframe)
            numChecked += 1
            if result:
                numProcessed += 1
            else:
                unprocessed_files.append(fname)
            if numChecked % 100 == 0 and numChecked != 0:
                print(f"---------- [{dt.datetime.now().time()}] Update for files {numChecked-99}-{numChecked}: {urlsFound - temp_url_count} URLs parsed in {round((time.time()-update_start_time), 5)} seconds; runtime so far: {round(((time.time()-absolute_start_time)/3600), 5)} hours")
                update_start_time = time.time()
                temp_url_count = urlsFound
            del dataframe, result, fname
            gc.collect()
        pool.close()
        pool.join()

    temp_time = time.time()
    print(f"All files checked after {round(((time.time()-absolute_start_time)/3600), 5)} hours; {urlsFound} URLs found; average time per file: {round(((time.time()-absolute_start_time)/len(os.listdir(root_path))), 5)} seconds")
    print(f"Unprocessed files: {', '.join(unprocessed_files)}" if not len(unprocessed_files)==0 else f"All {numProcessed} files processed, none unparsed")

def scan_file(filename, path):
    if filename.lower().endswith(".pdf"):
        print(f"Processing PDF: {filename}")
        df = process_pdf_file(filename, path)
        return df, True, filename
    elif filename.lower().endswith(".xml"):
        print(f"Processing non-PDF (XML): {filename}")
        df = process_text_file(filename, path)
        return df, True, filename
    else:
        print(f"{filename} not PDF or XML, didn't process")
        df = pd.DataFrame(columns=["File", "URL", "Context", "Status", "ErrorMessage"])
        return df, False, filename



url_semaphore = BoundedSemaphore(8)
numChecked = 0
numProcessed = 0
unprocessed_files = []
if __name__ == "__main__":
    core_count = 10 #however many cores you want to use
    root_path3 = ''
    csv_file_name3 = ""
    process_files(root_path3, core_count, csv_file_name3)
