import os
import requests
import hashlib
import json
import pickle
import pandas as pd
from urllib.parse import urlparse, urljoin, parse_qs, parse_qsl, urlencode, urlunparse

class URLNameGenerator:
    """
    A class to generate names from URLs, especially for empty paths, by incrementing a counter.

    Attributes:
        __empty_path_counter (int): A counter to generate names for URLs with empty or missing paths.
    """
    def __init__(self):
        self.__empty_path_counter = 1

    def get_name_from_url(self, url):
        """
        Generates a name based on the URL's path. If the path is empty or invalid, 
        it generates a default name with an incremented counter.

        Args:
            url (str): The URL from which to generate a name.

        Returns:
            str: The generated name.
        """
        # Parse the URL to get the path
        path = urlparse(url).path  # e.g., '/ITEP/FEE_Structure_180723.pdf'
        
        # Check if the path is empty or just a single slash
        if not path or path == '/':
            name = f"default_name_{self.__empty_path_counter}"   
            self.__empty_path_counter += 1 
            return name

        # Remove the leading slash if there is one
        path = path[1:] if path.startswith('/') else path
        
        # Remove the file extension
        name = path.rsplit('.', 1)[0]  # e.g., 'ITEP/FEE_Structure_180723'
        
        return name
    

def is_internal_link(base_url, link):
    """
    Determines whether a link is internal (within the same domain) to the base URL.

    Args:
        base_url (str): The base URL to compare against.
        link (str): The link to check.

    Returns:
        bool: True if the link is internal, False otherwise.
    """
    full_link = urljoin(base_url, link)
    return urlparse(full_link).netloc == urlparse(base_url).netloc


def normalize_url(url, base_url = None):
    """
    Normalizes a URL by ensuring it has a consistent scheme, netloc, and sorted query parameters.
    If the URL is relative, it is joined with the provided base URL.

    Args:
        url (str): The URL to normalize.
        base_url (str, optional): The base URL to use if the provided URL is relative.

    Returns:
        str: The normalized URL.
    """
    parsed_url = urlparse(url)
    
    # If the URL is relative and base_url is provided, join with base_url
    if not parsed_url.netloc and base_url:
        url = urljoin(base_url, url)
    
    # Parse the URL into components
    parsed_url = urlparse(url.lower())
    
    # Remove fragments
    scheme = 'http' if parsed_url.scheme == 'https' else parsed_url.scheme
    path = parsed_url.path.rstrip('/')  # Remove trailing slashes to standardize
    
    # Sort query parameters and filter out unimportant ones
    query_params = parse_qsl(parsed_url.query)

    # Define parameters to ignore
    ignore_params = {'utm_source', 'utm_medium', 'utm_campaign'}
    filtered_params = [(k, v) for k, v in query_params if k not in ignore_params]
    sorted_query = urlencode(sorted(filtered_params))
    
    # Reconstruct the URL without fragment
    normalized_url = urlunparse((scheme, parsed_url.netloc, path, '', sorted_query, ''))
    
    return normalized_url


def normalize_href(href):
    """
    Normalizes an href by removing trailing slashes, lowercasing the path, and sorting query parameters.

    Args:
        href (str): The href to normalize.

    Returns:
        str: The normalized href.
    """
    parsed_url = urlparse(href)

    # Normalize path, remove trailing slash, and lowercase
    path = parsed_url.path.rstrip('/').lower()

    # Parse and sort query parameters
    query_params = parse_qs(parsed_url.query)
    normalized_query = {key.lower(): value for key, value in query_params.items()}
    sorted_query = sorted(normalized_query.items())
    normalized_query_string = urlencode(sorted_query, doseq=True)

    # Rebuild the href with normalized path and sorted query string
    normalized_href = urlunparse(('', '', path, parsed_url.params, normalized_query_string, ''))
    return normalized_href


