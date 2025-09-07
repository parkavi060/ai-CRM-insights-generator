"""
RAG-Enhanced Chatbot using ChromaDB and Gemini API
This module provides a retrieval-augmented generation chatbot for CRM insights.
"""

import os
import pandas as pd
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGChatbot:
    def __init__(self, 
                 gemini_api_key: str,
                 data_file_path: str,
                 chroma_db_path: str = "./chroma_db",
                 collection_name: str = "crm_insights"):
        """
        Initialize the RAG chatbot with ChromaDB and Gemini API.
        
        Args:
            gemini_api_key: Google Gemini API key
            data_file_path: Path to the CSV data file
            chroma_db_path: Path to store ChromaDB
            collection_name: Name of the ChromaDB collection
        """
        self.gemini_api_key = gemini_api_key
        self.data_file_path = data_file_path
        self.chroma_db_path = chroma_db_path
        self.collection_name = collection_name
        
        # Initialize components
        self._setup_gemini()
        self._setup_chromadb()
        self._setup_embedder()
        self._load_data()
        
        # Initialize or load the vector database
        self._initialize_vector_db()
    
    def _setup_gemini(self):
        """Initialize Gemini API."""
        try:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {e}")
            raise
    
    def _setup_chromadb(self):
        """Initialize ChromaDB client."""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=self.chroma_db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info("ChromaDB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _setup_embedder(self):
        """Initialize sentence transformer for embeddings."""
        try:
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence transformer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize sentence transformer: {e}")
            raise
    
    def _load_data(self):
        """Load and preprocess the CRM data."""
        try:
            self.df = pd.read_csv(self.data_file_path)
            logger.info(f"Loaded data with {len(self.df)} records")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def _create_document_chunks(self) -> List[Dict[str, Any]]:
        """
        Create document chunks from the CRM data for vector storage.
        Each chunk represents a customer record with relevant context.
        """
        chunks = []
        
        for _, row in self.df.iterrows():
            # Create a comprehensive text representation of each customer
            customer_text = f"""
            Customer ID: {row.get('customer_id', 'N/A')}
            Company Name: {row.get('company_name', 'N/A')}
            Industry: {row.get('industry', 'N/A')}
            Purchase History: ${row.get('purchase_history', 0):,}
            Engagement Score: {row.get('engagement_score', 0)}
            Last Interaction: {row.get('last_interaction_date', 'N/A')}
            Churn Status: {'Churned' if row.get('churn', 0) == 1 else 'Active'}
            Segment: {row.get('segment', 'N/A')}
            Churn Probability: {row.get('churn_prob', 0):.2%}
            Total Spend: ${row.get('total_spend', 0):,}
            Tenure Days: {row.get('tenure_days', 0)}
            Product Diversity: {row.get('product_diversity', 0)}
            """
            
            # Create metadata for filtering and context
            metadata = {
                'customer_id': str(row.get('customer_id', '')),
                'company_name': str(row.get('company_name', '')),
                'industry': str(row.get('industry', '')),
                'segment': str(row.get('segment', '')),
                'churn_status': 'churned' if row.get('churn', 0) == 1 else 'active',
                'churn_probability': float(row.get('churn_prob', 0)),
                'purchase_history': float(row.get('purchase_history', 0)),
                'engagement_score': float(row.get('engagement_score', 0))
            }
            
            chunks.append({
                'id': f"customer_{row.get('customer_id', '')}",
                'text': customer_text.strip(),
                'metadata': metadata
            })
        
        return chunks
    
    def _initialize_vector_db(self):
        """Initialize or load the vector database with customer data."""
        try:
            # Check if collection exists
            try:
                self.collection = self.chroma_client.get_collection(name=self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except:
                # Create new collection
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "CRM customer insights and data"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
                # Add documents to the collection
                self._populate_collection()
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            raise
    
    def _populate_collection(self):
        """Populate the ChromaDB collection with customer data."""
        try:
            chunks = self._create_document_chunks()
            
            # Prepare data for ChromaDB
            documents = [chunk['text'] for chunk in chunks]
            metadatas = [chunk['metadata'] for chunk in chunks]
            ids = [chunk['id'] for chunk in chunks]
            
            # Add to collection in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_metadatas = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                
                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
            
            logger.info(f"Successfully populated collection with {len(documents)} documents")
        except Exception as e:
            logger.error(f"Failed to populate collection: {e}")
            raise
    
    def _retrieve_relevant_documents(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from ChromaDB based on the query.
        
        Args:
            query: User query
            n_results: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            documents = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    documents.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0
                    })
            
            return documents
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            return []
    
    def _generate_response(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """
        Generate a response using Gemini API with retrieved context.
        
        Args:
            query: User query
            context_docs: Retrieved relevant documents
            
        Returns:
            Generated response
        """
        try:
            # Prepare context from retrieved documents
            context_text = "\n\n".join([doc['text'] for doc in context_docs])
            
            # Create prompt for Gemini
            prompt = f"""
            You are an AI assistant specialized in Customer Relationship Management (CRM) insights. 
            You have access to customer data and should provide helpful, accurate responses based on the context provided.
            
            Context from CRM database:
            {context_text}
            
            User Query: {query}
            
            Please provide a helpful response based on the context above. If the query is about specific customers, 
            use the provided data. If it's a general question about CRM insights, provide analysis based on the data.
            Be conversational but professional, and include relevant metrics when appropriate.
            
            Response:
            """
            
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again."
    
    def chat(self, query: str, n_results: int = 5) -> str:
        """
        Main chat function that combines retrieval and generation.
        
        Args:
            query: User query
            n_results: Number of relevant documents to retrieve
            
        Returns:
            Generated response
        """
        try:
            # Retrieve relevant documents
            relevant_docs = self._retrieve_relevant_documents(query, n_results)
            
            if not relevant_docs:
                return "I couldn't find relevant information in the database. Please try rephrasing your question."
            
            # Generate response with context
            response = self._generate_response(query, relevant_docs)
            return response
            
        except Exception as e:
            logger.error(f"Error in chat function: {e}")
            return "I apologize, but I encountered an error. Please try again."
    
    def get_customer_insights(self, customer_id: str) -> Dict[str, Any]:
        """
        Get detailed insights for a specific customer.
        
        Args:
            customer_id: Customer ID to look up
            
        Returns:
            Dictionary with customer insights
        """
        try:
            # Query for specific customer
            results = self.collection.query(
                query_texts=[f"customer {customer_id}"],
                n_results=1,
                where={"customer_id": customer_id}
            )
            
            if results['documents'] and results['documents'][0]:
                doc = results['documents'][0][0]
                metadata = results['metadatas'][0][0] if results['metadatas'] else {}
                
                return {
                    'customer_data': doc,
                    'metadata': metadata,
                    'found': True
                }
            else:
                return {'found': False, 'message': f'Customer {customer_id} not found'}
                
        except Exception as e:
            logger.error(f"Error getting customer insights: {e}")
            return {'found': False, 'message': 'Error retrieving customer data'}
    
    def get_segment_analysis(self, segment: str = None) -> Dict[str, Any]:
        """
        Get analysis for customer segments.
        
        Args:
            segment: Specific segment to analyze (optional)
            
        Returns:
            Dictionary with segment analysis
        """
        try:
            if segment:
                # Query for specific segment
                results = self.collection.query(
                    query_texts=[f"segment {segment}"],
                    n_results=10,
                    where={"segment": segment}
                )
            else:
                # Get all segments
                results = self.collection.query(
                    query_texts=["customer segments analysis"],
                    n_results=50
                )
            
            if results['documents'] and results['documents'][0]:
                return {
                    'documents': results['documents'][0],
                    'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                    'found': True
                }
            else:
                return {'found': False, 'message': 'No segment data found'}
                
        except Exception as e:
            logger.error(f"Error getting segment analysis: {e}")
            return {'found': False, 'message': 'Error retrieving segment data'}


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here")
    DATA_FILE = "data/processed_customers.csv"
    
    if GEMINI_API_KEY == "your-gemini-api-key-here":
        print("Please set your GEMINI_API_KEY environment variable")
    else:
        try:
            # Initialize the RAG chatbot
            chatbot = RAGChatbot(
                gemini_api_key=GEMINI_API_KEY,
                data_file_path=DATA_FILE
            )
            
            # Test queries
            test_queries = [
                "Show me high-value customers",
                "Who are the customers at risk of churning?",
                "Tell me about customer C00001",
                "What are the customer segments?",
                "Show me customers in the healthcare industry"
            ]
            
            print("Testing RAG Chatbot:")
            print("=" * 50)
            
            for query in test_queries:
                print(f"\nQuery: {query}")
                response = chatbot.chat(query)
                print(f"Response: {response}")
                print("-" * 30)
                
        except Exception as e:
            print(f"Error: {e}")
