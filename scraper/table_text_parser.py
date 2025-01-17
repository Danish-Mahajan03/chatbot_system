import os
import pandas as pd
from datetime import datetime
from tqdm import tqdm

class TableTextExtractor:
    """
    A class to extract text and tables from a webpage using BeautifulSoup and save the tables as CSV files.

    Attributes:
        __driver (WebDriver): The Selenium WebDriver used to navigate the webpage.
        __save_dir (str): The directory where extracted tables will be saved as CSV files.
    """

    def __init__(self, driver, save_dir='tables'):
        """
        Initializes the TableTextExtractor with a WebDriver instance and a directory to save tables.

        Args:
            driver (WebDriver): The Selenium WebDriver for accessing the current webpage.
            save_dir (str): The directory where extracted tables will be saved (default is 'tables').
        """
        self.__driver = driver
        self.__save_dir = save_dir
        os.makedirs(save_dir, exist_ok = True)


    def __extract_text_from_html(self, soup):
        """
        Extracts and concatenates all paragraph text from the HTML content.

        Args:
            soup (BeautifulSoup): A BeautifulSoup object representing the HTML content of the webpage.

        Returns:
            str: A string containing all paragraph text from the webpage.
        """
        paragraphs = soup.find_all('p')
        page_text = " ".join([para.get_text(strip=True) for para in paragraphs])
        return page_text


    def __extract_tables(self, soup):
        """
        Extracts all tables from the HTML content, saves them as CSV files, and generates metadata for each table.

        Args:
            soup (BeautifulSoup): A BeautifulSoup object representing the HTML content of the webpage.

        Returns:
            list: A list of dictionaries, each containing metadata about an extracted table, including:
                  - table_name (str): The name of the table (e.g., 'table_1').
                  - csv_path (str): The file path where the table is saved as a CSV file.
                  - source_url (str): The URL of the webpage from which the table was extracted.
                  - timestamp (str): The timestamp when the table was extracted.
        """
        tables = soup.find_all('table')
        table_data = []

        for idx, table in tqdm(enumerate(tables), desc="Processing tables"):
            headers = []
            rows = []

            # Extract table headers if present
            header_row = table.find('tr')
            if header_row:
                for th in header_row.find_all('th'):
                    headers.append(th.get_text(strip=True))

            # Extract table rows
            for row in table.find_all('tr')[1:]:  # Skip the header row
                row_data = []
                for cell in row.find_all(['td', 'th']):
                    row_data.append(cell.get_text(strip=True))
                rows.append(row_data)

            df = pd.DataFrame(rows, columns=headers if headers else None)

            csv_filename = f'table_{idx + 1}.csv'
            csv_path = os.path.join(self.__save_dir, csv_filename)
            df.to_csv(csv_path, index = False, encoding='utf-8')

            table_metadata = {
                'table_name': f'table_{idx + 1}',
                'csv_path':csv_path,
                'source_url': self.__driver.current_url,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            table_data.append(table_metadata)

        return table_data


    def extract_content_from_page(self, soup):
        """Method to extract both text and tables from the page.
    
    This method uses BeautifulSoup to extract the textual content and tables from the given HTML page.
    It calls internal methods to extract text from all paragraph elements and tables (with headers and rows).
    
    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the parsed HTML page.

    Returns:
        dict: A dictionary containing the extracted text and tables. The 'text' key holds the combined 
              text from the paragraphs, and the 'tables' key holds metadata about the extracted tables.
    """
        try:
            page_text = self.__extract_text_from_html(soup)
            tables = self.__extract_tables(soup)
            result = {
                'text': page_text,
                'tables': tables
            }
            return result
        except Exception as e:
            print(f"Error extracting content: {e}")
            return {'text': "", 'tables': []}