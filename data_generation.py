import pandas as pd
import random
import faker

# initialize faker for generating company names, industries, dates
fake = faker.Faker()

# sample industries
industries = ["IT", "Finance", "Healthcare", "Manufacturing", "Retail", "Education"]

# number of customers you want
n_customers = 500

data = []
for i in range(1, n_customers + 1):
    company_name = fake.company()
    industry = random.choice(industries)
    purchase_history = random.randint(1000, 20000)   # total spent
    engagement_score = random.randint(0, 100)        # engagement score out of 100
    last_interaction_date = fake.date_between(start_date="-6M", end_date="today")
    churn = random.choice([0, 1])                    # 0 = active, 1 = churn
    
    data.append([i, company_name, industry, purchase_history, 
                 engagement_score, last_interaction_date, churn])

# create dataframe
df = pd.DataFrame(data, columns=[
    "customer_id", "company_name", "industry", "purchase_history", 
    "engagement_score", "last_interaction_date", "churn"
])

# save to CSV
df.to_csv("data/crm_data.csv", index=False)

print("✅ Mock CRM data generated successfully in data/crm_data.csv")
