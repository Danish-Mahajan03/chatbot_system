import os
import pytesseract
import cv2
import requests
import numpy as np
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
from datetime import datetime
from io import BytesIO
from urllib.parse import urljoin
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

class ImageExtractor:
    """
    A class to extract images from a webpage, process them using OCR and captioning models, 
    and gather metadata related to the images.

    Attributes:
        processor (BlipProcessor): The image processor for generating captions.
        captioning_model (BlipForConditionalGeneration): The model for generating image captions.
    """

    def __init__(self, driver):
        """
        Initializes the ImageProcessor with the path to the Tesseract executable and loads the BLIP captioning model.

        Args:
            tesseract_cmd (str): The path to the Tesseract executable (default is '/usr/bin/tesseract').
        """
        self.__driver = driver
        # Set up Tesseract command Path
        pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD")
   
        model_name = os.getenv("BLIP_MODEL_NAME", "Salesforce/blip-image-captioning-base")
        self.__processor = BlipProcessor.from_pretrained(model_name)
        self.__captioning_model = BlipForConditionalGeneration.from_pretrained(model_name)


    # Function to create an image dictionary with OCR and Captioning
    def __create_image_dict(self, image_url, image_desc, description_ocr, 
                          description_caption, image_format, sibling_info="", 
                          timestamp=None):
        """
        Creates a dictionary containing image metadata, including OCR text, caption, and other image details.

        Args:
            image_url (str): The URL of the image.
            image_desc (str): A description of the image.
            description_ocr (str): Text extracted from the image using OCR.
            description_caption (str): Caption generated for the image.
            image_format (str): The format of the image (e.g., 'jpg', 'png').
            sibling_info (str): Additional textual information from sibling elements (default is an empty string).
            timestamp (str, optional): Timestamp when the image was processed. If not provided, the current time is used.

        Returns:
            dict: A dictionary containing all the provided image metadata.
        """
        
        if not timestamp:
            timestamp = datetime.now().isoformat()
        
        image_data = {
            'url': image_url,
            'description': image_desc,
            'description_ocr': description_ocr,   
            'description_caption': description_caption,  
            'format': image_format,
            'sibling_info': sibling_info,  # Combined parent and sibling info
            'timestamp': timestamp
        }
        
        return image_data


    # Function to perform OCR on an image URL
    def __extract_text_from_image(self, image_url):
        """
        Extracts text from an image using OCR (Tesseract) after downloading the image from the given URL.

        Args:
            image_url (str): The URL of the image to process.

        Returns:
            str: The extracted text from the image, or an empty string if OCR fails.
        """

        try:
            response = requests.get(image_url)
            response.raise_for_status() 
            image_array = np.array(bytearray(response.content), dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)  

            if image is None:  # Check if image decoding was successful
                print(f"Error: Could not decode image at {image_url}.")
                return ""

            # Use Tesseract to extract text
            text = pytesseract.image_to_string(image)
            return text.strip()   
        except Exception as e:
            print(f"Error extracting text from image at {image_url}: {e}")
            return ""


    # Function to generate caption for an image
    def __generate_caption(self, image_url):
        """
        Generates a caption for an image by processing the image through a pre-trained BLIP model.

        Args:
            image_url (str): The URL of the image for which the caption will be generated.

        Returns:
            str: The generated caption for the image, or an empty string if the generation fails.
        """
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content)).convert("RGB")

            # Process the image and generate caption
            inputs = self.__processor(images=image, return_tensors="pt")
            out = self.__captioning_model.generate(**inputs, max_new_tokens=50)
            caption = self.__processor.decode(out[0], skip_special_tokens=True)
            return caption
        except Exception as e:
            print(f"Error generating caption for image at {image_url}: {e}")
            return ""


    # Function to extract parent and sibling info
    def __extract_parent_sibling_info(self, element):
        """
        Extracts textual information from the parent element and its sibling elements.

        Args:
            element (Tag): The HTML element from which parent and sibling information will be extracted.

        Returns:
            str: A string containing the text from the parent and sibling elements, or an empty string if no information is found.
        """
        if element:
            # Extract text from parent element
            parent_info = element.get_text(strip=True)
            
            # Extract text from all sibling elements
            sibling_elements = element.find_all(recursive=False)
            sibling_texts = []
            for sibling in sibling_elements:
                sibling_text = sibling.get_text(strip=True)
                sibling_texts.append(sibling_text)
            
            sibling_info = ' '.join(sibling_texts).strip()
            return parent_info + ' ' + sibling_info
        return ""


    # Function to check if URL points to a valid image format
    def __is_image_url(self, image_url):
        """
        Checks if the given URL points to a valid image format (e.g., .png, .jpg, .jpeg).

        Args:
            image_url (str): The URL to check.

        Returns:
            bool: True if the URL points to a valid image format, otherwise False.
        """
        return image_url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))


    # Function to extract images from page
    def extract_images_from_page(self, soup):
        """
        Extracts image URLs from the provided BeautifulSoup object (`soup`), processes each image 
        by generating an OCR description and a caption, and collects relevant metadata about the images.
        
        This method looks for `<img>` tags in the HTML and `<a>` tags that link to images. For each image, 
        it performs the following:
        1. Extracts the URL and description (alt text) from the image or anchor tag.
        2. Performs Optical Character Recognition (OCR) to extract text from the image (if it's a valid image).
        3. Generates a caption for the image using a pre-trained captioning model.
        4. Extracts parent and sibling information to provide contextual metadata.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing the parsed HTML page.

        Returns:
            list: A list of dictionaries containing metadata and processed information for each image.
                  Each dictionary includes:
                  - 'url': The full URL of the image.
                  - 'description': The alt text description of the image.
                  - 'description_ocr': The OCR-extracted text from the image (if applicable).
                  - 'description_caption': The generated caption for the image.
                  - 'format': The image format (e.g., 'jpg', 'png').
                  - 'sibling_info': Additional contextual information extracted from the parent and sibling elements.
                  - 'timestamp': The timestamp when the data was extracted.
        """
        image_list = []

        images = soup.find_all('img')
        for img in tqdm(images, desc="Processing img tags"):
            image_url = img.get('src')
            image_full_url = urljoin(self.__driver.current_url, image_url)
            image_desc = img.get('alt', '')
            
            # Validate and handle image format
            image_format = image_full_url.split('.')[-1] if self.__is_image_url(image_full_url) else 'unknown'
            
            # Perform OCR and generate caption for <img> tags
            if self.__is_image_url(image_full_url):
                description_ocr = self.__extract_text_from_image(image_full_url)
                description_caption = self.__generate_caption(image_full_url)
            else:
                print(f"Warning: Invalid image URL or format for <img>: {image_full_url}")
                description_ocr = ''
                description_caption = ''

            # Extract parent and sibling info
            parent_element = img.find_parent()
            sibling_info = self.__extract_parent_sibling_info(parent_element.find_parent()) if parent_element else ""
            
            image_data = self.__create_image_dict(image_full_url, image_desc, description_ocr,
                                                   description_caption, image_format, sibling_info)

            image_list.append(image_data)

        # Extract images from <a> tags
        anchor_tags = soup.find_all('a')
        for anchor in tqdm(anchor_tags, desc="Processing anchor tags containing images href"):
            image_url = anchor.get('href')

            # Check if the href points to an image
            if image_url and self.__is_image_url(image_url):
                image_desc = anchor.get_text(strip=True)  # Get any text associated with the anchor
                image_full_url = urljoin(self.__driver.current_url, image_url)

                # Perform OCR and generate caption for <a> tag images
                description_ocr = self.__extract_text_from_image(image_full_url)
                description_caption = self.__generate_caption(image_full_url)
                image_format = image_full_url.split('.')[-1] if image_full_url else 'unknown'

                # Extract parent and sibling info
                parent_element = anchor.find_parent()
                sibling_info = self.__extract_parent_sibling_info(parent_element) if parent_element else ""

                # Create a dictionary entry for the image found in the <a> tag
                image_data = self.__create_image_dict(image_full_url, image_desc, description_ocr,
                                                      description_caption, image_format, sibling_info)

                image_list.append(image_data)

        return image_list  