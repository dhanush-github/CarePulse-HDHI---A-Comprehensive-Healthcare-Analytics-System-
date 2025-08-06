import pandas as pd
import numpy as np
from xgboost import XGBClassifier, XGBRegressor
from sklearn.model_selection import train_test_split

class CarePulseRiskEngine:
    def __init__(self, data_path):
        self.df = pd.read_csv(data_path)
        self.model_mortality = XGBClassifier(use_label_encoder=False, eval_metric='logloss', base_score=0.5)
        self.model_los = XGBRegressor()
        self.features = [
            'age', 'smoking', 'alcohol', 'dm', 'htn', 'cad', 'ckd',
            'hb', 'tlc', 'glucose', 'urea', 'creatinine', 'bnp'
        ]
        self.result_df = None

    def preprocess(self):
        df = self.df.copy()

        # Ensure outcome exists
        df['mortality_flag'] = np.where(df['outcome'].astype(str).str.upper() == 'DEATH', 1, 0)

        # Handle column naming
        if 'duration_of_stay' in df.columns:
            df = df.rename(columns={'duration_of_stay': 'length_of_stay'})
        elif 'length_of_stay' not in df.columns:
            raise ValueError("Missing duration_of_stay or length_of_stay column in input data.")

        # Drop rows with missing targets
        df = df.dropna(subset=['length_of_stay', 'mortality_flag'])

        # Coerce features to numeric
        for col in self.features:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Drop rows if key features are still missing after coercion
        df = df.dropna(subset=self.features)

        # Fill any remaining with medians
        df = df.fillna(df.median(numeric_only=True))

        self.df = df

    def train_models(self):
        X = self.df[self.features]
        y_mortality = self.df['mortality_flag']
        y_los = self.df['length_of_stay']

        X_train_m, _, y_train_m, _ = train_test_split(X, y_mortality, stratify=y_mortality, test_size=0.2, random_state=42)
        X_train_l, _, y_train_l, _ = train_test_split(X, y_los, test_size=0.2, random_state=42)

        self.model_mortality.fit(X_train_m, y_train_m)
        self.model_los.fit(X_train_l, y_train_l)

    def predict_and_flag_patients(self):
        X = self.df[self.features]
        self.df['predicted_mortality_prob'] = self.model_mortality.predict_proba(X)[:, 1]
        self.df['predicted_los'] = self.model_los.predict(X)

        # Flag based on mortality and LOS
        self.df['risk_flag'] = np.where(self.df['predicted_mortality_prob'] > 0.6, 'High Risk',
                                 np.where(self.df['predicted_mortality_prob'] > 0.4, 'Moderate Risk', 'Low Risk'))
        self.df['extended_stay_flag'] = np.where(self.df['predicted_los'] > 7, 'Likely Long Stay', 'Normal Stay')

        self.result_df = self.df[['mrd_no', 'age', 'gender', 'risk_flag', 'extended_stay_flag',
                                  'predicted_mortality_prob', 'predicted_los']]

        print("\n--- Sample Flagged Patients ---")
        print(self.result_df.head(10))

    def department_summary_flags(self):
        if 'department' not in self.df.columns:
            print("Department column not found for summary. Skipping department-level flagging.")
            return

        summary = self.df.groupby('department').agg(
            patients=('mrd_no', 'count'),
            avg_predicted_los=('predicted_los', 'mean'),
            high_risk_count=('risk_flag', lambda x: (x == 'High Risk').sum())
        ).reset_index()

        summary['dept_risk_level'] = np.where(summary['high_risk_count'] >= 10, 'Review',
                                      np.where(summary['high_risk_count'] >= 5, 'Monitor', 'Stable'))

        print("\n--- Department Risk Summary ---")
        print(summary.sort_values(by='high_risk_count', ascending=False))

    def run_all(self):
        print("Step 1: Preprocessing...")
        self.preprocess()
        print("Step 2: Training Models...")
        self.train_models()
        print("Step 3: Predicting & Flagging Patients...")
        self.predict_and_flag_patients()
        print("Step 4: Summarizing Departmental Risk...")
        self.department_summary_flags()


# ------------------------------
# Run the Script
# ------------------------------
if __name__ == "__main__":
    engine = CarePulseRiskEngine("master_hospital_data.csv")
    engine.run_all()
