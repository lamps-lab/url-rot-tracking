# url-rot-tracking

Everywhere the code describes a path from "D:/pmcs0", that is simply my own machine's directory to the files. The output filenames in every script are a direct match with what they are called in the figshare link. For the scripts using OpenAlex API access, the pyalex package must be installed. 
Associated data:
https://figshare.com/articles/dataset/Tracking_URL_Decay_Data/30525827

dateChecker.py
Extracts publication dates from XML content of PLoS XML files and records to a new CSV file.
Instructions: Set root_path to the folder that contains all PLoS XML files. Set csv_file_name to your desired output CSV file. Set dois_file to the PLoSDOIs.csv file, which is described in the figshare link.

doiChecker.py
Extracts DOIs from XML content of PLoS XML files and records to a new CSV file.
Instructions: Set root_path to the folder that contains all PLoS XML files. Set output_file to your desired output CSV file.

domainChecker.py
Retrieves domains and fields of PLoS articles using their DOIs and records to a new CSV file. This script was made using the basic OpenAlex plan, meaning only 100,000 calls to the API could be made per day. Contains methods is_connected_via_wifi, has_internet_connection, and is_fully_connected only to ensure internet access under unstable internet conditions, which are not necessary if stable internet connection is guaranteed.
Instructions: Set config_email to your email, which is used by the OpenAlex API to help reduce spam; doing so will reduce problems that one may encounter using the API. Set limit to your desired limit at that time. Set csv_file_name to your desired output CSV file. Set dois_file to the PLoSDOIs.csv file, which is described in the figshare link. Set start_index to your starting index for your batch of API collection; for example, if you initially make 95,000 calls to the API one day, then set start_index to 95,000 the next day to begin where you last left off.

openAlexTopicsGetter.py
Retrieves a list of all topics in OpenAlex from the OpenAlex API, along with their associated subfields, fields, and domains, and records to a new CSV file. Contains methods is_connected_via_wifi, has_internet_connection, and is_fully_connected only to ensure internet access under unstable internet conditions, which are not necessary if stable internet connection is guaranteed.
Instructions: Set csv_file_name to your desired output CSV file.

plosCheckerFinal.py
Extracts all URLs from XML content of PLoS XML files and records to a new CSV file with a regular expression. Uses multiprocessing to speed up the process and prevent stalling. For this project, due to limited computational power, extraction was done over 10 batches of the PLoS dataset.
Instructions: Set core_count to the amount of cores you wish to use to perform multiprocessing operations. Set root_path3 to the the folder that contains PLoS XML files. Set csv_file_name3 to your desired output CSV file.

timeUrlsDistribution.py
Prints distributions of URL response codes stratified by the publication year of the work the URL appears in, which are extracted from XML content of PLoS articles.
Instructions: Set url_codes_topics_file to the urlsCodesTopics.csv file, which is described in the figshare link; alternatively, refer to the description of urlCodesTopics.py. 

urlChecker.py
Crawls all the URLs contained within marchURLs for response codes and error messages and records it to a new CSV file. During this project, initial URL collection done with plosCheckerFinal.py was done in 10 separate files due to computational constraints, which is why marchURLs is separated into 10 files. The response codes we collected in March were not used in this project; we used response codes collected in May. Uses multiprocessing to speed up the process and prevent stalling.
Instructions: Set core_count to the amount of cores you wish to use to perform multiprocessing operations. Set root to the parent folder of the marchURLs folder, which is the parent folder of the marchURLs_# folders, each of which holds one marchURLs_# CSV file. Set folder to the marchURLs folder. Set csv_file_name to your desired output CSV file.

urlCodesTopics.py
Takes URLs from mayURLs.csv and assigns them to the domains of the works they are each found in, from PLoSDomains.csv and records to a new CSV file. 
Instructions: Set url_file_name to the mayURLs.csv file, which is described in the figshare link. Set domains_file to the PLoSDomains.csv file, which is described in the figshare link. Set output_file_name to your desired output CSV file. 
