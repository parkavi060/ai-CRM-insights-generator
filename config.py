"""
Configuration file for the CRM RAG Chatbot
"""

import os
from typing import Optional

class Config:
    """Configuration class for the CRM RAG Chatbot."""
    
    # API Keys
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # Data paths
    DATA_FILE_PATH: str = "data/processed_customers.csv"
    CHROMA_DB_PATH: str = "./chroma_db"
    
    # RAG Settings
    COLLECTION_NAME: str = "crm_insights"
    RAG_THRESHOLD: float = 0.7
    MAX_RETRIEVAL_RESULTS: int = 5
    
    # Chatbot Settings
    USE_RAG: bool = True
    ENABLE_LOGGING: bool = True
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required configuration is present."""
        if not cls.GEMINI_API_KEY:
            print("⚠️ Warning: GEMINI_API_KEY not found in environment variables")
            print("Please set your Gemini API key:")
            print("export GEMINI_API_KEY='your-api-key-here'")
            return False
        
        if not os.path.exists(cls.DATA_FILE_PATH):
            print(f"⚠️ Warning: Data file not found at {cls.DATA_FILE_PATH}")
            return False
        
        return True
    
    @classmethod
    def get_gemini_api_key(cls) -> str:
        """Get the Gemini API key with validation."""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set. Please set it as an environment variable.")
        return cls.GEMINI_API_KEY
