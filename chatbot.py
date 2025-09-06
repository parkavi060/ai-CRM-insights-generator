# chatbot_improved.py
import re
import random
from difflib import get_close_matches
from insights import top_insights, customer_insight, recommend_upsell

# Conversation context storage
GREETINGS = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
BYES = ["bye", "goodbye", "see ya", "talk later", "see you"]
THANKS = ["thank you", "thanks", "thx", "thankyou"]

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

def _is_contained_any(phrase, words):
    return any(w in phrase for w in words)

def _format_list_for_context(results):
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

def handle_query(query: str, df, context: dict = None):
    if context is None:
        context = {}

    q = query.lower().strip()

    # 1) Social replies
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

    # 2) Follow-up requests (tell me more about 2)
    m = re.search(r"(?:tell me more about|details for|more about|info on)\s+(\d+)", q)
    if m and context.get('last_list'):
        idx = int(m.group(1))
        for it in context['last_list']:
            if it['rank'] == idx:
                row = df[df['customer_id'].astype(str) == str(it['id'])]
                if row.empty:
                    return f"I couldn't load full details for item {idx} (ID {it['id']}).", context
                text = customer_insight(row.iloc[0])
                return text, context
        return f"I don't have item {idx} in the last list. Try one of these: {', '.join(str(x['rank']) for x in context['last_list'])}", context

    # 3) Intent detection
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

    # 4) Handle intents
    if intent in ['churn', 'high_risk']:
        results = top_insights(df, n=10)
        display, structured = _format_list_for_context(results)
        context['last_list'] = structured
        resp = "🚨 Chrun or High-risk customers:\n" + display + "\n\nYou can say 'give details for 2' to get more info."
        return resp, context

    if intent == 'low_risk':
        rows = df[df['churn_prob'] < 0.2].sort_values('churn_prob').head(10)
        if rows.empty:
            return "No low-risk customers found.", context
        lines = [f"{i+1}. {r['company_name']} (ID {r['customer_id']}) — churn {r['churn_prob']:.0%}" for i, r in rows.iterrows()]
        structured = [{"rank": i+1, "id": r['customer_id'], "company": r['company_name'], "insight": ''} for i, r in rows.iterrows()]
        context['last_list'] = structured
        return "✅ Low-risk customers:\n" + "\n".join(lines), context

    if intent == 'high_value':
        rows = df[df['segment'] == 'high_value'].sort_values('purchase_history', ascending=False).head(10)
        if rows.empty:
            return "No high-value customers found.", context
        lines = [f"{i+1}. {r['company_name']} (ID {r['customer_id']}) — spent {r['purchase_history']}" for i, r in rows.iterrows()]
        structured = []
        for i, r in enumerate(rows.itertuples(), start=1):
            structured.append({"rank": i, "id": getattr(r, 'customer_id'), "company": getattr(r, 'company_name'), "insight": ''})
        context['last_list'] = structured
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
        context['last_list'] = [{"rank": i+1, "id": c['id'], "company": c['company'], "insight": c['rec']} for i, c in enumerate(cand[:10])]
        resp = "💡 Upsell candidates:\n" + "\n".join(lines)
        return resp, context

    if intent == 'segment':
        dist = df['segment'].value_counts().to_dict()
        context.pop('last_list', None)
        return f"📊 Segment distribution:\n{dist}", context

    if intent == 'customer':
        m = re.search(r'(?:tell me about|info on|details for|show customer|who is)\\s+([A-Za-z0-9_ -]+)', q)
        if m:
            cid = m.group(1).strip().upper()
            row = df[(df['customer_id'].astype(str).str.upper() == cid) | (df['company_name'].str.upper() == cid)]
            if row.empty:
                return f"No customer matching '{cid}'. Try a customer id like C00001.", context
            return customer_insight(row.iloc[0]), context

    # 5) Fallback
    closest = get_close_matches(q, DEFAULT_SUGGESTIONS, n=1)
    hint = f" Did you mean: '{closest[0]}'?" if closest else ""
    return "🤔 I didn't quite get that." + hint, context


# Example usage:
# df = pd.read_csv("data/crm_enriched.csv")   # after preprocessing
# context = {}
# resp, context = handle_query("show top churn accounts", df, context)
# print(resp)
