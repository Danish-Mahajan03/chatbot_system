import faiss
import torch
import os
import pickle
import numpy as np
import uuid
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

class VectorDatabaseModule:
    """
    This class handles the creation and management of a vector database using FAISS,
    enabling the storage of text embeddings, metadata, and performing semantic search.
    """
    def __init__(self):
        """
        Initializes the vector database module by loading the FAISS index and metadata from disk, 
        or creating them if they don't exist. Also initializes the sentence transformer model 
        for generating text embeddings.
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SentenceTransformer(os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")).to(self.device)
        self.vector_dim = int(os.getenv("VECTOR_DIM", 384))
        self.index_file = os.getenv("FAISS_INDEX_FILE", "faiss_index_file.index")
        self.metadata_file = os.getenv("METADATA_FILE", "metadata.pkl")
        
        self.index = None
        self.metadata = {}

        if torch.cuda.is_available():
            self.res = faiss.StandardGpuResources()  
            self.index = faiss.IndexFlatL2(self.vector_dim)  
            self.index = faiss.index_cpu_to_gpu(self.res, 0, self.index)   
        else:
            self.index = faiss.IndexFlatL2(self.vector_dim)

        if os.path.exists(self.index_file):
            self.load_index_from_disk(self.index_file) 

        if os.path.exists(self.metadata_file):
            self.load_metadata_from_disk(self.metadata_file)

    def create_and_store_embedding(self, text):
        """
        Creates an embedding for the provided text, stores it in the FAISS index, 
        and stores the metadata with a unique embedding ID.
        
        Args:
            text (str): The input text to be embedded.
        
        Returns:
            str: The unique embedding ID for the stored embedding.
        """
        embedding_id = str(uuid.uuid4())
        embedding = self.model.encode([text], device=self.device)[0]
        self.index.add(np.array([embedding]))
        self.save_index_to_disk(self.index_file)

        self.metadata[len(self.metadata)] = {'embeddingID': embedding_id}
        self.save_metadata_to_disk(self.metadata_file)

        return embedding_id

    def search(self, query_text, top_k=5):
        """
        Searches the vector database for the most similar embeddings to the query text.
        
        Args:
            query_text (str): The input text to search for.
            top_k (int): The number of top results to return.
        
        Returns:
            list: A list of embedding IDs of the top-k most similar embeddings.
        """
        query_embedding = self.model.encode([query_text], device=self.device)
        distances, indices = self.index.search(np.array(query_embedding), top_k)
        results = []
        for idx in indices[0]:
            if idx in self.metadata:
                 embedding_id = self.metadata[idx].get('embeddingID')
                 if embedding_id is not None:
                    results.append(embedding_id)
        return results

    def save_index_to_disk(self, index_file='faiss_index_file.index'):
        """
        Saves the current FAISS index to disk.
        
        Args:
            index_file (str): Path to the file where the index will be saved.
        """
        if torch.cuda.is_available():
            cpu_index = faiss.index_gpu_to_cpu(self.index)
            faiss.write_index(cpu_index, index_file)
        else:
            faiss.write_index(self.index, index_file)
    
    def load_index_from_disk(self, index_file='faiss_index_file.index'):
        """
        Loads a FAISS index from the disk.
        
        Args:
            index_file (str): Path to the index file to load.
        """
        if torch.cuda.is_available():
            cpu_index = faiss.read_index(index_file)
            self.index = faiss.index_cpu_to_gpu(self.res, 0, cpu_index)
        else:
            self.index = faiss.read_index(index_file)

    def save_metadata_to_disk(self, metadata_file='metadata.pkl'):
        """
        Saves the metadata dictionary to disk using pickle.
        
        Args:
            metadata_file (str): Path to the file where metadata will be saved.
        """
        with open(metadata_file, 'wb') as f:
            pickle.dump(self.metadata, f)

    def load_metadata_from_disk(self, metadata_file='metadata.pkl'):
        """
        Loads the metadata dictionary from disk using pickle.
        
        Args:
            metadata_file (str): Path to the metadata file to load.
        """
        with open(metadata_file, 'rb') as f:
            self.metadata = pickle.load(f)