###  A Comprehensive Healthcare Analytics System for Patient Outcomes and Environmental Risk at Hero DMC Heart Institute

---

## 📖 Project Overview

**CarePulse HDHI** is a real-world healthcare analytics project focused on **analyzing hospital admissions, mortality, patient risk profiles, and environmental pollution exposure** using data from **Hero DMC Heart Institute (HDHI)**. This project combines **clinical insights**, **environmental data**, and **predictive modeling** to uncover patterns in patient outcomes and hospital operations.

Unlike many analytics projects that rely on synthetic or simulated data, this initiative exclusively leverages **real hospital datasets**, making it more **authentic, impactful, and applicable** for real-world healthcare stakeholders.

---

## 🧩 Data Sources Used

All datasets were sourced from **internal HDHI records** and manually validated. No synthetic or dummy records were used.

- `HDHI Admission Data.csv` – Patient demographics, admission dates, diagnosis
- `HDHI Mortality Data.csv` – Mortality indicators and timestamps
- `HDHI Pollution Data.csv` – Environmental exposure factors (PM2.5, AQI)
- `table_headings.csv` – Metadata and schema reference

---

## 🛠️ Tech Stack & Tools

| Component          | Tools & Libraries |
|-------------------|-------------------|
| Data Cleaning      | Pandas, NumPy     |
| Statistical Tests  | Scipy, Statsmodels|
| Predictive Modeling| XGBoost, Sklearn  |
| Explainability     | SHAP, LIME        |
| Visualization      | Matplotlib, Seaborn, Plotly |
| Reporting & BI     | Power BI, DAX     |
| Documentation      | PowerPoint, PDF   |
| SQL Analysis       | PostgreSQL (CTEs, Views, Window Functions) |

---

## 🔍 Phase-Wise Execution Plan

### 🔹 **Phase 1: Data Cleaning & Integration**
- Cleaned inconsistent fields, standardized date formats
- Merged mortality & pollution data into the admission table
- Computed Length of Stay (LOS), age brackets, and flags

### 🔹 **Phase 2: SQL-Based Descriptive & Diagnostic Analysis**
- Created advanced queries using CTEs, window functions, groupings
- Focused on trends in mortality, admission peaks, high-risk departments

### 🔹 **Phase 3: Python-Based Analytics Pipeline**
Scripts developed using class-based architecture:
1. `1_EDA.py` – Generated 25+ plots exploring seasonality, age-wise risk, pollution impact
2. `2_Statistical_Tests.py` – 25 statistical tests (5+ hypothesis tests)
3. `3_Predictive_Modeling.py` – XGBoost model predicting mortality probability
4. `4_Model_Explainability.py` – SHAP + LIME plots for interpretability
5. `5_Risk_Flagging.py` – Classified patients by:
   - Mortality risk (High, Medium, Low)
   - Extended stay likelihood (Likely, Unlikely)

### 🔹 **Phase 4: Power BI Dashboard**
- Built 4 interactive report pages:
  1. Overview KPIs and slicers
  2. Pollution vs Outcomes
  3. Mortality Trends & LOS by Demographics
  4. Predictive Risk Flagging Visualizations

### 🔹 **Phase 5: Documentation**
- `Executive_Summary.pdf`: White-paper style documentation with insights
- `Executive_Deck.pptx`: McKinsey-style deck for C-suite storytelling

---

## 📈 Key Findings

1. **Age & Mortality:** Mortality rate rises significantly for patients above 70.
2. **Pollution Impact:** High PM2.5 levels correlate with increased admissions.
3. **Seasonality:** Winter months saw a 15–20% spike in heart-related cases.
4. **Gender Patterns:** Males had slightly higher average LOS compared to females.
5. **Risk Flagging:** XGBoost model flagged high-risk patients with ~94% accuracy.
6. **SHAP Insights:** Top predictors include age, diagnosis type, pollution exposure.

---

## 🧠 Business & Clinical Impact

| Impact Area                 | Description |
|----------------------------|-------------|
| Patient Risk Profiling     | Enables preemptive care for high-risk patients |
| Resource Optimization      | Flags potential long-stay patients for early planning |
| Environmental Alert System | Identifies critical pollution thresholds for alerts |
| Policy Formulation         | Insights for hospital administrators on strategic interventions |
| Transparency & Trust       | Builds explainable AI models (SHAP + LIME) for auditability |

---

