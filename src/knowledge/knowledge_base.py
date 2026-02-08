import chromadb
from chromadb.utils import embedding_functions
import uuid
import os

class KnowledgeBase:
    """
    A simple RAG-based Knowledge Base using ChromaDB.
    """
    def __init__(self, path="./chroma_db", collection_name="agent_knowledge"):
        """
        Initialize the Knowledge Base.
        
        Args:
            path (str): Path to persist the ChromaDB database.
            collection_name (str): Name of the collection to replicate.
        """
        self.client = chromadb.PersistentClient(path=path)
        
        # Use default embedding function (all-MiniLM-L6-v2)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def add_document(self, content: str, metadata: dict = None, doc_id: str = None):
        """
        Add a document to the knowledge base.
        
        Args:
            content (str): The text content to add.
            metadata (dict, optional): Metadata associated with the document (e.g., source, author).
            doc_id (str, optional): Unique ID for the document. If None, a UUID is generated.
        """
        if doc_id is None:
            doc_id = str(uuid.uuid4())
            
        if metadata is None:
            metadata = {}
            
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def query(self, query_text: str, n_results: int = 5):
        """
        Query the knowledge base for relevant documents.
        
        Args:
            query_text (str): The query string.
            n_results (int): Number of results to return.
            
        Returns:
            dict: Query results containing 'documents', 'metadatas', and 'distances'.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results

    def count(self):
        """Return the number of documents in the collection."""
        return self.collection.count()

    def reset(self):
        """Clear the collection (use with caution)."""
        # Note: ChromaDB client.reset() is not always enabled by default for safety.
        # We can delete and recreate the collection instead.
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            embedding_function=self.embedding_fn
        )
