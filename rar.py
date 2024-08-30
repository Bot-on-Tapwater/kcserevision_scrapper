#!/usr/bin/env python3

import requests
import os
from bs4 import BeautifulSoup

def download_file(google_drive_url, download_directory):
    # Extract the file ID from the URL
    file_id = google_drive_url.split('/')[5]
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

    print(download_url) # Print url to help debug

    # Start a session to persist cookies
    session = requests.Session()
    
    # Send a GET request to the download URL
    response = session.get(download_url, allow_redirects=True)

    # Check for the virus scan warning page
    if 'Google Drive - Virus scan warning' in response.text:
        print("Virus scan warning page detected. Submitting confirmation form...")

        # Parse the response to find the confirmation form
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', {'id': 'download-form'})
        if form:
            confirm_url = form['action']
            form_data = {}
            for input_tag in form.find_all('input'):
                name = input_tag.get('name')
                if name:  # Ensure 'name' attribute exists
                    form_data[name] = input_tag.get('value', '')

            # Submit the form to confirm the download
            response = session.get(confirm_url, params=form_data, allow_redirects=True)
        else:
            print("Confirmation form not found.")
            return
    
    # Check the response headers to get the filename if available
    content_disposition = response.headers.get('content-disposition')
    if content_disposition:
        # Extract filename from content-disposition header
        filename = content_disposition.split('filename=')[-1].strip('"')
    else:
        # Fallback to file ID if filename cannot be determined
        filename = file_id

    # Define the path where the file will be saved
    os.makedirs(download_directory, exist_ok=True)
    filepath = os.path.join(download_directory, filename)

    # Save the file
    if response.status_code == 200:
        with open(filepath, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded file saved as: {filepath}")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

# Example usage
google_drive_url = "https://drive.google.com/file/d/1gU3AQ-sRG91pkh9RqBevtXcP5Begq4JU/view"
download_directory = 'rar_files'
download_file(google_drive_url, download_directory)
