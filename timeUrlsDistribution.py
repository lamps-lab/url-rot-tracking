import csv
import pandas as pd
import datetime as dt
import ast

#Give URL response code distributions, stratified by publication year of the work the URL appears in

def simplify_response(code):
    i = int(code)
    return i-i%100

if __name__ == '__main__':
    domains_dict = {}
    fields_dict = {}
    url_codes_topics_file = 'D:/pmcs0/urlsCodesTopics.csv'

    with open(url_codes_topics_file, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            response_code = row[2]
            simple_response = simplify_response(response_code)
            topic1_module = ast.literal_eval(row[3])
            if len(topic1_module.keys()) == 0:
                continue
            domain1 = topic1_module['domain']['display_name']
            field1 = topic1_module['field']['display_name']
            if not domain1 in domains_dict.keys():
                domains_dict[domain1] = {}
                domains_dict[domain1][simple_response] = 1
            elif not simple_response in domains_dict[domain1].keys():
                domains_dict[domain1][simple_response] = 1
            else:
                domains_dict[domain1][simple_response] += 1
            
            if not field1 in fields_dict.keys():
                fields_dict[field1] = {}
                fields_dict[field1][simple_response] = 1
            elif not simple_response in fields_dict[field1].keys():
                fields_dict[field1][simple_response] = 1
            else:
                fields_dict[field1][simple_response] += 1
        
    for key in domains_dict.keys():
        print(f"{key}: {domains_dict[key]}")
    for key in fields_dict.keys():
        print(f"{key}: {fields_dict[key]}")