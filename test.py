import unittest
import faiss
import os
from datetime import datetime
from vectorDB.vectordbcpu import VectorDatabaseModule  # Assuming the module is in a file called vector_database_module.py

class TestVectorDatabaseModule(unittest.TestCase):

    def setUp(self):
        """ Set up the test environment """
        self.vector_db = VectorDatabaseModule()
        self.test_text_1 = "This is a test sentence for embedding."
        self.test_text_2 = "This is another test sentence for embedding."
        
    def test_create_and_store_embedding(self):
        """ Test that embeddings are created and stored correctly """
        embedding_id = self.vector_db.create_and_store_embedding(self.test_text_1)
        self.assertIsInstance(embedding_id, str)  # Check that an embedding ID is returned
        self.assertTrue(len(embedding_id) > 0)  # Ensure the ID is not empty
        self.assertEqual(self.vector_db.index.ntotal, 1)  # Check that the embedding has been added to the index

    def test_search(self):
        """ Test that search returns the correct embedding IDs """
        embedding_id_1 = self.vector_db.create_and_store_embedding(self.test_text_1)
        embedding_id_2 = self.vector_db.create_and_store_embedding(self.test_text_2)

        search_results = self.vector_db.search(self.test_text_1, top_k=2)
        self.assertIn(embedding_id_1, search_results)  # Ensure the correct embedding is in the search results
        self.assertIn(embedding_id_2, search_results)  # Ensure the other embedding is returned as well

    def test_save_and_load_index(self):
        """ Test that the FAISS index can be saved and loaded properly """
        embedding_id_1 = self.vector_db.create_and_store_embedding(self.test_text_1)
        self.vector_db.save_index_to_disk('test_faiss.index')
        
        # Simulate a new instance (mimicking application restart or reloading)
        new_vector_db = VectorDatabaseModule()
        new_vector_db.load_index_from_disk('test_faiss.index')
        
        # Check that the index contains the expected embedding
        self.assertEqual(new_vector_db.index.ntotal, 1)  # Ensure the index has the embedding
        self.assertEqual(new_vector_db.metadata[0]['embeddingID'], embedding_id_1)

    def test_save_and_load_metadata(self):
        """ Test that the metadata can be saved and loaded properly """
        embedding_id_1 = self.vector_db.create_and_store_embedding(self.test_text_1)
        self.vector_db.save_metadata_to_disk('test_metadata.pkl')
        
        # Simulate a new instance
        new_vector_db = VectorDatabaseModule()
        new_vector_db.load_metadata_from_disk('test_metadata.pkl')
        
        # Verify metadata integrity
        self.assertIn(0, new_vector_db.metadata)  # Ensure metadata exists
        self.assertEqual(new_vector_db.metadata[0]['embeddingID'], embedding_id_1)

    def tearDown(self):
        """ Clean up after tests """
        if os.path.exists('test_faiss.index'):
            os.remove('test_faiss.index')
        if os.path.exists('test_metadata.pkl'):
            os.remove('test_metadata.pkl')

if __name__ == '__main__':
    unittest.main()
