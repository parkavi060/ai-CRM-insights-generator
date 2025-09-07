# RAG-Enhanced CRM Chatbot Setup Guide

This guide will help you set up and use the RAG (Retrieval-Augmented Generation) enhanced chatbot for your CRM system using ChromaDB and Google Gemini API.

## Features

- **RAG Integration**: Uses ChromaDB for vector storage and retrieval
- **Gemini API**: Powered by Google's Gemini Pro model for natural language generation
- **Hybrid Approach**: Combines rule-based responses with AI-generated insights
- **Customer Data Analysis**: Provides insights on churn, segments, and customer behavior
- **Interactive Mode**: Both programmatic and interactive chat interfaces

## Prerequisites

1. **Python 3.8+**
2. **Google Gemini API Key** - Get one from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. **CRM Data** - Your processed customer data in CSV format

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key-here"
   ```

3. **Verify Data File**:
   Ensure your data file is at `data/processed_customers.csv` or update the path in `config.py`

## Quick Start

### 1. Run the Demo
```bash
python demo_rag.py
```

### 2. Interactive Mode
```bash
python demo_rag.py --interactive
```

### 3. Programmatic Usage
```python
from enhanced_chatbot import EnhancedChatbot
import os

# Initialize chatbot
chatbot = EnhancedChatbot(
    gemini_api_key=os.getenv("GEMINI_API_KEY"),
    data_file_path="data/processed_customers.csv"
)

# Chat with the bot
response, context = chatbot.handle_query("Show me high-value customers")
print(response)
```

## Example Queries

### Simple Queries (Rule-based)
- "Show me high-value customers"
- "Who are at risk of churning?"
- "List low-risk customers"
- "Tell me about customer 1"
- "Show customer segments"

### Complex Queries (RAG-powered)
- "Analyze the relationship between engagement score and churn probability"
- "What are the main trends in customer behavior?"
- "Compare high-value and at-risk customer segments"
- "What insights can you provide about healthcare industry customers?"
- "Explain the correlation between purchase history and churn risk"

## Configuration

Edit `config.py` to customize:

```python
class Config:
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Data paths
    DATA_FILE_PATH = "data/processed_customers.csv"
    CHROMA_DB_PATH = "./chroma_db"
    
    # RAG Settings
    COLLECTION_NAME = "crm_insights"
    RAG_THRESHOLD = 0.7  # Threshold for using RAG vs rule-based
    MAX_RETRIEVAL_RESULTS = 5
    
    # Chatbot Settings
    USE_RAG = True
    ENABLE_LOGGING = True
```

## How It Works

### 1. Data Processing
- Customer data is loaded from CSV
- Each customer record is converted to a text document
- Documents are embedded using sentence transformers
- Embeddings are stored in ChromaDB

### 2. Query Processing
- User queries are analyzed for complexity
- Simple queries use rule-based responses
- Complex queries use RAG (retrieval + generation)
- Relevant documents are retrieved from ChromaDB
- Gemini API generates responses with context

### 3. Response Generation
- Rule-based: Fast, deterministic responses for common queries
- RAG-based: AI-generated insights with data context
- Fallback: Suggestions when queries aren't understood

## File Structure

```
├── rag_chatbot.py          # Core RAG implementation
├── enhanced_chatbot.py     # Hybrid chatbot with RAG + rules
├── config.py              # Configuration settings
├── demo_rag.py            # Demo and testing script
├── requirements.txt       # Python dependencies
├── data/
│   └── processed_customers.csv  # Your CRM data
└── chroma_db/             # ChromaDB storage (created automatically)
```

## Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY not found"**
   - Set your API key: `export GEMINI_API_KEY="your-key"`
   - Verify the key is valid at Google AI Studio

2. **"Data file not found"**
   - Check the path in `config.py`
   - Ensure your CSV file exists

3. **"Failed to initialize ChromaDB"**
   - Check write permissions in the project directory
   - Try deleting the `chroma_db` folder and restarting

4. **"RAG responses are slow"**
   - Reduce `MAX_RETRIEVAL_RESULTS` in config
   - Increase `RAG_THRESHOLD` to use more rule-based responses

### Performance Tips

- **First Run**: Initial setup may take a few minutes to create embeddings
- **Subsequent Runs**: Much faster as ChromaDB is persistent
- **Memory Usage**: Large datasets may require more RAM for embeddings
- **API Limits**: Monitor your Gemini API usage and quotas

## Advanced Usage

### Custom Embeddings
```python
# Use a different embedding model
from sentence_transformers import SentenceTransformer
embedder = SentenceTransformer('all-mpnet-base-v2')  # Larger, more accurate
```

### Custom Prompts
Modify the prompt in `rag_chatbot.py` to customize how Gemini generates responses.

### Filtering Results
```python
# Query with metadata filters
results = collection.query(
    query_texts=["high value customers"],
    where={"segment": "high_value"},
    n_results=10
)
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your API key and data file
3. Check the logs for detailed error messages
4. Ensure all dependencies are installed correctly

## Next Steps

- Integrate with your existing CRM system
- Add more sophisticated data preprocessing
- Implement user authentication and session management
- Add support for real-time data updates
- Create a web interface using Streamlit or Flask