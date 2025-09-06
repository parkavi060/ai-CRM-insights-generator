# ml_models.py
import os, json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, silhouette_score

def find_input():
    candidates = ['data/mock_crm.csv', 'data/crm_data.csv', 'data/processed_customers.csv']
    for p in candidates:
        if os.path.exists(p):
            return p
    raise SystemExit("Put your mock CSV in data/mock_crm.csv or data/crm_data.csv")

def load_df(path):
    df = pd.read_csv(path, low_memory=False)
    # try to parse common date columns
    for col in ['signup_date','signup','last_interaction_date','last_interaction','last_contact','last_seen']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

def normalize_columns(df):
    # map common column names to our canonical names
    colmap = {}
    if 'total_spend' in df.columns: colmap['total_spend']='total_spend'
    elif 'purchase_history' in df.columns: colmap['purchase_history']='total_spend'
    elif 'purchase' in df.columns: colmap['purchase']='total_spend'

    if 'num_purchases' in df.columns: colmap['num_purchases']='num_purchases'
    elif 'frequency' in df.columns: colmap['frequency']='num_purchases'
    elif 'num_transactions' in df.columns: colmap['num_transactions']='num_purchases'

    if 'engagement_score' in df.columns: colmap['engagement_score']='engagement_score'
    elif 'engagement' in df.columns: colmap['engagement']='engagement_score'

    # rename where applicable
    for src, tgt in colmap.items():
        if src in df.columns:
            df[tgt] = df[src]

    # fill defaults for missing numeric columns
    for c in ['total_spend','num_purchases','engagement_score']:
        if c not in df.columns:
            df[c] = 0

    return df

def engineer_features(df):
    today = pd.to_datetime("2025-09-05")  # fixed for reproducibility
    # choose last interaction column
    last_cols = ['last_interaction_date','last_interaction','last_contact','last_seen']
    last_col = next((c for c in last_cols if c in df.columns), None)
    signup_cols = ['signup_date','signup']
    signup_col = next((c for c in signup_cols if c in df.columns), None)

    if last_col is None:
        df['last_interaction_date'] = pd.NaT
    else:
        df['last_interaction_date'] = pd.to_datetime(df[last_col], errors='coerce')

    if signup_col is None:
        df['signup_date'] = df['last_interaction_date'] - pd.to_timedelta(180, unit='d')
    else:
        df['signup_date'] = pd.to_datetime(df[signup_col], errors='coerce')

    df['recency_days'] = (today - df['last_interaction_date']).dt.days.fillna(9999).astype(int)
    df['tenure_days'] = (today - df['signup_date']).dt.days.fillna(0).astype(int)

    # product diversity if present
    if 'product_categories' in df.columns:
        def pd_len(x):
            try:
                if pd.isna(x): return 0
                if isinstance(x, str):
                    j=json.loads(x) if x.strip().startswith('[') else x.split(';')
                    return len(j)
                return len(x)
            except:
                return 0
        df['product_diversity'] = df['product_categories'].apply(pd_len)
    else:
        df['product_diversity'] = 1

    # ensure numeric
    df['monetary'] = pd.to_numeric(df.get('total_spend',0), errors='coerce').fillna(0)
    df['frequency'] = pd.to_numeric(df.get('num_purchases',0), errors='coerce').fillna(0)
    df['engagement_score'] = pd.to_numeric(df.get('engagement_score',0), errors='coerce').fillna(0)

    return df

def train_and_save(df):
    features = ['recency_days','frequency','monetary','engagement_score','product_diversity','tenure_days']
    X = df[features].fillna(0).values

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    os.makedirs('models', exist_ok=True)
    joblib.dump(scaler, 'models/scaler.pkl')

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    kmeans.fit(Xs)
    joblib.dump(kmeans, 'models/kmeans.pkl')
    df['cluster'] = kmeans.predict(Xs)

    # label clusters heuristically
    profile = df.groupby('cluster')[['monetary','recency_days','engagement_score']].mean()
    high_value_cluster = profile['monetary'].idxmax()
    at_risk_cluster = profile['recency_days'].idxmax()
    label_map = {c:('high_value' if c==high_value_cluster else ('at_risk' if c==at_risk_cluster else 'mid_value')) for c in profile.index}
    df['segment'] = df['cluster'].map(label_map)

    # churn label: use existing if present else synthetic
    if 'churn' in df.columns:
        df['churn_label'] = pd.to_numeric(df['churn'], errors='coerce').fillna(0).astype(int)
    else:
        df['churn_label'] = (((df['recency_days'] > 90) & (df['engagement_score'] < 0.35)) | ((df['frequency'] == 0) & (df['recency_days']>60))).astype(int)

    # train RF
    y = df['churn_label'].values
    if y.sum() == 0:
        print("Warning: no positive churn labels found. Synthetic labels used - treat model as demo-only.")
    X_train, X_test, y_train, y_test = train_test_split(Xs, y, test_size=0.2, random_state=42, stratify=y if y.sum()>0 else None)
    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
    rf.fit(X_train, y_train)
    joblib.dump(rf, 'models/rf_churn.pkl')

    # churn prob
    df['churn_prob'] = rf.predict_proba(Xs)[:,1]

    # diagnostics
    try:
        auc = roc_auc_score(y_test, rf.predict_proba(X_test)[:,1])
    except:
        auc = None
    sil = silhouette_score(Xs, df['cluster']) if len(np.unique(df['cluster']))>1 else None

    df.to_csv('data/processed_customers.csv', index=False)
    print("Saved models to models/ and processed data to data/processed_customers.csv")
    print("Diagnostics - ROC AUC (test):", auc, " Silhouette:", sil)

if __name__ == "__main__":
    path = find_input()
    df = load_df(path)
    df = normalize_columns(df)
    df = engineer_features(df)
    train_and_save(df)
