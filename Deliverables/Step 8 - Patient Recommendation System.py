# Filename: 8_Patient_Recommendation_System.py

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings("ignore")

class PatientRecommender:
    def __init__(self, data_path):
        self.raw_data = pd.read_csv(data_path)
        self.df = None
        self.features = None
        self.similarity_matrix = None

    def preprocess(self):
        print("🔹 Preprocessing for recommendation system...")
        df = self.raw_data.copy()

        # Encode categorical variables
        df['gender'] = df['gender'].map({'M': 0, 'F': 1})

        # Drop rows with missing values in core columns
        df = df.dropna(subset=[
            'age', 'gender', 'los',
            'pollution_pm25', 'pollution_no2', 'pollution_o3'
        ])

        # Define feature vector for similarity
        self.features = [
            'age', 'gender', 'los',
            'pollution_pm25', 'pollution_no2', 'pollution_o3'
        ]

        # Normalize
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(df[self.features])

        self.df = df.reset_index(drop=True)
        self.df[self.features] = scaled_features
        print("Data is normalized and ready.")

    def compute_similarity(self):
        print("🔹 Computing patient similarity matrix...")
        self.similarity_matrix = cosine_similarity(self.df[self.features])
        print("✅ Similarity matrix created.")

    def recommend_similar_patients(self, mrd_no, top_n=5):
        print(f"\n🔍 Fetching top {top_n} similar patients for MRD No: {mrd_no}...")

        try:
            idx = self.df[self.df['mrd_no'] == mrd_no].index[0]
        except IndexError:
            print("❌ MRD not found in dataset.")
            return

        sim_scores = list(enumerate(self.similarity_matrix[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

        # Exclude the patient itself
        sim_scores = [score for score in sim_scores if score[0] != idx][:top_n]

        recommended = self.df.iloc[[i[0] for i in sim_scores]]
        print(recommended[['mrd_no', 'age', 'los', 'pollution_pm25', 'mortality_flag']])
        return recommended

    def suggest_interventions(self, patient_row):
        print(f"\n💡 Suggestions for MRD: {patient_row['mrd_no']}")

        suggestions = []

        if patient_row['pollution_pm25'] > 1.5:
            suggestions.append("Air purifier recommended / transfer to cleaner ward")

        if patient_row['los'] > 10:
            suggestions.append("Flag for long-stay review and infection monitoring")

        if patient_row['age'] > 65:
            suggestions.append("Geriatric support plan initiation")

        if patient_row['mortality_flag'] == 1:
            suggestions.append("Retrospective review for critical event prevention")

        if not suggestions:
            suggestions.append("Maintain standard monitoring and care")

        for s in suggestions:
            print(f"- {s}")

    def run_recommender_for_patient(self, mrd_no):
        self.preprocess()
        self.compute_similarity()
        similar_patients = self.recommend_similar_patients(mrd_no)

        if similar_patients is not None:
            for _, row in similar_patients.iterrows():
                self.suggest_interventions(row)


if __name__ == "__main__":
    recommender = PatientRecommender("Data/master_hospital_data.csv")
    recommender.run_recommender_for_patient(mrd_no=234882)  # Replace with actual MRD number