def fetch_and_hash_content(url):
    """
    Fetches the content from a URL and returns its SHA-256 hash if successful.

    Args:
        url (str): The URL from which to fetch content.

    Returns:
        str: The SHA-256 hash of the content, or None if there was an error fetching the content.
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return hashlib.sha256(response.text.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
    return None


def download_file(download_url, local_folder, filename):
    """
    Downloads a file from a URL and saves it to a local folder with the specified filename.

    Args:
        download_url (str): The URL to download the file from.
        local_folder (str): The folder where the file should be saved.
        filename (str): The name of the file to save locally.

    Returns:
        str: The path of the downloaded file, or None if the download failed.
    """
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        file_path = os.path.join(local_folder, filename)
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Downloaded: {filename}")
        return file_path  # Return the path of the downloaded file
    except Exception as e:
        print(f"Failed to download {download_url}: {e}")
        return None
    

def create_content_dictionary(text_data, images_data, links_data, video_data):
    """
    Creates a dictionary with content data for text, images, links, and videos.

    Args:
        text_data (str): The extracted text content.
        images_data (list): A list of image data (dictionaries with metadata).
        links_data (dict): A dictionary of link data (downloadable files, internal/external links).
        video_data (list): A list of video data (dictionaries with metadata).

    Returns:
        dict: A dictionary containing all content data.
    """
    content_dict = {
        "text": text_data,            
        "images": images_data,       
        "downloadables": links_data, 
        "video_data":video_data
    }
    return content_dict


def is_google_drive_url(url):
    """
    Checks if the given URL is a Google Drive URL.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is a Google Drive URL, False otherwise.
    """
    return "drive.google.com" in url


def extract_google_drive_file_id(url):
    """
    Extracts the file ID from a Google Drive URL.

    Args:
        url (str): The Google Drive URL from which to extract the file ID.

    Returns:
        str: The file ID if present, or None if the file ID cannot be extracted.
    """
    if "file/d/" in url:
        return url.split("file/d/")[1].split("/")[0]
    return None


def google_drive_download_url(file_id):
    """
    Constructs a direct download URL for a Google Drive file using its file ID.

    Args:
        file_id (str): The Google Drive file ID.

    Returns:
        str: The direct download URL for the file.
    """
    return f"https://drive.google.com/uc?id={file_id}"


def is_pdf_url(url):
    """
    Checks if the given URL points to a PDF file.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is a PDF file, False otherwise.
    """
    return url.lower().endswith('.pdf')


def is_college_url(url):
    """
    Checks if the given URL is related to the college domain (e.g., "nitj.ac.in").

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is related to the college domain, False otherwise.
    """
    try:
        parsed_url = urlparse(url)
        return 'nitj.ac.in' in parsed_url.netloc  # Check if the domain is nitj.ac.in
    except Exception as e:
        print(f"Error parsing URL: {url}, {str(e)}")
        return False


def can_fetch_content(url):
    """
    Checks if the content at the given URL is accessible using an HTTP HEAD request.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the content can be fetched (status code 200), False otherwise.
    """
    try:
        response = requests.head(url)  # Use HEAD to check if the page is accessible
        return response.status_code == 200
    except requests.RequestException:
        return False
    

def save_as_json(obj, file_path):
    """
    Save a Python object as a JSON file.

    Args:
        obj (dict, list, etc.): The Python object to be saved.
        file_path (str): The path to the file where the object will be stored.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=4)
        print(f"Object successfully saved as JSON to {file_path}")
    except Exception as e:
        print(f"Error saving object to JSON: {e}")


def load_from_json(file_path):
    """
    Load a Python object from a JSON file.

    Args:
        file_path (str): The path to the JSON file to be loaded.

    Returns:
        object: The Python object loaded from the JSON file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            obj = json.load(f)
        print(f"Object successfully loaded from JSON file {file_path}")
        return obj
    except Exception as e:
        print(f"Error loading object from JSON: {e}")
        return None


def save_as_pickle(obj, file_path):
    """
    Save a Python object as a pickle file.

    Args:
        obj (dict, list, etc.): The Python object to be saved.
        file_path (str): The path to the file where the object will be stored.
    """
    try:
        with open(file_path, 'wb') as f:
            pickle.dump(obj, f)
        print(f"Object successfully saved as pickle to {file_path}")
    except Exception as e:
        print(f"Error saving object to pickle: {e}")


def load_from_pickle(file_path):
    """
    Load a Python object from a pickle file.

    Args:
        file_path (str): The path to the pickle file to be loaded.

    Returns:
        object: The Python object loaded from the pickle file.
    """
    try:
        with open(file_path, 'rb') as f:
            obj = pickle.load(f)
        print(f"Object successfully loaded from pickle file {file_path}")
        return obj
    except Exception as e:
        print(f"Error loading object from pickle: {e}")
        return None


def handle_dataframes_in_dict(d):
    """
    Recursively traverses a dictionary and converts any pandas DataFrame objects 
    into a list of dictionaries (or another desired format), while leaving other 
    data types (e.g., strings, integers) unchanged.

    Args:
        d (dict or list): The input data, which can be a dictionary, list, or 
                          a mix of both. It may also contain pandas DataFrame objects.

    Returns:
        dict or list: The transformed data where pandas DataFrames are converted 
                      to a list of dictionaries (one per row), and other data 
                      structures remain unchanged.
    
    Example:
        input_dict = {
            'key1': pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]}),
            'key2': ['item1', 'item2'],
            'key3': {
                'nested_key1': pd.DataFrame({'col1': [5, 6], 'col2': [7, 8]}),
                'nested_key2': 'string'
            }
        }
        
        output = handle_dataframes_in_dict(input_dict)
        # output will convert the DataFrame to a list of records and preserve other data
    """
    if isinstance(d, dict):
        # If the value is a dictionary, recursively check the dictionary
        return {k: handle_dataframes_in_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        # If the value is a list, recursively check each element
        return [handle_dataframes_in_dict(item) for item in d]
    elif isinstance(d, pd.DataFrame):
        # If the value is a DataFrame, convert it to a list of records
        return d.to_dict(orient='records')
    else:
        # If the value is not a dictionary, list, or DataFrame, return it as is
        return d

