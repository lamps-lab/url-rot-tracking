import os
import requests
import time
import datetime as dt
import pandas as pd
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.exceptions import NewConnectionError, MaxRetryError, ReadTimeoutError, ConnectTimeoutError
from requests.exceptions import ConnectionError, Timeout

# Custom exception (kept for completeness, though not used in this version)
class AbsoluteTimeoutError(Exception):
    def __init__(self):
        super().__init__()

def tryURL(row):
    if len(row) >= 2 and all(cell.strip() for cell in row[:2]):
        filename, url = row[0], row[1]
        try:
            response = requests.get(url, timeout=7.5)
            return filename, url, response.status_code, ""
        except ConnectionError as e:
            return filename, url, 600 + _get_error_code(e), str(e)
        except Timeout as e:
            return filename, url, 700 + _get_error_code(e), str(e)
        except requests.exceptions.TooManyRedirects as e:
            return filename, url, 800, str(e)
        except AbsoluteTimeoutError:
            return filename, url, 900, "Absolute timeout"
        except Exception as e:
            return filename, url, 1000, str(e)
    else:
        return None

def _get_error_code(e):
    if isinstance(e.__cause__, NewConnectionError):
        return 1
    elif isinstance(e.__cause__, MaxRetryError):
        return 2
    elif isinstance(e.__cause__, ReadTimeoutError):
        return 3
    elif isinstance(e.__cause__, ConnectTimeoutError):
        return 4
    else:
        return 5

def process_urls(root_path, thread_count, csv_name):
    absolute_start_time = time.time()
    update_start_time = time.time()
    files = [os.path.join(root_path, f) for f in os.listdir(root_path) if os.path.isfile(os.path.join(root_path, f))]
    total_checked = 0
    total_rows = 0
    batch_results = []
    batch_size = 100  # Flush every 100 results
    output_path = f"{csv_name}.csv"

    # Remove existing output file if present (to ensure clean header)
    if os.path.exists(output_path):
        os.remove(output_path)

    for file in files:
        print(f"**********[{dt.datetime.now().time()}] Processing {file}")
        with open(file, 'r', encoding='utf-8', newline='') as csvfile:
            csvreader = csv.reader(csvfile)
            total_rows_in_file = 0
            for row in csvreader:
                if len(row) >= 2 and all(cell.strip() for cell in row[:2]):
                    total_rows_in_file += 1
            total_rows += total_rows_in_file
            print(f"**********[{dt.datetime.now().time()}] {total_rows_in_file} valid URLs found in {file}")

        # Re-open to process with threads
        with open(file, 'r', encoding='utf-8', newline='') as csvfile:
            csvreader = csv.reader(csvfile)

            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                future_to_row = {executor.submit(tryURL, row): row for row in csvreader if len(row) >= 2 and all(cell.strip() for cell in row[:2])}

                for future in as_completed(future_to_row):
                    result = future.result()
                    if result:
                        batch_results.append(result)
                        total_checked += 1

                        # Flush batch if reached size limit
                        if len(batch_results) >= batch_size:
                            df = pd.DataFrame(batch_results, columns=["File", "URL", "Status", "ErrorMessage"])
                            df.to_csv(output_path, index=False, mode='a', header=not os.path.exists(output_path))
                            batch_results = []

                            print(f"[{dt.datetime.now().time()}] URLs {total_checked - batch_size + 1} - {total_checked} out of {total_rows} tried in {round(time.time() - update_start_time, 2)} seconds; runtime so far: {round((time.time() - absolute_start_time) / 3600, 3)} hours")
                            update_start_time = time.time()

        print(f"**********[{dt.datetime.now().time()}] {file} finished processing")

    # Flush any remaining results
    if batch_results:
        df = pd.DataFrame(batch_results, columns=["File", "URL", "Status", "ErrorMessage"])
        df.to_csv(output_path, index=False, mode='a', header=not os.path.exists(output_path))

    print(f"**********[{dt.datetime.now().time()}] All files processed. {total_checked} URLs checked in {round((time.time() - absolute_start_time) / 3600, 3)} hours", flush=True)


if __name__ == "__main__":
    thread_count = 64  # Reduced from 128 to lower concurrent memory pressure
    root = "" #root path
    folder = "" #path to folder containing URLs
    file_path = os.path.join(root, folder)
    csv_file_name = "" #name of new file to store response codes
    process_urls(file_path, thread_count, csv_file_name)
