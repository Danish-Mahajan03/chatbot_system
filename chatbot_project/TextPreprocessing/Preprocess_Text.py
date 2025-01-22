import nltk
import re
from nltk.corpus import stopwords, wordnet
from nltk import pos_tag
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from abc import ABC, abstractmethod

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger_eng', quiet=True)


class BaseMasker(ABC):
    def __init__(self, name):
        self._placeholder_counter = 1
        self._placeholder_dict = {}
        self._name = name

    @abstractmethod
    def mask(self, text):
        pass

    def _replace_with_placeholder(self, match):
        """
        Replaces the matched value with a placeholder and stores it in a dictionary.
        
        Args:
            match (re.Match): The matched pattern from the regular expression.
        
        Returns:
            str: The placeholder corresponding to the matched value.
        """
        value = match.group(0)
        placeholder = f"{self._name}{self._placeholder_counter}"
        self._placeholder_dict[placeholder] = value
        self._placeholder_counter += 1
        return placeholder

    def _mask_values(self, text, patterns):
        """
        Masks values in the text based on the provided patterns.
        
        Args:
            text (str): The text to be processed.
            patterns (list): A list of regex patterns to identify values to be masked.
        
        Returns:
            str: The masked text.
        """
        masked_text = text
        for pattern in patterns:
            masked_text = re.sub(pattern, self._replace_with_placeholder, masked_text)
        return masked_text
    
    def unmask_values(self, text):
        """
        Replaces the placeholders in the text with the original values.
        
        Args:
            text (str): The text with placeholders to be replaced.
        
        Returns:
            str: The text with original values restored.
        """
        unmasked_text = text
        for placeholder, value in self._placeholder_dict.items():
            unmasked_text = unmasked_text.replace(placeholder, value)
        return unmasked_text



class URLMasker(BaseMasker):
    def __init__(self):
        super().__init__("URL")
        self.__patterns = [
            r'\b(?:https?|ftp):\/\/(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:\/[^\s]*)?\?[^\s#]*#\S*\b',  # URL with both query and fragment
            r'\b(?:https?|ftp):\/\/(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:\/[^\s]*)?(?:\?[^\s#]*)?(?:#[^\s]*)?\b|\b(?:https?|ftp):\/\/(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:\/[^\s]*)?(?:\?[^\s#]*)?(?:#[^\s]*)?\b',  # URL including IP and Port
            r'\b(?:https?|ftp):\/\/(?:\d{1,3}\.){3}\d{1,3}(?:\/[^\s]*)?\b',  # URL with IP address in domain
            r'\b(?:https?|ftp):\/\/(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}:\d+(?:\/[^\s]*)?\b',  # URL with port number
            r'\b(?:https?|ftp):\/\/(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:\/[^\s]*)?(?:\?[^\s#]*)?(?:#[^\s]*)?\b',  # Full URL with query and fragment
            r'\b(?:https?|ftp):\/\/(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:\/[^\s]*)?\b',  # with paths and subdomains
            r'\b(?:https?|ftp):\/\/(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:\/[^\s]*)?\?[^\s#]*\b',  # URL with query parameters
            r'\b(?:https?|ftp):\/\/(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:\/[^\s]*)?#\S*\b',  # URL with fragment identifier
            r'\bhttps?:\/\/(?:bit\.ly|t\.co|goo\.gl)\/[a-zA-Z0-9-]+\b',  # Common URL shorteners
            r'\bhttps?:\/\/[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+(?:\/[^\s]*)?\b',  # URL with IDN
        ]

    def mask(self, text):
        """
        Masks URLs in the provided text.
        
        Args:
            text (str): The text containing URLs to be masked.
        
        Returns:
            str: The text with masked URLs.
        """
        return self._mask_values(text, self.__patterns)


class EmailMasker(BaseMasker):
    def __init__(self):
        super().__init__("EMAIL")
        self.__patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', # Basic email format (e.g., user@example.com), 
                                                                   # Email with subdomains (e.g., user@sub.example.com), 
                                                                   # Email with hyphens in the local part (e.g., user-name@example.com)
                                                                   # Email with numbers, dots, and hyphens in local part (e.g., user.name-123@example.com)
                                                                   # Email with upper case characters (e.g., User@Example.com)
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,6}(\.[A-Za-z]{2})?\b',  # Email with number and subdomain (e.g., user123@example.co.in)
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z0-9]{2,}\b', # Email with domain containing digits (e.g., user@example123.com)
            r'\b"([A-Za-z0-9._%+-]+)"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', # Email with quoted local part (e.g., "user.name"@example.com)
            r'\b[A-Za-z0-9._%+-]+@(?:\d{1,3}\.){3}\d{1,3}\b',    # Email with IP address in the domain part (e.g., user@192.168.1.1)
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{4,}\b' # Email with TLD of more than 4 characters (e.g., user@example.photography)
        ]

    def mask(self, text):
        """
        Masks email addresses in the provided text.
        
        Args:
            text (str): The text containing email addresses to be masked.
        
        Returns:
            str: The text with masked email addresses.
        """
        return self._mask_values(text, self.__patterns)


