import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBClassifier, XGBRegressor
import warnings

warnings.filterwarnings("ignore")

class CarePulseModeling:
    def __init__(self, data_path):
        self.df = pd.read_csv(data_path)
        self.df_original = self.df.copy()
        self.preprocessed = False

    def preprocess_data(self):
        df = self.df.copy()

        # Create mortality flag (1 if DEATH, else 0)
        df['mortality_flag'] = np.where(df['outcome'].str.upper() == 'DEATH', 1, 0)

        # Drop rows with missing outcome or duration
        df = df.dropna(subset=['mortality_flag', 'duration_of_stay'])

        # Define usable columns based on available data
        features = [
            'age', 'gender', 'smoking', 'alcohol', 'dm', 'htn', 'cad', 'ckd',
            'hb', 'tlc', 'glucose', 'urea', 'creatinine', 'bnp'
        ]

        selected_columns = features + ['mortality_flag', 'duration_of_stay', 'mrd_no', 'outcome']
        df = df[[col for col in selected_columns if col in df.columns]]

        # Convert lab results to numeric
        lab_cols = ['hb', 'tlc', 'glucose', 'urea', 'creatinine', 'bnp']
        for col in lab_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df.dropna(inplace=True)

        if 'gender' in df.columns:
            le = LabelEncoder()
            df['gender'] = le.fit_transform(df['gender'])

        self.df = df
        self.preprocessed = True
        print("Preprocessing complete. Final shape:", df.shape)

    def train_mortality_model(self):
        if not self.preprocessed:
            self.preprocess_data()

        if self.df['mortality_flag'].nunique() < 2:
            print("\n[Warning] Mortality model not trained: only one class (0 or 1) found in target.")
            return

        X = self.df.drop(columns=['mortality_flag', 'duration_of_stay', 'mrd_no', 'outcome'])
        y = self.df['mortality_flag']

        X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)

        model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        print("\nMortality Model Evaluation:")
        print(confusion_matrix(y_test, y_pred))
        print(classification_report(y_test, y_pred))
        print("ROC AUC Score:", roc_auc_score(y_test, y_proba))

        self.df['predicted_mortality'] = model.predict(X)
        self.df['mortality_risk_score'] = model.predict_proba(X)[:, 1]
        self.df['mortality_risk_flag'] = np.where(self.df['mortality_risk_score'] > 0.5, 1, 0)

        self.mortality_model = model

    def train_los_model(self):
        if not self.preprocessed:
            self.preprocess_data()

        X = self.df.drop(columns=[
            'duration_of_stay', 'mortality_flag', 'mrd_no', 'outcome'
        ] + [col for col in ['predicted_mortality', 'mortality_risk_score', 'mortality_risk_flag'] if col in self.df.columns])
        
        y = self.df['duration_of_stay']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = XGBRegressor()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        print("\nLength of Stay (LOS) Model Evaluation:")
        print("MAE:", mean_absolute_error(y_test, y_pred))
        print("RMSE:", mean_squared_error(y_test, y_pred, squared=False))
        print("R2:", r2_score(y_test, y_pred))

        self.df['predicted_los'] = model.predict(X)
        self.df['los_risk_flag'] = np.where(self.df['predicted_los'] >= 5, 1, 0)

        self.los_model = model

    def export_predictions(self, filename="predicted_outcomes.csv"):
        output_cols = [
            'mrd_no', 'outcome', 'mortality_risk_score', 'mortality_risk_flag',
            'duration_of_stay', 'predicted_los', 'los_risk_flag'
        ]
        export_cols = [col for col in output_cols if col in self.df.columns]
        self.df[export_cols].to_csv(filename, index=False)
        print(f"\nPredictions exported to: {filename}")

    def run_full_pipeline(self):
        self.preprocess_data()
        self.train_mortality_model()
        self.train_los_model()
        self.export_predictions()


if __name__ == "__main__":
    model_runner = CarePulseModeling("master_hospital_data.csv")
    model_runner.run_full_pipeline()
