"""
Flask backend providing:
- index page
- /api/summary --> overall counts, top risk, upsell
- /api/segment/<segment> --> customers in selected segment
- /api/upsell --> upsell candidates
- /api/info --> foundational info for mini web page
- /api/chat --> chatbot endpoint (POST {"query": "..."} )
"""

import os
from flask import Flask, render_template, jsonify, request
import pandas as pd
from chatbot import handle_query
from insights import recommend_upsell

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")
STATIC_FOLDER = os.path.join(BASE_DIR, "static")
DATA_FILE = os.path.join(BASE_DIR, "data", "processed_customers.csv")

app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)


def load_dataframe():
    """Load preprocessed customer data. Ensure required columns exist or add defaults."""
    if not os.path.exists(DATA_FILE):
        raise SystemExit(f"Missing data file: {DATA_FILE}. Run your training script (ml_models.py) first.")
    df = pd.read_csv(DATA_FILE, parse_dates=["signup_date", "last_interaction_date"], low_memory=False)
    for col, default in [
        ("customer_id", ""), ("company_name", ""),
        ("segment", "unknown"), ("churn_prob", 0.0),
        ("monetary", 0.0), ("product_diversity", 0),
        ("engagement_score", 0.0), ("recency_days", 9999)
    ]:
        if col not in df.columns:
            df[col] = default
    return df

# Load into global df for simplicity
df = load_dataframe()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/summary")
def api_summary():
    seg_counts = df["segment"].value_counts().to_dict()
    top_risk = df.sort_values("churn_prob", ascending=False).head(10)[
        ["customer_id", "company_name", "segment", "churn_prob", "last_interaction_date"]
    ].to_dict(orient="records")
    upsell = df[
        (df["segment"] == "high_value") & (df["churn_prob"] < 0.4) & (df["product_diversity"] <= 2)
    ].sort_values("monetary", ascending=False).head(10)[
        ["customer_id", "company_name", "monetary", "product_diversity", "churn_prob"]
    ].to_dict(orient="records")
    return jsonify({"segments": seg_counts, "top_risk": top_risk, "upsell": upsell})


@app.route("/api/segment/<segment>")
def api_segment(segment):
    seg = segment.lower()
    rows = df[df["segment"].str.lower() == seg].sort_values("churn_prob", ascending=False)
    if rows.empty:
        return jsonify({"error": f"No customers found for segment: {segment}"}), 404
    out = rows[
        ["customer_id", "company_name", "segment", "churn_prob", "monetary", "product_diversity", "engagement_score", "last_interaction_date"]
    ].head(200).to_dict(orient="records")
    return jsonify(out)


@app.route("/api/upsell")
def api_upsell():
    ups = df[
        (df["segment"] == "high_value") & (df["churn_prob"] < 0.4) & (df["product_diversity"] <= 2)
    ].sort_values("monetary", ascending=False).head(50)[
        ["customer_id", "company_name", "monetary", "product_diversity", "churn_prob"]
    ]
    arr = ups.to_dict(orient="records")
    for r in arr:
        r["recommendation"] = recommend_upsell(r)
    return jsonify(arr)


@app.route("/api/info")
def api_info():
    info = {
        "title": "AI-Powered CRM Insights - Hackathon Demo",
        "subtitle": "Quickly find at-risk accounts, upsell targets, and conversational insights.",
        "contact": {
            "name": "Parkavi. S",
            "email": "parkavisaravanan06@gmail.com"
        },
        "notes": [
            "Data shown is mock/simulated. Replace with real CRM export for production.",
            "Models: KMeans for segmentation, RandomForest for churn probability (demo).",
            "Designed to help sales teams prioritize high-risk accounts and identify upsell opportunities.",
            "Interactive dashboard allows filtering by region, account size, and risk category.",
            "Built with Python (Flask backend), JavaScript (frontend interactivity), and Bootstrap for responsive design.",
            "Future improvements: integrate real-time CRM data, advanced NLP for conversation insights, and predictive revenue forecasting."
        ],
        "features": [
            "At-risk account identification with churn probability visualization",
            "Upsell candidate recommendations based on customer segmentation",
            "Interactive pie charts, tables, and filters for easy data exploration",
            "Exportable insights for team reporting",
            "Clean and responsive UI suitable for desktop and mobile"
        ],
        "tech_stack": [
            "Python (Flask) - backend API and data processing",
            "JavaScript (D3.js/Chart.js) - interactive charts",
            "Bootstrap 5 - responsive design",
            "scikit-learn - machine learning models (KMeans, RandomForest)",
            "Pandas/Numpy - data manipulation"
        ]
    }
    return jsonify(info)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    payload = request.get_json() or {}
    query = payload.get("query", "")
    # handle_query returns (response_text, context)
    try:
        response_text, context = handle_query(query, df, payload.get("context"))
    except Exception:
        # Backward compatibility if handle_query returns just a string
        ans = handle_query(query, df)
        if isinstance(ans, tuple) and len(ans) >= 1:
            response_text = ans[0]
            context = ans[1] if len(ans) > 1 else {}
        else:
            response_text = str(ans)
            context = {}
    return jsonify({"answer": response_text, "context": context})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