class DateMasker(BaseMasker):
    def __init__(self):
        super().__init__("DATE")
        self.__patterns = [
            r'\b\d{1,2}[/-/.]\d{1,2}[/-/.]\d{2,4}\b',   # MM/DD/YYYY or M/D/YYYY or DD/MM/YYYY or D/M/YYYY
            r'\b\d{2,4}[-/]\d{1,2}[-/]\d{1,2}\b',    # YYYY-MM-DD
            r'\b\d{1,2}(st|nd|rd|th)?( of)? \w{3,9},? \d{2,4}\b',   # Ordinal dates like 1st January, 2020, 23rd April, 2015, 1st of May, 2020 (, is optional)
            r'\b\w{3,9} \d{1,2}-\d{1,2},? \d{2,4}\b',  # Range of dates like March 10-12, 2015
            r'\b\w{3,9} \d{1,2}(st|nd|rd|th)?,? \d{2,4}\b',  # Month Dayth, Year (e.g., October 10th, 2017)
            r'\b\d{2,4}[-]\w{3}-\d{2}\b',  # YYYY-MMM-DD format (e.g., 2020-Dec-21)
            r'\b\w{3,9} \d{1,2}\b',  # Month Day , Common written date formats with day and month abbreviation
            r'\b\d{4}\b' # YYYY format (Year only)
        ]

    def mask(self, text):
        """
        Masks date information in the provided text.
        
        Args:
            text (str): The text containing dates to be masked.
        
        Returns:
            str: The text with masked dates.
        """
        return self._mask_values(text, self.__patterns)


class PhoneMasker(BaseMasker):
    def __init__(self):
        super().__init__("PHONE")
        self.__patterns = [
            r'\b(?:\+91|91|0)?[789]\d{9}\b',   # 10-digit mobile numbers
            r'\b(?:\d{3,4}-)?\d{7,10}\b',  # Landline numbers with area code
            r'\b(?:\+91|91|0)?[789]\d{2}[ -]?\d{3}[ -]?\d{4}\b',  # Mobile numbers with spaces or hyphens
            r'\b(?:\+91|91|0)?[789]\d{9}(?:\s?ext\s?\d{1,4})?\b',  # Numbers with extensions
            r'\b\(\d{3,4}\)\s?\d{7,10}\b',  # Numbers with area code in parentheses
            r'\b\(\d{3,4}\)[-\s]?\d{7,10}\b',  # Landline with parentheses and hyphen/space
            r'\b(?:\+91)[\s]?[789]\d{9}\b',  # Mobile numbers with country code and space
            r'\b\(\+91\)[\s]?[789]\d{9}\b'  # Mobile numbers with country code in parentheses
        ]

    def mask(self, text):
        """
        Masks phone numbers in the provided text.
        
        Args:
            text (str): The text containing phone numbers to be masked.
        
        Returns:
            str: The text with masked phone numbers.
        """
        return self._mask_values(text, self.__patterns)


class TextProcessor:
    def __init__(self):
        self.__maskers = [URLMasker(), EmailMasker(), PhoneMasker(), DateMasker()]

    def __preprocess_function(self, text):
        """
        Preprocesses the text by performing steps such as normalization, tokenization, 
        stopword removal, lemmatization, and restoring placeholders.
        
        Args:
            text (str): The raw text to be preprocessed.
        
        Returns:
            str: The preprocessed text.
        """
        placeholder_pattern = r'(EMAIL|URL|PHONE|DATE)\d+'
    
        placeholders = re.findall(placeholder_pattern, text)
        temp_placeholders = {ph: f"placeholder_{i}" for i, ph in enumerate(placeholders)}
        for ph, temp in temp_placeholders.items():
            text = text.replace(ph, temp)

        text = text.lower()
        text = re.sub(r'\s+', ' ', text).strip()  # Remove extra whitespaces
        text = re.sub(r'\.{2,}', '.', text)   # Normalize punctuation
        text = re.sub(r'[^\w\s.,<>-]', '', text)  # Remove unwanted characters, ensuring placeholders remain intact
        text = re.sub(r'[\n\t\r]+', ' ', text)  # Replace newlines and tabs with spaces
        text = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', text)  # Remove leading or trailing punctuation marks that aren't part of valid content
        text = re.sub(r'[^\w\s]', '', text)  # Remove all punctuation marks

        stop_words = set(stopwords.words('english'))
        words = word_tokenize(text)   

        lemmatizer = WordNetLemmatizer()

        def get_wordnet_pos(treebank_tag):
            if treebank_tag.startswith('J'):
                return wordnet.ADJ
            elif treebank_tag.startswith('V'):
                return wordnet.VERB
            elif treebank_tag.startswith('N'):
                return wordnet.NOUN
            elif treebank_tag.startswith('R'):
                return wordnet.ADV
            else:
                return wordnet.NOUN  
            
        processed_words = []
        words_with_pos = pos_tag(words) 

        for word, tag in words_with_pos:
            if word in temp_placeholders.values():  
                processed_words.append(word)
            elif word not in stop_words:   
                lemmatized_word = lemmatizer.lemmatize(word, get_wordnet_pos(tag))
                processed_words.append(lemmatized_word)

        text = ' '.join(processed_words)

        for temp, ph in temp_placeholders.items():   
            text = text.replace(ph, temp)
        
        return text


    def process_text(self, raw_text):
        """
        Processes the raw text by applying masking, preprocessing, and unmasking steps.
        
        Args:
            raw_text (str): The raw input text to be processed.
        
        Returns:
            str: The final processed text with original values restored.
        """
        masked_text = raw_text
        for masker in self.__maskers:
            masked_text = masker.mask(masked_text)

        preprocessed_text = self.__preprocess_function(masked_text)

        final_text = preprocessed_text
        for masker in self.__maskers:
            final_text = masker.unmask_values(final_text)
        
        return final_text
