"""
Enhanced Chatbot with RAG Integration
Combines the original rule-based chatbot with RAG capabilities using ChromaDB and Gemini API.
"""

import os
import re
import random
from difflib import get_close_matches
from typing import Dict, Any, Optional, Tuple
import pandas as pd
from rag_chatbot import RAGChatbot
from insights import top_insights, customer_insight, recommend_upsell

class EnhancedChatbot:
    def __init__(self, 
                 gemini_api_key: str,
                 data_file_path: str,
                 use_rag: bool = True,
                 rag_threshold: float = 0.7):
        """
        Initialize the enhanced chatbot with RAG capabilities.
        
        Args:
            gemini_api_key: Google Gemini API key
            data_file_path: Path to the CSV data file
            use_rag: Whether to use RAG for enhanced responses
            rag_threshold: Confidence threshold for using RAG vs rule-based responses
        """
        self.use_rag = use_rag
        self.rag_threshold = rag_threshold
        
        # Load data for rule-based responses
        self.df = pd.read_csv(data_file_path)
        
        # Initialize RAG chatbot if enabled
        if self.use_rag:
            try:
                self.rag_chatbot = RAGChatbot(
                    gemini_api_key=gemini_api_key,
                    data_file_path=data_file_path
                )
                print("✅ RAG chatbot initialized successfully")
            except Exception as e:
                print(f"⚠️ Failed to initialize RAG chatbot: {e}")
                print("Falling back to rule-based responses only")
                self.use_rag = False
        else:
            self.rag_chatbot = None
        
        # Conversation patterns
        self.GREETINGS = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
        self.BYES = ["bye", "goodbye", "see ya", "talk later", "see you"]
        self.THANKS = ["thank you", "thanks", "thx", "thankyou"]
        
        self.DEFAULT_SUGGESTIONS = [
            "show top churn accounts",
            "suggest upsell for high-value segment",
            "show customer segments",
            "list low-risk customers",
            "show high-value customers",
            "tell me about C00001",
            "who are at risk of churn",
            "give details for 2",
            "upsell candidates",
            "show distribution of segments"
        ]
    
    def _is_contained_any(self, phrase: str, words: list) -> bool:
        """Check if any word from the list appears as a whole word in the phrase."""
        for w in words:
            pattern = r"\b" + re.escape(w) + r"\b"
            if re.search(pattern, phrase):
                return True
        return False
    
    def _format_list_for_context(self, results: list) -> Tuple[str, list]:
        """Format results for context storage."""
        structured = []
        lines = []
        for i, r in enumerate(results, start=1):
            cid = r.get('customer_id')
            cname = r.get('company_name')
            prob = float(r.get('churn_prob', 0))
            insight = r.get('insight', '')
            lines.append(f"{i}. {cname} (ID {cid}) — churn {prob:.0%}")
            structured.append({"rank": i, "id": cid, "company": cname, "insight": insight})
        return "\n".join(lines), structured
    
    def _detect_query_complexity(self, query: str) -> float:
        """
        Detect query complexity to decide between RAG and rule-based responses.
        Returns a score between 0 and 1, where 1 indicates high complexity.
        """
        q = query.lower().strip()
        
        # Simple patterns that work well with rule-based responses
        simple_patterns = [
            r'^(hi|hello|hey)',
            r'^(bye|goodbye)',
            r'^(thank|thanks)',
            r'^show (top|high|low)',
            r'^list (low|high)',
            r'^tell me about \w+',
            r'^give details for \d+',
            r'^upsell candidates',
            r'^show distribution'
        ]
        
        # Check for simple patterns
        for pattern in simple_patterns:
            if re.match(pattern, q):
                return 0.2  # Low complexity
        
        # Complex patterns that benefit from RAG
        complex_indicators = [
            'analyze', 'compare', 'trend', 'pattern', 'insight', 'recommendation',
            'why', 'how', 'what if', 'explain', 'describe', 'summarize',
            'relationship', 'correlation', 'impact', 'effect'
        ]
        
        complexity_score = 0.5  # Base complexity
        
        for indicator in complex_indicators:
            if indicator in q:
                complexity_score += 0.1
        
        # Check for multiple conditions or questions
        if '?' in query or ' and ' in q or ' or ' in q:
            complexity_score += 0.2
        
        return min(complexity_score, 1.0)
    
    def _handle_social_interactions(self, query: str) -> Optional[str]:
        """Handle social interactions like greetings, thanks, and goodbyes."""
        q = query.lower().strip()
        
        if self._is_contained_any(q, self.GREETINGS):
            return random.choice([
                "Hello! 👋 I'm your AI-powered CRM assistant. I can help you with customer insights, churn analysis, and business recommendations. How can I assist you today?",
                "Hi there! 🤖 I have access to your customer data and can provide detailed insights. What would you like to know about your customers?"
            ])
        
        if self._is_contained_any(q, self.THANKS):
            return random.choice([
                "You're welcome! 😊 I'm here whenever you need CRM insights.",
                "Happy to help! Feel free to ask me anything about your customer data."
            ])
        
        if self._is_contained_any(q, self.BYES):
            return random.choice([
                "Goodbye! 👋 Thanks for using the CRM assistant!",
                "See you later! 🎯 Keep those customer insights flowing!"
            ])
        
        return None
    
    def _handle_follow_up_requests(self, query: str, context: dict) -> Optional[str]:
        """Handle follow-up requests for more details."""
        m = re.search(r"(?:tell me more about|details for|more about|info on)\s+(\d+)", query.lower())
        if m and context.get('last_list'):
            idx = int(m.group(1))
            for it in context['last_list']:
                if it['rank'] == idx:
                    row = self.df[self.df['customer_id'].astype(str) == str(it['id'])]
                    if row.empty:
                        return f"I couldn't load full details for item {idx} (ID {it['id']})."
                    text = customer_insight(row.iloc[0])
                    return text
            return f"I don't have item {idx} in the last list. Try one of these: {', '.join(str(x['rank']) for x in context['last_list'])}"
        return None
    
    def _handle_rule_based_intents(self, query: str, context: dict) -> Optional[str]:
        """Handle specific intents using rule-based logic."""
        q = query.lower().strip()
        
        # Intent detection
        intents = {
            "churn": ["churn", "at risk", "likely to cancel", "leaving", "show top churn accounts", "who are at risk"],
            "high_risk": ["high risk", "very risky", "extreme churn"],
            "low_risk": ["low risk", "safe customers", "loyal customers", "list low-risk customers"],
            "high_value": ["high-value", "high value", "top customers", "best customers", "show high-value customers"],
            "upsell": ["upsell", "cross-sell", "expansion", "growth", "upsell candidates", "suggest upsell"],
            "segment": ["segment", "group", "distribution", "breakdown", "show customer segments", "show distribution of segments"],
            "customer": ["tell me about", "info on", "details for", "show customer", "who is"]
        }
        
        def match_intent(phrase):
            for intent, words in intents.items():
                if any(w in phrase for w in words):
                    return intent
            return None
        
        intent = match_intent(q)
        
        # Handle specific intents
        if intent in ['churn', 'high_risk']:
            results = top_insights(self.df, n=10)
            display, structured = self._format_list_for_context(results)
            context['last_list'] = structured
            return "🚨 Churn or High-risk customers:\n" + display + "\n\nYou can say 'give details for 2' to get more info."
        
        if intent == 'low_risk':
            rows = self.df[self.df['churn_prob'] < 0.2].sort_values('churn_prob').head(10)
            if rows.empty:
                return "No low-risk customers found."
            lines = [f"{i+1}. {r['company_name']} (ID {r['customer_id']}) — churn {r['churn_prob']:.0%}" for i, r in rows.iterrows()]
            structured = [{"rank": i+1, "id": r['customer_id'], "company": r['company_name'], "insight": ''} for i, r in rows.iterrows()]
            context['last_list'] = structured
            return "✅ Low-risk customers:\n" + "\n".join(lines)
        
        if intent == 'high_value':
            rows = self.df[self.df['segment'] == 'high_value'].sort_values('purchase_history', ascending=False).head(10)
            if rows.empty:
                return "No high-value customers found."
            lines = [f"{i+1}. {r['company_name']} (ID {r['customer_id']}) — spent ${r['purchase_history']:,}" for i, r in rows.iterrows()]
            structured = []
            for i, r in enumerate(rows.itertuples(), start=1):
                structured.append({"rank": i, "id": getattr(r, 'customer_id'), "company": getattr(r, 'company_name'), "insight": ''})
            context['last_list'] = structured
            return "🏆 High-value customers:\n" + "\n".join(lines)
        
        if intent == 'upsell':
            cand = []
            for _, r in self.df.iterrows():
                rec = recommend_upsell(r)
                if rec:
                    cand.append({"id": r.get('customer_id'), "company": r.get('company_name'), "rec": rec})
            if not cand:
                return "No immediate upsell candidates found by the rule."
            lines = [f"{i+1}. {c['company']} (ID {c['id']}) — {c['rec']}" for i, c in enumerate(cand[:10])]
            context['last_list'] = [{"rank": i+1, "id": c['id'], "company": c['company'], "insight": c['rec']} for i, c in enumerate(cand[:10])]
            return "💡 Upsell candidates:\n" + "\n".join(lines)
        
        if intent == 'segment':
            dist = self.df['segment'].value_counts().to_dict()
            context.pop('last_list', None)
            return f"📊 Segment distribution:\n{dist}"
        
        if intent == 'customer':
            m = re.search(r'(?:tell me about|info on|details for|show customer|who is)\s+([A-Za-z0-9_ -]+)', q)
            if m:
                cid = m.group(1).strip().upper()
                row = self.df[(self.df['customer_id'].astype(str).str.upper() == cid) | (self.df['company_name'].str.upper() == cid)]
                if row.empty:
                    return f"No customer matching '{cid}'. Try a customer id like C00001."
                return customer_insight(row.iloc[0])
        
        return None
    
    def handle_query(self, query: str, context: dict = None) -> Tuple[str, dict]:
        """
        Main query handler that combines rule-based and RAG responses.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            Tuple of (response, updated_context)
        """
        if context is None:
            context = {}
        
        # Handle social interactions first
        social_response = self._handle_social_interactions(query)
        if social_response:
            return social_response, context
        
        # Handle follow-up requests
        follow_up_response = self._handle_follow_up_requests(query, context)
        if follow_up_response:
            return follow_up_response, context
        
        # Determine query complexity
        complexity = self._detect_query_complexity(query)
        
        # Try rule-based responses first for simple queries
        if complexity < self.rag_threshold:
            rule_response = self._handle_rule_based_intents(query, context)
            if rule_response:
                return rule_response, context
        
        # Use RAG for complex queries or when rule-based fails
        if self.use_rag and self.rag_chatbot:
            try:
                rag_response = self.rag_chatbot.chat(query)
                if rag_response and "I couldn't find relevant information" not in rag_response:
                    return rag_response, context
            except Exception as e:
                print(f"RAG error: {e}")
        
        # Fallback to rule-based for complex queries if RAG fails
        if complexity >= self.rag_threshold:
            rule_response = self._handle_rule_based_intents(query, context)
            if rule_response:
                return rule_response, context
        
        # Final fallback
        closest = get_close_matches(query.lower(), self.DEFAULT_SUGGESTIONS, n=1)
        hint = f" Did you mean: '{closest[0]}'?" if closest else ""
        
        suggestions = "\n".join([f"• {suggestion}" for suggestion in self.DEFAULT_SUGGESTIONS[:5]])
        return f"🤔 I didn't quite understand that query. Here are some things you can ask me:\n\n{suggestions}\n\n{hint}", context


