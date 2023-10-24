import requests
import queue
import threading
import multiprocessing
from bs4 import BeautifulSoup
import time

output_file = 'urls.txt'
lock = multiprocessing.Lock()

# Function to send a request and process URLs in the response
def process_url(url, url_queue):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Process the response and extract URLs
            page_content = response.text
            
            # Extract URLs from the page content
            new_urls = extract_urls_from_page(page_content)
            # Append the newly discovered URLs back to the queue
            with lock:
                for new_url in new_urls:
                    url_queue.put(new_url)

            # Write the processed URL to the output file
            with open(output_file, 'a') as f:
                f.write(f"{url}\n")

            # Process the response as needed
            print(f"Processed URL: {url}")
            print(f"{multiprocessing.current_process().name}")
            #print(page_content)
        else:
            #print(f"Failed to fetch URL: {url} (Status Code: {response.status_code})")
            print("")
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
    while not url_queue.empty():
        url = url_queue.get()
        process_url(url, url_queue)

if __name__ == '__main__':
    manager = multiprocessing.Manager()
    url_queue = manager.Queue()
    # Create a queue for URLs
    #url_queue = queue.Queue()

    # Start with an initial URL
    initial_url = 'https://example.com'
    url_queue.put(initial_url)
    url_queue.put('https://mit.edu')
    #url_queue.put('https://www.mit.edu')

    # Number of worker processes
    num_processes = 3

    # Create and start worker processes
    processes = []
    for _ in range(num_processes):
        process = multiprocessing.Process(target=worker, args=(url_queue,))
        processes.append(process)
        process.start()

    # Wait for all worker processes to finish
    for process in processes:
        process.join()

    print("All URLs processed.")