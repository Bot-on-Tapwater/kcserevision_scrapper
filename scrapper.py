#!/usr/bin/env python3

import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import json

# Import variables from .env file
load_dotenv()

# Set up a directory to save files
download_directory = 'downloaded_files'
os.makedirs(download_directory, exist_ok=True)

# Initialize a set for visited URLs to avoid loops
visited_urls = set()

# Initialize a set for downloaded file URLs to avoid duplicate downloads
downloaded_file_urls = set()

# Initialize a session
session = requests.Session()

# Replace these with your actual login credentials
login_url = 'https://kcserevision.com/'
username = os.environ.get('KCSE_REVISION_USERNAME')
password = os.environ.get('PASSWORD')

# Print credentials to confirm
print(username, password)

# Set the delay time (in seconds) between requests
request_delay = 0  # Adjust this delay as needed

# Initialize JSON records file
json_file = 'download_records.json'
if not os.path.exists(json_file):
    with open(json_file, 'w') as f:
        json.dump([], f)

# Function to handle login
def login():
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Referer': login_url,
        'Origin': login_url,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.6',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Sec-GPC': '1'
    }

    login_data = {
        'swpm_user_name': username,
        'swpm_password': password,
        'swpm-login': 'Log In',
    }

    response = session.post(login_url, data=login_data, headers=headers)

    if "Log Out" in response.text or "logout" in response.text:
        print("Login successful!")
    else:
        print("Login failed. Check your credentials.")
        print(response.text)

def download_file(url):
    if url in downloaded_file_urls:
        print(f"File from {url} has already been downloaded. Skipping.")
        return None, None

    if 'drive.google.com' in url:
        file_id = url.split('/')[5]
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = session.get(download_url)

        # Check if the response is an HTML indicating a Google Drive warning page
        if "text/html" in response.headers["Content-Type"]:
            print('HTML response, file cannot be scanned') # Print to help debug
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find the form action for the "Download anyway" button
            form = soup.find("form", {"id": "download-form"})
            if form:
                download_link = form["action"]
                download_id = form.find("input", {"name": "id"})["value"]
                download_url = f"https://drive.usercontent.google.com/download?id={download_id}"
                
                # Request the actual file download
                response = session.get(download_url)
        
        filename = response.headers.get('Content-Disposition')
        if filename:
            filename = filename.split('filename=')[1].strip('"')
        else:
            filename = f"{file_id}"

    else:
        response = session.get(url)
        filename = os.path.basename(url)

    filepath = os.path.join(download_directory, filename)

    # Check if the file already exists
    if os.path.exists(filepath):
        print(f"File already exists: {filepath}. Skipping download.")
        downloaded_file_urls.add(url)  # Mark as processed to avoid trying again
        return None, None

    with open(filepath, 'wb') as file:
        file.write(response.content)
    print(f'Downloaded: {filepath}')

    downloaded_file_urls.add(url)  # Add to the set of downloaded files
    return url, filename

def is_valid_url(url):
    parsed_url = urlparse(url)
    return bool(parsed_url.netloc) and bool(parsed_url.scheme)

def update_json(crawled_url, google_drive_download_link, downloaded_file_name, path_to_file):
    try:
        with open(json_file, 'r+') as f:
            try:
                records = json.load(f)
            except json.JSONDecodeError:
                records = []
            records.append({
                'crawled_url': crawled_url,
                'google_drive_download_link': google_drive_download_link,
                'downloaded_file_name': downloaded_file_name,
                'path_to_file': path_to_file
            })
            f.seek(0)
            json.dump(records, f, indent=4)
    except IOError as e:
        print(f"An error occurred while updating JSON: {e}")

def crawl_website(url):
    if url in visited_urls or not url.startswith("https://kcserevision.com"):
        print(f"\t*{url}* already crawled or not within allowed domain")
        return

    print(f"Crawling: *{url}*")
    visited_urls.add(url)

    with open('visited_urls.txt', 'a') as file:
        file.write(url + '\n')

    time.sleep(request_delay)

    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    for link in soup.find_all('a', href=True):
        file_url = urljoin(url, link['href'])

        if 'drive.google.com' in file_url:
            download_url, filename = download_file(file_url)
            if filename:
                update_json(crawled_url=url, google_drive_download_link=download_url,
                            downloaded_file_name=filename, path_to_file=os.path.join(download_directory, filename))

        elif 'https://kcserevision.com' in file_url and is_valid_url(file_url) and file_url not in visited_urls:
            crawl_website(file_url)

# Start by logging in
login()

# Start crawling from the homepage
start_url = 'https://kcserevision.com/'
# start_url = 'https://kcserevision.com/free-kcse-past-papers-and-marking-schemes-pdf/'
crawl_website(start_url)
