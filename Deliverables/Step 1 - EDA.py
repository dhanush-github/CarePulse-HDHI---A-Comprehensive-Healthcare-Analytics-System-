import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import warnings

warnings.filterwarnings("ignore")
sns.set(style="whitegrid")

class HDHIEDAAdvanced:
    def __init__(self, data):
        self.df = data.copy()
        self.df['duration_of_stay'] = pd.to_numeric(self.df['duration_of_stay'], errors='coerce')

    def run_all(self):
        self.basic_overview()
        self.visualize_age_distribution()
        self.visualize_gender_distribution()
        self.los_distribution()
        self.kde_los_by_outcome()
        self.age_vs_los_boxplot()
        self.correlation_heatmap()
        self.admission_type_distribution()
        self.outcome_distribution()
        self.readmission_frequency()

    def basic_overview(self):
        print("\n Basic Info:")
        print(self.df.info())
        print("\n Nulls Summary:\n", self.df.isnull().sum().sort_values(ascending=False).head(10))
        print("\n Duplicates:", self.df.duplicated().sum())

    def visualize_age_distribution(self):
        plt.figure(figsize=(8, 4))
        sns.histplot(self.df['age'], bins=30, kde=True)
        plt.title("Age Distribution")
        plt.tight_layout()
        plt.show()

    def visualize_gender_distribution(self):
        sns.countplot(x='gender', data=self.df)
        plt.title("Gender Distribution")
        plt.tight_layout()
        plt.show()

    def los_distribution(self):
        plt.figure(figsize=(8, 4))
        sns.histplot(self.df['duration_of_stay'].dropna(), bins=30, kde=True)
        plt.title("Length of Stay Distribution")
        plt.tight_layout()
        plt.show()

    def kde_los_by_outcome(self):
        plt.figure(figsize=(8, 4))
        sns.kdeplot(data=self.df.dropna(subset=['duration_of_stay']), x='duration_of_stay', hue='outcome', fill=True)
        plt.title("LOS by Outcome (KDE)")
        plt.tight_layout()
        plt.show()

    def age_vs_los_boxplot(self):
        plt.figure(figsize=(10, 5))
        sns.boxplot(x='age_bucket', y='duration_of_stay', data=self.df)
        plt.title("LOS Across Age Buckets")
        plt.tight_layout()
        plt.show()

    def correlation_heatmap(self):
        numeric_cols = self.df.select_dtypes(include=['int64', 'float64']).drop(columns=['sno'], errors='ignore')
        plt.figure(figsize=(12, 8))
        sns.heatmap(numeric_cols.corr(), cmap='coolwarm', annot=False)
        plt.title("Correlation Heatmap")
        plt.tight_layout()
        plt.show()

    def admission_type_distribution(self):
        sns.countplot(x='type_of_admissionemergencyopd', data=self.df)
        plt.title("Admission Type Distribution")
        plt.tight_layout()
        plt.show()

    def outcome_distribution(self):
        sns.countplot(x='outcome', data=self.df)
        plt.title("Patient Outcome Distribution")
        plt.tight_layout()
        plt.show()

    def readmission_frequency(self):
        readmits = self.df['mrd_no'].value_counts()
        print("\n Patients with multiple admissions:")
        print(readmits[readmits > 1])

if __name__ == "__main__":
    df = pd.read_csv("master_hospital_data.csv")
    eda = HDHIEDAAdvanced(df)
    eda.run_all()
