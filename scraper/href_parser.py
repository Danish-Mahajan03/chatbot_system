import os
from scraper.utils import URLNameGenerator, normalize_url, download_file, fetch_and_hash_content
from datetime import datetime
from urllib.parse import urljoin
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

class LinkProcessor:
    """
LinkProcessor Class

This class processes anchor tags ('a') in a webpage, identifies and downloads specific file types 
(e.g., PDFs, DOCX, XLSX, ZIP), and categorizes them. It tracks seen and relevant links to avoid 
repeated downloads and ensure efficient link processing.

Attributes:
    __base_url (str): The base URL of the website being processed.
    __download_folder (str): The folder where downloadable files will be saved.
    __url_name_gen (URLNameGenerator): An instance of the URLNameGenerator class to generate filenames.

Methods:
    __handle_downloadable(full_url, a_tag, downloadables_data, downloadables):
        Handles downloading files from specified links, stores their metadata, and categorizes them 
        based on file type. Skips already downloaded files.
        
    process_href_links(soup, seen_links, relevant_links, downloadables):
        Processes all anchor tags in the provided BeautifulSoup object, identifies downloadable files, 
        downloads them, and categorizes the metadata. Updates seen and relevant links to avoid duplicates.
"""
    def __init__(self, driver):
        self.__driver = driver
        self.__download_folder = os.getenv("DOWNLOAD_FOLDER", "fetched_downloadables")
        self.__url_name_gen = URLNameGenerator()

    def __handle_downloadable(self, full_url, a_tag, downloadables_data, downloadables):
        """
    Handles downloading files from specified links, stores their metadata, 
    and categorizes them based on file type.

    Args:
        full_url (str): The full URL of the downloadable file.
        a_tag (Tag): The BeautifulSoup tag of the anchor element ('a') containing the link.
        downloadables_data (dict): A dictionary containing categorized downloadable metadata by file format.
        downloadables (dict): A dictionary tracking downloaded filenames to avoid duplicates.

    Side Effects:
        Downloads the file to the specified download folder and adds metadata to downloadables_data.

    Notes:
        Skips files that are already downloaded, as determined by the downloadables dictionary.
    """
        file_name = self.__url_name_gen.get_name_from_url(full_url).replace('/', '_')

        if (file_name not in [item[0] for item in downloadables.get('pdf', [])] and 
            file_name not in [item[0] for item in downloadables.get('docx', [])] and
            file_name not in [item[0] for item in downloadables.get('xlsx', [])] and 
            file_name not in [item[0] for item in downloadables.get('zip', [])]):

            file_ext = full_url.split('.')[-1]
            file_path = download_file(full_url, self.__download_folder, file_name)
            print(f"Downloaded file {file_name} in {file_path}")
        
            if file_path:
                downloadable_info = {
                    'url': full_url,
                    'filename': file_name,
                    'format': file_ext,
                    'description': a_tag.text.strip(),
                    'metadata': {
                        'source_url': self.__driver.current_url,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'folder': self.__download_folder
                        }
                }       
                if file_ext in downloadables_data:
                    print("Pushed file into downloadables_data and downloadables")
                    downloadables_data.get(file_ext).append(downloadable_info)
                    downloadables.get(file_ext).append((file_name, full_url))
        else:
            print(f"skipping already downloaded file: {file_name} with url {full_url}")
            return


    def process_href_links(self, soup, seen_links, relevant_links, downloadables):
        """
    Processes all anchor tags ('a') in the given BeautifulSoup object to identify valid links, 
    excluding images and video files. Downloads specific file types (PDF, DOCX, XLSX, ZIP) 
    and stores their metadata. Tracks and filters out already seen links to avoid duplication.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the parsed HTML content.
        seen_links (dict): A dictionary of already seen links mapped to their respective content hashes.
        relevant_links (dict): A dictionary of relevant links to be used for further processing.
        downloadables (dict): A dictionary tracking downloaded filenames to avoid duplicates.

    Returns:
        dict: A dictionary containing categorized downloadable links (e.g., PDFs, DOCX, etc.), 
              where each file type maps to a list of metadata about the downloaded files.

    Side Effects:
        Updates the seen_links and relevant_links dictionaries with unique links.
        Downloads files to the specified download folder and updates the downloadables_data dictionary.
    """
        all_links = soup.find_all('a', href=True)

        downloadables_data = {
            'pdf': [],
            'docx': [],
            'xlsx': [],
            'zip': []
        }
        
        for a_tag in tqdm(all_links, desc='Processing href links of anchor_tags'):
            href = a_tag['href']

            full_url = urljoin(self.__driver.current_url, href)  
            normalized_url = normalize_url(full_url)

            if any(href.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']): 
                continue
            elif any(href.endswith(ext) for ext in ['.pdf', '.docx', '.xlsx', '.zip']):           
                self.__handle_downloadable(full_url, a_tag, downloadables_data, downloadables)
            elif not normalized_url or normalized_url in seen_links:          
                continue
            else:
                content_hash = fetch_and_hash_content(full_url)
                if content_hash and content_hash not in seen_links.values():                      
                        seen_links[normalized_url] = content_hash
                        relevant_links[normalized_url] = full_url
        
        return downloadables_data