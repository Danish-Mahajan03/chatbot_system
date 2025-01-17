import os
import time
import pickle
from tqdm import tqdm
from bs4 import BeautifulSoup
from scraper.config import quit_driver
from scraper.table_text_parser import TableTextExtractor
from scraper.image_parser import ImageExtractor
from scraper.video_parser import VideoExtractor
from scraper.href_parser import LinkProcessor
from scraper.utils import (URLNameGenerator, create_content_dictionary, normalize_url, is_college_url, is_pdf_url,
                  download_file, is_google_drive_url, extract_google_drive_file_id,
                  google_drive_download_url, can_fetch_content, fetch_and_hash_content)

class ContentFetcher:
    def __init__(self, driver, 
                 download_folder="fetched_downloadables", 
                 storage_file="URLMetaData.pkl"):
        """
    Initializes the ContentFetcher class with driver, download folder, and storage file.
    Loads previously saved data if available and sets up the download folder.

    Args:
        driver (WebDriver): The Selenium WebDriver instance for browser automation.
        download_folder (str, optional): Path to the folder where downloaded files will be saved. Defaults to "fetched_downloadables".
        storage_file (str, optional): Path to the pickle file for saving and loading URL metadata. Defaults to "URLmetadata.pkl".

    Side Effects:
        Creates the download folder if it doesn't exist.
        Loads previously stored data from the storage file, if available.
    """
        self.__driver = driver
        self.__download_folder = download_folder
        self.__storage_file = storage_file
        self.__url_name_gen = URLNameGenerator()
        self.__relevant_links = {}

        self.__seen_links = {}
        self.__non_college_urls = set()
        self.__urls_not_fetched = set()
        self.__error_urls = set()
        self.__extracted_data = {}
        self.__google_drive_urls = set()
        self.__downloadables = {
            'pdf': [],
            'docx': [],
            'xlsx': [],
            'zip': []
        }

        if os.path.exists(self.__storage_file):
            self.__load_data()
            print(f"Loaded Data from {self.__storage_file}")

        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
            print(f"Created download folder: {download_folder}")
        else:
            print(f"Download Folder already exists: {download_folder}")

    def __load_data(self):
        """
    Loads previously saved URL metadata from the storage file into the class attributes.
    
    Side Effects:
        Updates class attributes with the loaded data from the storage file.
        Prints a message indicating data has been loaded.
    """
        with open(self.__storage_file, 'rb') as file:
            data = pickle.load(file)
            self.__seen_links = data.get('seen_links', {})
            self.__non_college_urls = data.get('non_college_urls', set())
            self.__urls_not_fetched = data.get('urls_not_fetched', set())
            self.__error_urls = data.get('error_urls', set())
            self.__extracted_data = data.get('extracted_data', {})
            self.__google_drive_urls = data.get('google_drive_urls', set())
            self.__downloadables = data.get('downloadables', {'pdf':[], 'docx':[], 'xlsx':[], 'zip':[]})

    def __save_data(self):
        """
    Saves the current state of URL metadata to the storage file.

    Side Effects:
        Writes data to the storage file using pickle.
        Prints a message indicating data has been saved.
    """
        data = {
            'seen_links': self.__seen_links,
            'non_college_urls': self.__non_college_urls,
            'urls_not_fetched': self.__urls_not_fetched,
            'error_urls': self.__error_urls,
            'extracted_data': self.__extracted_data,
            'google_drive_urls': self.__google_drive_urls,
            'downloadables':self.__downloadables
        }
        with open(self.__storage_file, 'wb') as file:
            pickle.dump(data, file)
            print(f"Data saved to {self.__storage_file}")

    def __fetch_content(self, url):
        """
    Fetches and extracts content from the given URL, including text, images, videos, and links.

    Args:
        url (str): The URL to fetch and process.

    Returns:
        dict: A dictionary containing the extracted content categorized as text, images, videos, and links.

    Side Effects:
        Navigates the browser to the given URL.
        Prints progress messages for each extraction step.
    """
        self.__driver.get(url)

        time.sleep(5)
        soup = BeautifulSoup(self.__driver.page_source, 'html.parser')

        print("Entering the text extraction function-------------------------------------")
        extractor = TableTextExtractor(self.__driver)
        text_data = extractor.extract_content_from_page(soup) 
        print("Text Completed------------------------------------------------------------")

        print("Entering images extraction function---------------------------------------")
        extractor = ImageExtractor(self.__driver)
        images_data = extractor.extract_images_from_page(soup)
        print("Image Completed------------------------------------------------------------")
 
        print("Entering videos extraction function----------------------------------------")
        extractor = VideoExtractor(self.__driver)
        video_data = extractor.extract_video_iframes_and_links(soup)
        print("Video Completed------------------------------------------------------------")

        print("Entering links extraction function------------------------------------------")
        extractor = LinkProcessor(self.__driver)
        links_data = extractor.process_href_links(soup, self.__seen_links, self.__relevant_links, self.__downloadables)
        print("Links Completed------------------------------------------------------------")

        content_dict = create_content_dictionary(text_data, images_data, links_data, video_data)
        print("Returning content dictionary")

        return content_dict
    
    def process_url(self, url):
        """
    Processes the given URL by normalizing it, checking for duplication, 
    and extracting its content if it hasn't been processed before.

    Args:
        url (str): The URL to process.

    Side Effects:
        Updates relevant_links, seen_links, and extracted_data with new data.
        Downloads PDFs and Google Drive files if applicable.
        Extracts content from URLs that can be fetched.
        Prints progress and error messages for each URL.
        Saves metadata to the storage file after processing all URLs.
    """
        normalized_url = normalize_url(url)

        if normalized_url in self.__seen_links or fetch_and_hash_content(url) in self.__seen_links.values():
            print(f"skipping already processed url: {url}")
            return
        else:
            self.__seen_links[normalized_url] = fetch_and_hash_content(url)
        
        self.__relevant_links[normalized_url] = url

        while self.__relevant_links:
            current_links_snapshot = self.__relevant_links.copy()
            self.__relevant_links.clear()

            for _, url in tqdm(current_links_snapshot.items(), desc = "Processing URL's"):
                normalized_url = normalize_url(url)
                if is_college_url(url):
                    if is_pdf_url(url):
                        print(f"Processing PDF: {url}")
                        filename = self.__url_name_gen.get_name_from_url(url).replace('/', '_')
                        if filename not in [item[0] for item in self.__downloadables.get('pdf', [])]:
                            downloaded_pdf_path = download_file(url, local_folder='fetched_downloadables', filename=filename)
                            if downloaded_pdf_path:
                                self.__extracted_data[normalized_url] = {
                                    'pdf_path': downloaded_pdf_path,
                                    'url': url,
                                    'source_page': self.__driver.current_url
                                }
                                print(f"Downloaded and stored PDF: {url}")
                                self.__downloadables.get('pdf').append((filename, url))
                        else:
                            print(f"skipping already processed PDF file : {filename}.pdf")
                        
                    elif is_google_drive_url(url):
                        print(f"Processing Google Drive link: {url}")
                        file_id = extract_google_drive_file_id(url)
                        if file_id:
                            download_url = google_drive_download_url(file_id)
                            filename = f"{file_id}".replace('/', '_')
                            
                            if filename not in [item[0] for item in self.__downloadables.get('pdf', [])]:
                                downloaded_pdf_path = download_file(download_url, local_folder='fetched_downloadables', filename=filename)
                                    
                                if downloaded_pdf_path:
                                    self.__extracted_data[normalized_url] = {
                                        'pdf_path': downloaded_pdf_path,
                                        'url': url,
                                        'source_page': self.__driver.current_url
                                    }
                                    print(f"Downloaded and stored PDF from Google Drive: {url}")
                                    self.__downloadables.get('pdf').append((filename, url))
                                    self.__google_drive_urls.add(url)
                            else:
                                print(f"skipping already processed google drive file : {filename}")
                            
                    elif can_fetch_content(url):
                        print(f"-------------------------------------Extracting content from: {url}-------------------------------------")
                        try:
                            content = self.__fetch_content(url)
                            if content:
                                self.__extracted_data[normalized_url] = content
                                print("------------------------Stored data in the extracted data------------------------------------")
                        except Exception as e:
                            self.__error_urls.add(url)
                            print(f"---------------------------Error fetching content from {url}: {str(e)}----------------------------")
                    else:
                        self.__urls_not_fetched.add(url)
                        print(f"-------------------------------Cannot fetch content from: {url}, skipping...---------------------------")
                else:
                    self.__non_college_urls.add(url)
                    print(f"-----------------------------------Skipping non-college URL: {url}------------------------------------------")
        
        self.__save_data()
        print("Updated the storage file with the fresh content")
        quit_driver(self.__driver)