import requests
import json
import http
import socket
import multiprocessing
from bs4 import BeautifulSoup
import time
import matplotlib.pyplot as plt
from urllib.parse import urlparse
from collections import Counter
from keywords import keyword_data
import threading

textfile_db = 'urls.txt'
lock = multiprocessing.Lock()

# Ensures most updated adblock list
def initialise_adblock(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
            print(f"Adblock list saved at {save_path}")
        with open(save_path, 'r') as file:
            return set({line.strip().partition(' ')[-1] for line in file})
    else:
        print(f"Error: Unable to download adblock list from {url}")

def continue_crawl(url):
    # Check if the URL is in the exclusion list (ad block list)
    if url not in exclusion: # Checks if been to the site before
        exclusion.add(url)
        domain=urlparse(url).netloc
        domain = domain.replace("www.","")
        #print(domain)
        if domain not in adblocker: # Checks domain if its an adblocker
            #print("Continue crawling!")
            exclusion.add(url)
            #print(exclusion)
            return True
    #print("Don't crawl")
    return False


# Function to send a request and process URLs in the response
def process_url(url, url_queue):
    try:
        time.sleep(1)
        start = time.perf_counter()
        response = requests.get(url, timeout=3)
        request_time = time.perf_counter() - start
        if response.status_code == 200:
            # Process the response and extract URLs
            page_content = response.text
            #print(page_content)
            visited_set.append(url)
            # Extract URLs from the page content
            new_urls = extract_urls_from_page(page_content)
            # Append the newly discovered URLs back to the queue

            for category, keywords in keyword_data.items():
                for keyword in keywords:
                    count = page_content.lower().count(keyword.lower())
                    shared_keyword_counts[category] += count
                    

            for new_url in new_urls:
                if continue_crawl(new_url):
                    url_queue.put(new_url)
                else:
                    continue
                        
            url_geolocation = f"{url}, {request(url)}, {request_time:.5f}"
            # Write the processed URL to the output file
            if url not in init_url:
                with open(textfile_db, 'a') as f:
                    f.write(f"{url_geolocation}\n")

            # Process the response as needed
            print(f"{multiprocessing.current_process().name} Processed URL: {url_geolocation}")

    except requests.exceptions.Timeout:
        print(f"Request timed out. Dropping the response. URL={url}")
    except Exception as e:
        #print(f"Error processing URL: {url} - {str(e)}")
        print("")

# Function to extract URLs from the page content using BeautifulSoup
def extract_urls_from_page(page_content):
    new_urls = []
    try:
        soup = BeautifulSoup(page_content, 'html.parser')
        # Extract links from 'a' tags with the 'href' attribute
        for link in soup.find_all('a', href=True):
            new_url = link.get('href')
            # You may want to filter and normalize URLs as needed
            new_urls.append(new_url)
    except Exception as e:
        print(f"Error extracting URLs: {str(e)}")
    return new_urls

def worker(url_queue):
    while not url_queue.empty() and not stop_event.is_set():
        url = url_queue.get()
        if url not in visited_set:
            process_url(url, url_queue)
        

# Reverse IP request
# Takes in an URL or address.

def request(addr):
    if "http" in addr:
        host = addr.split("/")[2]
        ip_address = socket.gethostbyname(host)
        addr = ip_address
    try:
        # Get from geolocation-db database
        request_url = 'https://geolocation-db.com/jsonp/' + addr
        response = requests.get(request_url)
        result = response.content.decode()
        result = result.split("(")[1].strip(")")
        result  = json.loads(result)
        ans = beautify(result)
    except http.client.RemoteDisconnected as e:
        print("Oh no, remote issues.")
        ans = ""
    except Exception as e:
        print(e)
        print("Some other issue")
        ans = ""
    return ans
    
# Helper function to beautify JSON response.
# Takes in a dictionary as formatted via JSON, and outputs a string containing
# the city of origin, country of origin, and IPv4 address.
def beautify(dic):
    city = dic.get("city", "Unknown City")
    country = dic.get("country_name", "Unknown Country")
    ipv4 = dic.get("IPv4", "Unknown IP")
    return f"{city}, {country}, {ipv4}"

def parse_urls_to_queue(queue):
    try:
        with open(textfile_db, 'r') as file:
            for line in file:
                url = line.strip()  # Remove leading/trailing whitespaces
                if url:
                    queue.put(url)
                    init_url.append(url)
    except FileNotFoundError:
        print(f"File not found: {textfile_db}")

def print_result():
    #keywords, counts = zip(*keyword_counts.most_common())
    #print(keyword_counts.keys())
    print(shared_keyword_counts)
    keywords = shared_keyword_counts.keys()
    counts = shared_keyword_counts.values()
    plt.bar(keywords, counts)
    plt.xlabel("Keywords")
    plt.ylabel("Occurrences")
    plt.title("IOT Devices Security Trends")
    plt.xticks(rotation=45)
    plt.savefig("keywords_trends.png")
    plt.show()

def stop_processes_after_time():
    time.sleep(5400)  # Stop the processes after 10 seconds
    stop_event.set()  # Set the stop event to signal the workers to stop

if __name__ == '__main__':
    # Stores the adblock as a set
    url = "https://raw.githubusercontent.com/badmojr/1Hosts/master/mini/hosts.txt" # You can choose the adblock filter in txt format
    save_path = "exclusion.txt"  # Replace with your desired file path
    adblocker = initialise_adblock(url,save_path)
    global exclusion
    exclusion=set() # I think this should be a global var so muli threading crawler can read?

    # Create a queue for URLs
    manager = multiprocessing.Manager()
    url_queue = manager.Queue()
    global visited_set
    global init_url
    global keyword_counts
    global shared_keyword_counts
    visited_set = manager.list()
    init_url = manager.list()
    stop_event = manager.Event()
    keyword_counts = Counter()

    shared_keyword_counts = manager.dict({category: 0 for category in keyword_data})


    # Call the function to parse URLs and put them into the queue
    parse_urls_to_queue(url_queue)

    # Number of worker processes
    num_processes = 4

    # Create and start worker processes
    processes = []
    for _ in range(num_processes):
        process = multiprocessing.Process(target=worker, args=(url_queue,))
        processes.append(process)
        process.start()
        time.sleep(1)

    timer_thread = threading.Thread(target=stop_processes_after_time)
    timer_thread.start()
    timer_thread.join()

    # Wait for all worker processes to finish
    for process in processes:
        process.join()

    print("All URLs processed.")

    print_result()
