import os 
import pdfplumber
from TextPreprocessing.Preprocess_Text import TextProcessor
from scraper.utils import save_as_pickle, load_from_pickle
from dotenv import load_dotenv

load_dotenv()

class PDFProcessor:
    def __init__(self):
        """
        Initialize the PDFProcessor with the directory containing PDF files.
        """
        self.__pdf_directory = os.getenv("DOWNLOAD_FOLDER") 
        self.__text_processor = TextProcessor()
        self.__pdf_save_dir = os.getenv("PDF_SAVE_DIR")
        
        self.__preprocessed_data = None
        file_name = os.getenv("PDF_FILENAME")

        if not os.path.exists(self.__pdf_save_dir):
            os.makedirs(self.__pdf_save_dir, exist_ok=True)

        file_path = os.path.join(self.__pdf_save_dir, file_name)

        if os.path.exists(file_path):
            self.__preprocessed_data = load_from_pickle(file_path)
        else:
            self.__preprocessed_data = {}

        
    def __extract_text_from_pdf(self, pdf_path):
        """
        Extract text content from a PDF file.
        
        Args:
            pdf_path (str): Path to the PDF file.
        
        Returns:
            str: Extracted text content from the PDF.
        """
        text = ''
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ''
        return text

    def process_pdfs(self):
        """
        Process all PDF files in the specified directory.
        
        Returns:
            dict: A dictionary with filenames as keys and preprocessed text as values.
        """
        data = {}

        for filename in os.listdir(self.__pdf_directory):
            pdf_path = os.path.join(self.__pdf_directory, filename)
            if filename.endswith('.pdf') and os.path.isfile(pdf_path):
                try:
                    text = self.__extract_text_from_pdf(pdf_path)
                    preprocessed_text = self.__text_processor.process_text(text)
                    data[filename] = preprocessed_text
                except Exception as e:
                    print(f"Error processing {filename}:{e}")
        
        if data:
            self.__preprocessed_data.update(data)
            save_as_pickle(self.__preprocessed_data, os.path.join(self.__pdf_save_dir, os.getenv("PDF_FILENAME")))
        
        return data
    
    def process_single_pdf(self, pdf_filename):
        """
        Process a single PDF file and return its preprocessed text.
        
        Args:
            pdf_filename (str): Filename of the PDF to process.
        
        Returns:
            str: Preprocessed text of the PDF.
        """
        pdf_path = os.path.join(self.__pdf_directory, pdf_filename)
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"File {pdf_filename} not found in directory {self.__pdf_directory}.")
        
        try:
            text = self.__extract_text_from_pdf(pdf_path)
            text = self.__text_processor.process_text(text)
            self.__preprocessed_data[pdf_filename] = text
            save_as_pickle(self.__preprocessed_data, os.path.join(self.__pdf_save_dir, os.getenv("PDF_FILENAME")))
        except Exception as e:
            print(f"Error processing single PDF {pdf_filename}: {e}")
        
        return text