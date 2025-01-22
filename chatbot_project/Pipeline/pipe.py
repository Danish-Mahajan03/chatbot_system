from TextPreprocessing.Preprocess_Text import TextProcessor
from vectorDB.vectordbcpu import VectorDatabaseModule
from ResponseGenerator.generator import GenerativeModule
from chatbot.utils import fetch_and_concatenate_text

class Pipeline:
    def __init__(self):
        self.__text_preprocessor = TextProcessor()
        self.__vector_db = VectorDatabaseModule()
        self.__generator = GenerativeModule()

    def __extract_questions(self, query):  
        # Future Implementation
        return list(query)

    def process_query(self, user_query):
        extracted_questions = self.__extract_questions(user_query)  # list of questions
        preprocessed_questions = [self.__text_preprocessor.process_text(q) for q in extracted_questions]  # list of questions
        
        embedding_ids = list()
        for pre_q in preprocessed_questions:
            embedding_ids += self.__vector_db.search(pre_q)   # list of embedding id's

        retrieved_text = fetch_and_concatenate_text(embedding_ids)
        response = self.__generator.generate_response(retrieved_text, user_query)

        return response 