from __future__ import annotations

from datetime import datetime, timedelta
import random

import numpy as np
import pandas as pd


random.seed(42)
np.random.seed(42)


REGIONS = [
    "Jharkhand", "West Bengal", "Bihar", "Odisha",
    "Maharashtra", "Uttar Pradesh", "Rajasthan",
    "Madhya Pradesh", "Gujarat", "Tamil Nadu",
    "Karnataka", "Andhra Pradesh", "Telangana",
    "Kerala", "Punjab", "Haryana", "Delhi",
    "Assam", "Chhattisgarh", "Uttarakhand",
    "Himachal Pradesh", "Jammu and Kashmir", "Goa",
    "Tripura", "Meghalaya", "Manipur", 
    "Nagaland", "Sikkim"
]

SCHEMES = ["Mudra", "PMEGP", "MSME", "Stand-Up India"]
CATEGORIES = ["Micro Enterprise", "Small Business", "Women-led", "Agri-linked"]
FIRST_NAMES = ["Aarav", "Diya", "Isha", "Rahul", "Pooja", "Arjun", "Neha", "Vikram", "Ananya", "Ravi"]
LAST_NAMES = ["Sharma", "Das", "Reddy", "Singh", "Patel", "Kumar", "Saha", "Yadav", "Jain", "Nair"]


def _amount_band(loan_amount: float) -> str:
    if loan_amount < 500_000:
        return "small"
    if loan_amount < 1_500_000:
        return "mid"
    return "large"


def build_regional_context() -> pd.DataFrame:
    # Read the directly configured state map
    return pd.read_csv("regional_context.csv")


BRANCH_MAPPING = {
    "Jharkhand": "Ranchi Main Branch",
    "West Bengal": "Kolkata Park Street Branch",
    "Bihar": "Patna Main Branch",
    "Odisha": "Bhubaneswar Rajpath Branch",
    "Maharashtra": "Mumbai Fort Branch",
    "Uttar Pradesh": "Lucknow Hazratganj Branch",
    "Rajasthan": "Jaipur MI Road Branch",
    "Madhya Pradesh": "Bhopal Arera Colony Branch",
    "Gujarat": "Ahmedabad Ashram Road Branch",
    "Tamil Nadu": "Chennai Anna Salai Branch",
    "Karnataka": "Bengaluru MG Road Branch",
    "Andhra Pradesh": "Vijayawada MG Road Branch",
    "Telangana": "Hyderabad Gachibowli Branch",
    "Kerala": "Kochi MG Road Branch",
    "Punjab": "Chandigarh Sector 17 Branch",
    "Haryana": "Gurugram Cyber City Branch",
    "Delhi": "Delhi Connaught Place Branch",
    "Assam": "Guwahati GS Road Branch",
    "Chhattisgarh": "Raipur GE Road Branch",
    "Uttarakhand": "Dehradun Rajpur Road Branch",
    "Himachal Pradesh": "Shimla Mall Road Branch",
    "Jammu and Kashmir": "Srinagar Residency Road Branch",
    "Goa": "Panaji Main Branch",
    "Tripura": "Agartala H.G.B. Road Branch",
    "Meghalaya": "Shillong Police Bazar Branch",
    "Manipur": "Imphal Main Branch",
    "Nagaland": "Kohima Main Branch",
    "Sikkim": "Gangtok MG Marg Branch"
}


