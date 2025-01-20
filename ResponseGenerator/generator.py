import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from dotenv import load_dotenv

load_dotenv()

class GenerativeModule:
    def __init__(self):
        """
        Initialize the generative module with a pretrained model and tokenizer.
        """
        model_name = os.getenv("MODEL_NAME")
        self.__tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.__model = AutoModelForCausalLM.from_pretrained(model_name)
    
    def generate_response(self, input_text, user_query, max_length=150):
        """
        Generate a response based on the input text and user query.
        
        Args:
            input_text (str): Text fetched from the database.
            user_query (str): User's query for context.
            max_length (int): Maximum length of the generated response.
        
        Returns:
            str: Generated response.
        """
        prompt = f"Content: {input_text}\nUser Query: {user_query}\nResponse:"
        inputs = self.__tokenizer.encode(prompt, return_tensors="pt")
        outputs = self.__model.generate(inputs, max_length=max_length, num_return_sequences=1, no_repeat_ngram_size=2)
        response = self.__tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response