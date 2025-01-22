import os
import torch
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

        self.__tokenizer.pad_token = self.__tokenizer.eos_token
        self.__model.config.pad_token_id = self.__tokenizer.pad_token_id

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
         # Prepare the prompt
        if not input_text.strip() or not user_query.strip():
            return "Invalid input: input text and user query cannot be empty."

        self.__tokenizer.pad_token = self.__tokenizer.eos_token
        prompt = f"Content: {input_text}\nUser Query: {user_query}\nResponse:"

        # Truncate input to fit within model's max length
        max_input_length = 1024 - max_length - 10  # Reserve space for the response
        tokenized_input = self.__tokenizer.encode(prompt, truncation=True, max_length=max_input_length, return_tensors="pt")
        
        # Attention mask for padding
        attention_mask = (tokenized_input != self.__tokenizer.pad_token_id).long()
        
        print(f"Tokenized input length: {len(tokenized_input[0])}")

        self.__model.config.pad_token_id = self.__model.config.eos_token_id
        outputs = self.__model.generate(
            tokenized_input,
            attention_mask=attention_mask,
            max_new_tokens=max_length,
            num_return_sequences=1,
            no_repeat_ngram_size=2
        )
        response = self.__tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response