def build_borrowers(regional_df: pd.DataFrame, n_borrowers: int = 420) -> pd.DataFrame:
    regional_lookup = regional_df.set_index("region").to_dict("index")
    borrowers = []

    for idx in range(n_borrowers):
        borrower_id = f"BORR_{idx + 1:05d}"
        region = random.choice(regional_df["region"].tolist())
        scheme = random.choices(SCHEMES, weights=[0.34, 0.18, 0.32, 0.16])[0]
        category = random.choice(CATEGORIES)
        loan_amount = float(np.random.choice([250_000, 400_000, 800_000, 1_200_000, 2_400_000, 4_000_000]))
        emi_amount = round(loan_amount * np.random.uniform(0.012, 0.025), 2)

        region_meta = regional_lookup[region]
        scheme_pressure = {"Mudra": 0.08, "PMEGP": 0.11, "MSME": 0.06, "Stand-Up India": 0.07}[scheme]
        latent_stress = min(0.96, max(0.08, region_meta["regional_stress_factor"] * 0.58 + scheme_pressure + np.random.uniform(-0.16, 0.18)))

        repayment_consistency = round(max(0.45, min(0.99, 1.02 - latent_stress * 0.48 + np.random.uniform(-0.05, 0.05))), 2)
        inflow_stability = round(max(0.38, min(0.98, 1.01 - latent_stress * 0.42 + np.random.uniform(-0.08, 0.05))), 2)
        balance_trend = round(np.random.uniform(-0.32, 0.18) - latent_stress * 0.18, 2)
        missed_payments = int(max(0, min(5, round(latent_stress * 4 + np.random.uniform(-1.0, 1.2)))))
        days_past_due = int(max(0, min(90, round(latent_stress * 65 + np.random.uniform(-12, 16)))))

        avg_monthly_inflow = round(emi_amount * np.random.uniform(1.2, 3.4) * (1.1 - latent_stress * 0.4), 2)
        avg_monthly_outflow = round(avg_monthly_inflow * np.random.uniform(0.72, 1.12), 2)
        current_balance = round(max(25_000, avg_monthly_inflow * np.random.uniform(0.6, 2.0)), 2)
        outstanding_ratio = min(0.96, max(0.24, 0.88 - repayment_consistency * 0.22 + latent_stress * 0.18))
        outstanding_amount = round(loan_amount * outstanding_ratio, 2)

        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        name = f"{first_name} {last_name}"
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(10,99)}@gmail.com"
        mobile_number = f"+91 {random.choice(['98', '99', '97', '96', '88', '89'])}{random.randint(10000000, 99999999)}"
        branch = BRANCH_MAPPING.get(region, f"{region} Main Branch")

        borrowers.append(
            {
                "borrower_id": borrower_id,
                "name": name,
                "email": email,
                "mobile_number": mobile_number,
                "branch": branch,
                "loan_scheme": scheme,
                "borrower_category": category,
                "region": region,
                "loan_amount": loan_amount,
                "amount_band": _amount_band(loan_amount),
                "emi_amount": emi_amount,
                "outstanding_amount": outstanding_amount,
                "current_balance": current_balance,
                "repayment_consistency": repayment_consistency,
                "inflow_stability": inflow_stability,
                "balance_trend": balance_trend,
                "missed_payments_90d": missed_payments,
                "days_past_due": days_past_due,
                "avg_monthly_inflow": avg_monthly_inflow,
                "avg_monthly_outflow": avg_monthly_outflow,
                "regional_stress_factor": region_meta["regional_stress_factor"],
                "peer_score": region_meta["peer_health_baseline"],
            }
        )

    return pd.DataFrame(borrowers)


def build_transactions(borrowers_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    start_date = datetime.now() - timedelta(days=180)

    for borrower in borrowers_df.itertuples(index=False):
        running_balance = borrower.current_balance
        for month in range(6):
            base_time = start_date + timedelta(days=month * 30 + random.randint(0, 4))

            inflow = max(15_000, borrower.avg_monthly_inflow * np.random.uniform(0.75, 1.25))
            running_balance += inflow
            rows.append(
                {
                    "transaction_id": f"TXN_{borrower.borrower_id}_{month:02d}_INFLOW",
                    "borrower_id": borrower.borrower_id,
                    "timestamp": base_time.isoformat(),
                    "transaction_type": "BUSINESS_INFLOW",
                    "amount": round(inflow, 2),
                    "status": "POSTED",
                    "balance_after": round(running_balance, 2),
                }
            )

            outflow = max(10_000, borrower.avg_monthly_outflow * np.random.uniform(0.7, 1.28))
            running_balance = max(0, running_balance - outflow)
            rows.append(
                {
                    "transaction_id": f"TXN_{borrower.borrower_id}_{month:02d}_OUTFLOW",
                    "borrower_id": borrower.borrower_id,
                    "timestamp": (base_time + timedelta(days=7)).isoformat(),
                    "transaction_type": "BUSINESS_OUTFLOW",
                    "amount": round(outflow, 2),
                    "status": "POSTED",
                    "balance_after": round(running_balance, 2),
                }
            )

            delay_bias = borrower.days_past_due / 90
            payment_status = random.choices(
                ["ON_TIME", "DELAYED", "MISSED"],
                weights=[
                    max(0.18, borrower.repayment_consistency),
                    0.22 + delay_bias * 0.4,
                    0.07 + delay_bias * 0.35,
                ],
            )[0]
            emi_paid = 0 if payment_status == "MISSED" else borrower.emi_amount * (1.0 if payment_status == "ON_TIME" else np.random.uniform(0.65, 0.95))
            running_balance = max(0, running_balance - emi_paid)
            rows.append(
                {
                    "transaction_id": f"TXN_{borrower.borrower_id}_{month:02d}_EMI",
                    "borrower_id": borrower.borrower_id,
                    "timestamp": (base_time + timedelta(days=25 + random.randint(0, 3))).isoformat(),
                    "transaction_type": "EMI_PAYMENT",
                    "amount": round(emi_paid, 2),
                    "status": payment_status,
                    "balance_after": round(running_balance, 2),
                }
            )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    # TODO: Re-import regional_context.csv to Supabase
    # Go to Supabase Table Editor → regional_context
    # Delete all rows → Import CSV → upload new file

    regional_df = build_regional_context()
    borrowers_df = build_borrowers(regional_df)
    transactions_df = build_transactions(borrowers_df)
    borrowers_df.to_csv("borrowers.csv", index=False)
    transactions_df.to_csv("loan_transactions.csv", index=False)

    print("✅ Bandhan demo data generated.")
    print(f"   Borrowers: {len(borrowers_df):,}")
    print(f"   Transactions: {len(transactions_df):,}")
    print(f"   Regions: {len(regional_df):,}")
