import pandas as pd
import shap
import lime
import lime.lime_tabular
import matplotlib.pyplot as plt
import numpy as np
import joblib
from xgboost import XGBClassifier, XGBRegressor

class CarePulseExplainability:
    def __init__(self, data_path, model_mortality, model_los):
        self.df = pd.read_csv(data_path)
        self.model_mortality = model_mortality
        self.model_los = model_los

        # Reuse same feature preprocessing logic
        self.feature_cols = [
            'age', 'gender', 'smoking', 'alcohol', 'dm', 'htn', 'cad', 'ckd',
            'hb', 'tlc', 'glucose', 'urea', 'creatinine', 'bnp'
        ]
        self.df = self.df[self.feature_cols + ['mortality_flag', 'duration_of_stay']].copy()
        self.df.dropna(inplace=True)
        if 'gender' in self.df.columns:
            self.df['gender'] = self.df['gender'].astype(str).map({'M': 1, 'F': 0}).fillna(0)

        self.X = self.df[self.feature_cols]

    def shap_summary_plots(self):
        print("Generating SHAP summary plots...")
        shap.initjs()

        # SHAP for Mortality Model
        explainer1 = shap.Explainer(self.model_mortality)
        shap_values1 = explainer1(self.X)

        plt.title("SHAP Summary - Mortality Model")
        shap.plots.beeswarm(shap_values1, show=False)
        plt.tight_layout()
        plt.savefig("shap_summary_mortality.png")
        plt.clf()

        # SHAP for LOS Model
        explainer2 = shap.Explainer(self.model_los)
        shap_values2 = explainer2(self.X)

        plt.title("SHAP Summary - LOS Model")
        shap.plots.beeswarm(shap_values2, show=False)
        plt.tight_layout()
        plt.savefig("shap_summary_los.png")
        plt.clf()

        print("SHAP plots saved: shap_summary_mortality.png, shap_summary_los.png")

    def shap_dependence_plot(self, feature_name="urea"):
        print(f"Generating SHAP dependence plot for '{feature_name}'...")
        explainer = shap.Explainer(self.model_mortality)
        shap_values = explainer(self.X)

        shap.plots.scatter(shap_values[:, feature_name], color=shap_values, show=False)
        plt.title(f"Dependence Plot – {feature_name}")
        plt.tight_layout()
        plt.savefig(f"shap_dependence_{feature_name}.png")
        plt.clf()

    def lime_explanation_mortality(self, row_id=5):
        print(f"\nRunning LIME for Mortality Model – Patient #{row_id}")
        explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data=self.X.values,
            feature_names=self.X.columns,
            class_names=['Survived', 'Died'],
            mode='classification'
        )

        exp = explainer.explain_instance(self.X.values[row_id], self.model_mortality.predict_proba, num_features=10)
        exp.save_to_file('lime_mortality.html')
        print("LIME explanation saved as: lime_mortality.html")

    def lime_explanation_los(self, row_id=10):
        print(f"\nRunning LIME for LOS Model – Patient #{row_id}")
        explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data=self.X.values,
            feature_names=self.X.columns,
            mode='regression'
        )

        exp = explainer.explain_instance(self.X.values[row_id], self.model_los.predict, num_features=10)
        exp.save_to_file('lime_los.html')
        print("LIME explanation saved as: lime_los.html")

    def run_full_explainability(self):
        self.shap_summary_plots()
        self.shap_dependence_plot(feature_name="urea")
        self.lime_explanation_mortality(row_id=5)
        self.lime_explanation_los(row_id=10)


if __name__ == "__main__":
    # Load trained models (if saved as joblib/pkl)
    # mortality_model = joblib.load("mortality_model.pkl")
    # los_model = joblib.load("los_model.pkl")

    # OR use freshly trained models directly (imported from script 3)
    from CarePulseModeling import CarePulseModeling  # Make sure script 3 is saved as CarePulseModeling.py

    model_obj = CarePulseModeling("master_hospital_data.csv")
    model_obj.run_full_pipeline()

    explainer = CarePulseExplainability(
        data_path="master_hospital_data.csv",
        model_mortality=model_obj.mortality_model,
        model_los=model_obj.los_model
    )

    explainer.run_full_explainability()