# Example usage
if __name__ == "__main__":
    # Example usage
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here")
    DATA_FILE = "data/processed_customers.csv"
    
    if GEMINI_API_KEY == "your-gemini-api-key-here":
        print("Please set your GEMINI_API_KEY environment variable")
    else:
        try:
            # Initialize the enhanced chatbot
            chatbot = EnhancedChatbot(
                gemini_api_key=GEMINI_API_KEY,
                data_file_path=DATA_FILE,
                use_rag=True
            )
            
            # Test queries
            test_queries = [
                "Hello!",
                "Show me high-value customers",
                "Who are the customers at risk of churning?",
                "Analyze the relationship between engagement score and churn probability",
                "What are the main trends in customer behavior?",
                "Tell me about customer 1",
                "Thank you!"
            ]
            
            print("Testing Enhanced Chatbot:")
            print("=" * 50)
            
            context = {}
            for query in test_queries:
                print(f"\nQuery: {query}")
                response, context = chatbot.handle_query(query, context)
                print(f"Response: {response}")
                print("-" * 30)
                
        except Exception as e:
            print(f"Error: {e}")


# Compatibility function for existing server.py
def handle_query(query: str, df, context: dict = None):
    """
    Compatibility function for existing server.py
    This maintains the original interface while using the enhanced chatbot.
    """
    if context is None:
        context = {}
    
    # Try to use the enhanced chatbot if possible
    try:
        # Check if we have a Gemini API key
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key and gemini_api_key != "your-gemini-api-key-here":
            # Use enhanced chatbot
            chatbot = EnhancedChatbot(
                gemini_api_key=gemini_api_key,
                data_file_path="data/processed_customers.csv",
                use_rag=True
            )
            response, context = chatbot.handle_query(query, context)
            return response, context
    except Exception as e:
        print(f"Enhanced chatbot failed, falling back to rule-based: {e}")
    
    # Fallback to original rule-based logic
    q = query.lower().strip()
    
    # Social interactions
    GREETINGS = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    BYES = ["bye", "goodbye", "see ya", "talk later", "see you"]
    THANKS = ["thank you", "thanks", "thx", "thankyou"]
    
    def _is_contained_any(phrase, words):
        return any(w in phrase for w in words)
    
    if _is_contained_any(q, GREETINGS):
        return random.choice([
            "Hello! 👋 How can I help with CRM insights today?",
            "Hi there — ask me about churn, segments, or upsell opportunities."
        ]), context
    
    if _is_contained_any(q, THANKS):
        return random.choice([
            "You're welcome! 😊",
            "Happy to help!"
        ]), context
    
    if _is_contained_any(q, BYES):
        return random.choice([
            "Goodbye! 👋",
            "Talk soon — good luck with the demo! 🎥"
        ]), context
    
    # Intent detection and handling
    intents = {
        "churn": ["churn", "at risk", "likely to cancel", "leaving", "show top churn accounts", "who are at risk"],
        "high_risk": ["high risk", "very risky", "extreme churn"],
        "low_risk": ["low risk", "safe customers", "loyal customers", "list low-risk customers"],
        "high_value": ["high-value", "high value", "top customers", "best customers", "show high-value customers"],
        "upsell": ["upsell", "cross-sell", "expansion", "growth", "upsell candidates", "suggest upsell"],
        "segment": ["segment", "group", "distribution", "breakdown", "show customer segments", "show distribution of segments"],
        "customer": ["tell me about", "info on", "details for", "show customer", "who is"]
    }
    
    def match_intent(phrase):
        for intent, words in intents.items():
            if any(w in phrase for w in words):
                return intent
        return None
    
    intent = match_intent(q)
    
    # Handle specific intents
    if intent in ['churn', 'high_risk']:
        results = top_insights(df, n=10)
        lines = []
        for i, r in enumerate(results, start=1):
            cid = r.get('customer_id')
            cname = r.get('company_name')
            prob = float(r.get('churn_prob', 0))
            lines.append(f"{i}. {cname} (ID {cid}) — churn {prob:.0%}")
        return "🚨 Churn or High-risk customers:\n" + "\n".join(lines), context
    
    if intent == 'low_risk':
        rows = df[df['churn_prob'] < 0.2].sort_values('churn_prob').head(10)
        if rows.empty:
            return "No low-risk customers found.", context
        lines = [f"{i+1}. {r['company_name']} (ID {r['customer_id']}) — churn {r['churn_prob']:.0%}" for i, r in rows.iterrows()]
        return "✅ Low-risk customers:\n" + "\n".join(lines), context
    
    if intent == 'high_value':
        rows = df[df['segment'] == 'high_value'].sort_values('purchase_history', ascending=False).head(10)
        if rows.empty:
            return "No high-value customers found.", context
        lines = [f"{i+1}. {r['company_name']} (ID {r['customer_id']}) — spent ${r['purchase_history']:,}" for i, r in rows.iterrows()]
        return "🏆 High-value customers:\n" + "\n".join(lines), context
    
    if intent == 'upsell':
        cand = []
        for _, r in df.iterrows():
            rec = recommend_upsell(r)
            if rec:
                cand.append({"id": r.get('customer_id'), "company": r.get('company_name'), "rec": rec})
        if not cand:
            return "No immediate upsell candidates found by the rule.", context
        lines = [f"{i+1}. {c['company']} (ID {c['id']}) — {c['rec']}" for i, c in enumerate(cand[:10])]
        return "💡 Upsell candidates:\n" + "\n".join(lines), context
    
    if intent == 'segment':
        dist = df['segment'].value_counts().to_dict()
        return f"📊 Segment distribution:\n{dist}", context
    
    if intent == 'customer':
        m = re.search(r'(?:tell me about|info on|details for|show customer|who is)\s+([A-Za-z0-9_ -]+)', q)
        if m:
            cid = m.group(1).strip().upper()
            row = df[(df['customer_id'].astype(str).str.upper() == cid) | (df['company_name'].str.upper() == cid)]
            if row.empty:
                return f"No customer matching '{cid}'. Try a customer id like C00001.", context
            return customer_insight(row.iloc[0]), context
    
    # Fallback
    DEFAULT_SUGGESTIONS = [
        "show top churn accounts",
        "suggest upsell for high-value segment",
        "show customer segments",
        "list low-risk customers",
        "show high-value customers",
        "tell me about C00001",
        "who are at risk of churn",
        "give details for 2",
        "upsell candidates",
        "show distribution of segments"
    ]
    
    closest = get_close_matches(q, DEFAULT_SUGGESTIONS, n=1)
    hint = f" Did you mean: '{closest[0]}'?" if closest else ""
    return "🤔 I didn't quite get that." + hint, context
