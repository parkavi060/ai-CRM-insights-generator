# 🤖 AI-Enhanced Customer Relationship Management (CRM) Insights Generator

A comprehensive CRM analytics platform that combines traditional machine learning with cutting-edge RAG (Retrieval-Augmented Generation) technology to provide intelligent customer insights, churn prediction, and conversational AI assistance.

## 🌟 Features

### 🧠 **AI-Powered Analytics**
- **RAG-Enhanced Chatbot**: Conversational AI using ChromaDB + Google Gemini API
- **Churn Prediction**: Machine learning models to identify at-risk customers
- **Customer Segmentation**: K-means clustering for customer categorization
- **Upsell Recommendations**: Intelligent cross-sell and upsell opportunities

### 📊 **Interactive Dashboard**
- **Real-time Visualizations**: Interactive charts and graphs
- **Customer Insights**: Detailed customer profiles and behavior analysis
- **Risk Assessment**: Visual churn probability indicators
- **Segment Analysis**: Customer group performance metrics

### 🔍 **Advanced Query Capabilities**
- **Natural Language Processing**: Ask questions in plain English
- **Complex Analytics**: Deep insights into customer relationships
- **Contextual Responses**: Maintains conversation context
- **Hybrid Intelligence**: Combines rule-based and AI-generated responses

## 🏗️ Architecture

### **Backend Components**
- **Flask Web Server**: RESTful API endpoints
- **RAG System**: ChromaDB vector database + Gemini API
- **ML Pipeline**: scikit-learn models for prediction and clustering
- **Data Processing**: Pandas/NumPy for data manipulation

### **Frontend Components**
- **Responsive Web Interface**: Bootstrap 5 + JavaScript
- **Interactive Charts**: Plotly.js for dynamic visualizations
- **Real-time Chat**: WebSocket-based chatbot interface
- **Mobile-Friendly**: Responsive design for all devices

## 📁 Project Structure

```
├── 🧠 Core AI Components
│   ├── rag_chatbot.py          # RAG implementation with ChromaDB
│   ├── chatbot.py              # Enhanced hybrid chatbot
│   ├── ml_models.py            # Machine learning pipeline
│   └── insights.py             # Business intelligence functions
│
├── 🌐 Web Application
│   ├── server.py               # Flask backend server
│   ├── templates/index.html    # Main dashboard interface
│   └── static/                 # CSS, JS, and assets
│
├── 📊 Data & Configuration
│   ├── data/                   # Customer data files
│   ├── models/                 # Trained ML models
│   ├── config.py               # System configuration
│   └── requirements.txt        # Python dependencies
│
└── 🧪 Testing & Utilities
    ├── simple_rag_test.py      # Basic functionality tests
    ├── data_generation.py      # Mock data generation
    └── RAG_SETUP.md           # Detailed setup guide
```

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))
- 2GB+ RAM (for ML models and vector database)

### **Installation**

1. **Clone and Setup**
   ```bash
   git clone https://github.com/parkavi060/ai-CRM-insights-generator.git
   cd AI-Enhanced-Customer-Relationship-Management-CRM-Insights-Generator
   python -m venv venv
   venv/bin/activate.ps1
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key-here"
   ```

4. **Run the Application**
   ```bash
   python server.py
   ```

5. **Access the Dashboard**
   Open your browser to `http://localhost:5000`

## 💬 Chatbot Capabilities

### **Simple Queries (Rule-based)**
- "Show me high-value customers"
- "Who are at risk of churning?"
- "List low-risk customers"
- "Tell me about customer 1"
- "Show customer segments"

### **Complex Queries (RAG-powered)**
- "Analyze the relationship between engagement score and churn probability"
- "What are the main trends in customer behavior?"
- "Compare high-value and at-risk customer segments"
- "What insights can you provide about healthcare industry customers?"
- "Explain the correlation between purchase history and churn risk"

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard interface |
| `/api/summary` | GET | Overall CRM metrics and insights |
| `/api/segment/<segment>` | GET | Customers in specific segment |
| `/api/upsell` | GET | Upsell candidate recommendations |
| `/api/info` | GET | System information and features |
| `/api/chat` | POST | Chatbot conversation endpoint |

