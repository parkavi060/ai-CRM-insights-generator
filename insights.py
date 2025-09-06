# insights.py
import datetime
import random

# Predefined realistic upsell offers for a fictional B2B software company
UPSELL_OFFERS = [
    "Upgrade to the Enterprise Analytics Suite",
    "Adopt the AI-powered Customer Support Bot",
    "Add Advanced Security & Compliance module",
    "Bundle with Premium API Access",
    "Expand to Multi-User Collaboration features",
    "Upgrade to Dedicated Account Manager + Priority Support"
]

def customer_insight(row):
    """
    row: a pandas Series representing a single customer (must contain churn_prob, engagement_score, segment, last_interaction_date)
    returns: short text insight
    """
    name = row.get('company_name', row.get('customer_id', 'Unknown'))
    prob = float(row.get('churn_prob', 0))
    eng = float(row.get('engagement_score', 0))
    seg = row.get('segment', 'unknown')
    last = row.get('last_interaction_date', None)
    last_str = str(last)[:10] if last is not None else 'N/A'

    reasons = []
    if prob > 0.6:
        reasons.append("high churn probability")
    if eng < 0.35:
        reasons.append("low engagement")
    if row.get('recency_days', 0) > 90:
        reasons.append("no recent contact")

    reason_text = ", ".join(reasons) if reasons else "mixed indicators"
    action = (
        "Recommend outreach: phone call within 48h + 10% renewal incentive."
        if prob > 0.6
        else "Recommend targeted upsell or account review."
    )

    text = f"{name} (segment: {seg}) — churn: {prob:.0%}. Last interaction: {last_str}. Key signals: {reason_text}. {action}"
    return text

def top_insights(df, n=10):
    out = []
    for _, r in df.sort_values('churn_prob', ascending=False).head(n).iterrows():
        out.append({
            "customer_id": r.get('customer_id'),
            "company_name": r.get('company_name'),
            "churn_prob": float(r.get('churn_prob', 0)),
            "insight": customer_insight(r)
        })
    return out

def recommend_upsell(row):
    # rule-based: high_value, low product diversity and low churn_prob -> expansion opportunity
    if (
        row.get('segment') == 'high_value'
        and row.get('product_diversity', 0) <= 2
        and row.get('churn_prob', 0) < 0.4
    ):
        offer = random.choice(UPSELL_OFFERS)
        return f"{row.get('company_name')} is a strong candidate for upsell → {offer}."
    return None
