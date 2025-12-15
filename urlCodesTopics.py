import csv
import pandas as pd
import datetime as dt


def find_url_topics(u_row):
    global d_reader, csvr
    url = u_row[1]
    response_code = u_row[2]
    index = u_row[0].index("journ") if "journ" in u_row[0] else u_row[0].index("plos.cor")
    filename = f"D:/pmcs0/allofplos\{u_row[0][index:]}"

    for d_row in csvr:
        if filename == d_row[0]:
            topics = [d_row[2], d_row[3], d_row[4]]
            break
    l = len(topics)
    dataframe = pd.DataFrame({'Filename': [filename], 'Url': [url], 'ResponseCode': [response_code],
                               'Topic1': [topics[0] if l>0 else {}], 'Topic2': [topics[1] if l>1 else {}], 'Topic3': [topics[2] if l>2 else {}]})
    return dataframe
        

def crawl_urls(url_file_name, domains_file):
    global output_file_name, count
    with open(url_file_name, 'r', encoding='utf-8') as u_file:
        with open(domains_file, 'r', encoding='utf-8') as d_file:
            u_reader = csv.reader(u_file)
            for u_row in u_reader:
                if count % 10000 == 0:
                    print(f"[{dt.datetime.now()}] scanned {count} URLs")
                dataframe = find_url_topics(u_row)
                dataframe.to_csv(output_file_name, mode='a', header=False, index=False)
                count += 1


if __name__ == '__main__':
    count = 0
    url_file_name = 'D:/pmcs0/mayURLs/mayURLs.csv'
    domains_file = 'D:/pmcs0/PLoSDomains.csv'
    output_file_name = 'urlsCodesTopics.csv'
    d = open(domains_file, newline='', mode='r', encoding='utf-8')
    d_reader = csv.reader(d)
    csvr = list(d_reader)
    crawl_urls(url_file_name, domains_file)