## 🎯 Use Cases

### **Sales Teams**
- Identify high-value prospects
- Prioritize at-risk accounts
- Discover upsell opportunities
- Get customer insights on-demand

### **Customer Success**
- Monitor customer health scores
- Predict churn risk
- Analyze engagement patterns
- Generate retention strategies

### **Business Intelligence**
- Segment analysis and trends
- Revenue forecasting insights
- Customer lifetime value analysis
- Market behavior patterns

## 🛠️ Configuration

### **Environment Variables**
```bash
GEMINI_API_KEY=your-gemini-api-key-here
```

### **Customization Options**
Edit `config.py` to modify:
- Data file paths
- RAG threshold settings
- ChromaDB configuration
- Logging preferences

## 📈 Machine Learning Models

### **Churn Prediction**
- **Algorithm**: Random Forest Classifier
- **Features**: Engagement score, purchase history, tenure, recency
- **Output**: Churn probability (0-1)

### **Customer Segmentation**
- **Algorithm**: K-means Clustering
- **Features**: RFM analysis (Recency, Frequency, Monetary)
- **Segments**: High-value, Mid-value, At-risk, Low-value

### **Upsell Recommendations**
- **Logic**: Rule-based + ML insights
- **Factors**: Purchase history, engagement, segment
- **Output**: Personalized recommendations

## 🔍 RAG System Details

### **Vector Database**
- **Technology**: ChromaDB
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Storage**: Persistent local database

### **Language Model**
- **Provider**: Google Gemini Pro
- **Capabilities**: Natural language understanding and generation
- **Context**: Customer data + conversation history

### **Retrieval Process**
1. Query embedding generation
2. Similarity search in ChromaDB
3. Context retrieval and ranking
4. Response generation with Gemini API

## 🧪 Testing

### **Basic Functionality Test**
```bash
python simple_rag_test.py
```

### **RAG System Test**
```bash
python -c "from rag_chatbot import RAGChatbot; print('RAG system ready')"
```

### **Web Server Test**
```bash
python -c "from server import app; print('Flask app ready')"
```

## 📊 Sample Data

The system includes mock CRM data with:
- **500 customer records**
- **19 features** including demographics, behavior, and predictions
- **Multiple industries**: Healthcare, Retail, IT, Manufacturing, Education
- **Realistic patterns**: Churn rates, purchase behaviors, engagement scores

## 🔒 Security & Privacy

- **API Key Management**: Environment variable storage
- **Data Privacy**: Local processing, no external data transmission
- **Access Control**: Configurable authentication (future enhancement)
- **Data Encryption**: ChromaDB built-in security features

## 🚀 Performance

### **Optimization Features**
- **Caching**: ChromaDB persistent storage
- **Batch Processing**: Efficient data loading
- **Lazy Loading**: On-demand model initialization
- **Memory Management**: Optimized for 2GB+ systems

### **Scalability**
- **Horizontal Scaling**: Multiple server instances
- **Database Scaling**: ChromaDB cluster support
- **API Rate Limiting**: Configurable request limits

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contact

**Developer**: Parkavi. S  
**Email**: parkavisaravanan06@gmail.com  
**Project**: AI-Enhanced CRM Insights Generator

## 🔮 Future Enhancements

- **Real-time Data Integration**: Live CRM system connections
- **Advanced NLP**: Sentiment analysis and conversation insights
- **Predictive Analytics**: Revenue forecasting and trend analysis
- **Multi-language Support**: International customer base support
- **Mobile App**: Native iOS/Android applications
- **Advanced Security**: OAuth2, role-based access control

## 📚 Documentation

- **[RAG Setup Guide](RAG_SETUP.md)**: Detailed RAG system configuration
- **[API Documentation](docs/api.md)**: Complete API reference
- **[Deployment Guide](docs/deployment.md)**: Production deployment instructions

---


**Built with ❤️ using Python, Flask, ChromaDB, and Google Gemini API**

