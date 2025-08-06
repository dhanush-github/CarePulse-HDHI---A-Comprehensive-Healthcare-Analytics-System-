import pandas as pd
import numpy as np

# Load datasets
admissions = pd.read_csv("/mnt/data/HDHI Admission data.csv")
mortality = pd.read_csv("/mnt/data/HDHI Mortality Data.csv")
pollution = pd.read_csv("/mnt/data/HDHI Pollution Data.csv")
table_meta = pd.read_csv("/mnt/data/table_headings.csv")

# --- 1. Clean column names ---
def clean_column_names(df):
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace(r"[^\w\s]", "", regex=True)
    return df

admissions = clean_column_names(admissions)
mortality = clean_column_names(mortality)
pollution = clean_column_names(pollution)

# --- 2. Convert dates ---
date_cols = ['admission_date', 'discharge_date', 'death_date', 'recorded_date']
for col in date_cols:
    if col in admissions.columns:
        admissions[col] = pd.to_datetime(admissions[col], errors='coerce')
    if col in mortality.columns:
        mortality[col] = pd.to_datetime(mortality[col], errors='coerce')
    if col in pollution.columns:
        pollution[col] = pd.to_datetime(pollution[col], errors='coerce')

# --- 3. Drop duplicates ---
admissions.drop_duplicates(inplace=True)
mortality.drop_duplicates(inplace=True)
pollution.drop_duplicates(inplace=True)

# --- 4. Feature Engineering on Admissions ---
if 'discharge_date' in admissions.columns and 'admission_date' in admissions.columns:
    admissions['length_of_stay'] = (admissions['discharge_date'] - admissions['admission_date']).dt.days

if 'admission_date' in admissions.columns:
    admissions['admission_week'] = admissions['admission_date'].dt.isocalendar().week

if 'age' in admissions.columns:
    bins = [0, 18, 40, 60, 80, 200]
    labels = ['0-18', '19-40', '41-60', '61-80', '80+']
    admissions['age_bucket'] = pd.cut(admissions['age'], bins=bins, labels=labels, right=False)

# --- 5. Merge Mortality ---
if 'patient_id' in admissions.columns and 'admission_date' in admissions.columns:
    merged = pd.merge(admissions, mortality[['patient_id', 'death_date']], 
                      on='patient_id', how='left', suffixes=('', '_death'))
    merged['is_mortality_case'] = ~merged['death_date'].isna()
else:
    merged = admissions.copy()

# --- 6. Merge Pollution Data ---
if 'admission_date' in merged.columns and 'recorded_date' in pollution.columns:
    pollution_daily = pollution.groupby('recorded_date').mean(numeric_only=True).reset_index()
    pollution_daily.columns = ['admission_date' if col == 'recorded_date' else col for col in pollution_daily.columns]
    merged = pd.merge(merged, pollution_daily, on='admission_date', how='left')

# --- 7. Clean Final Output ---
master_df = merged.copy()

import ace_tools as tools; tools.display_dataframe_to_user(name="Master Hospital Data Preview", dataframe=master_df)

# Save for future steps
master_df.to_csv("/mnt/data/master_hospital_data.csv", index=False)

# Descriptive summary of the master hospital data
summary = {}

# Basic info
summary['num_rows'] = master_df.shape[0]
summary['num_columns'] = master_df.shape[1]
summary['column_names'] = list(master_df.columns)

# Null value summary
nulls = master_df.isnull().sum()
null_percent = (nulls / master_df.shape[0]) * 100
null_summary = pd.DataFrame({'null_count': nulls, 'null_percent': null_percent})

# Data types
data_types = master_df.dtypes

# Descriptive statistics for numerical columns
numerical_summary = master_df.describe(include=[np.number]).T

# Categorical summary for object columns
categorical_summary = master_df.select_dtypes(include='object').describe().T

# Count of unique values per column
unique_counts = master_df.nunique()

# Mortality rate
if 'is_mortality_case' in master_df.columns:
    mortality_rate = master_df['is_mortality_case'].mean() * 100
else:
    mortality_rate = None

# Compile results into a dictionary
summary['data_types'] = data_types
summary['null_summary'] = null_summary
summary['numerical_summary'] = numerical_summary
summary['categorical_summary'] = categorical_summary
summary['unique_counts'] = unique_counts
summary['mortality_rate_percent'] = mortality_rate

# Display key components
import ace_tools as tools
tools.display_dataframe_to_user(name="Null Value Summary", dataframe=null_summary)
tools.display_dataframe_to_user(name="Numerical Summary", dataframe=numerical_summary)
tools.display_dataframe_to_user(name="Categorical Summary", dataframe=categorical_summary)

mortality_rate
