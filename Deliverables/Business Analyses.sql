-- Query 1: Departmental Mortality Risk Stratification (CTE + Aggregates)
WITH dept_summary AS (
    SELECT
        department,
        COUNT(*) AS total_admissions,
        COUNT(*) FILTER (WHERE is_mortality_case) AS total_deaths,
        ROUND(AVG(length_of_stay), 2) AS avg_los,
        ROUND(100.0 * COUNT(*) FILTER (WHERE is_mortality_case) / COUNT(*), 2) AS mortality_rate
    FROM fact_admissions
    GROUP BY department
)
SELECT *,
       CASE 
           WHEN mortality_rate > 15 THEN 'High Risk'
           WHEN mortality_rate BETWEEN 5 AND 15 THEN 'Moderate Risk'
           ELSE 'Low Risk'
       END AS risk_category
FROM dept_summary
ORDER BY mortality_rate DESC;

-- Query 2: Readmission Flagging using Window Function
SELECT *,
       CASE 
           WHEN admission_gap <= 30 THEN 'Readmission Within 30 Days'
           ELSE 'No Recent Readmission'
       END AS readmission_status
FROM (
    SELECT *,
           doa - LAG(dod) OVER (PARTITION BY mrd_no ORDER BY doa) AS admission_gap
    FROM fact_admissions
    WHERE mrd_no IS NOT NULL
) t
WHERE admission_gap IS NOT NULL;

-- Query 3: LOS Percentile Segmentation by Department
WITH los_cte AS (
    SELECT department, length_of_stay
    FROM fact_admissions
    WHERE length_of_stay IS NOT NULL
),
percentiles AS (
    SELECT department,
           PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY length_of_stay) AS p25,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY length_of_stay) AS p50,
           PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY length_of_stay) AS p75
    FROM los_cte
    GROUP BY department
)
SELECT l.department, l.length_of_stay,
       CASE
           WHEN l.length_of_stay <= p.p25 THEN 'Short Stay'
           WHEN l.length_of_stay <= p.p50 THEN 'Moderate Stay'
           WHEN l.length_of_stay <= p.p75 THEN 'Extended Stay'
           ELSE 'Long Stay'
       END AS los_category
FROM los_cte l
JOIN percentiles p ON l.department = p.department;

-- Query 4: Weekly Mortality Trend with Moving Averages
WITH base AS (
    SELECT admission_week,
           COUNT(*) AS total_admissions,
           COUNT(*) FILTER (WHERE is_mortality_case) AS deaths
    FROM fact_admissions
    GROUP BY admission_week
),
moving_avg AS (
    SELECT *,
           ROUND(AVG(deaths) OVER (ORDER BY admission_week ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS death_ma_3week
    FROM base
)
SELECT * FROM moving_avg ORDER BY admission_week;

-- Query 5: Age Bucket + Gender Cross Matrix with Mortality
SELECT age_bucket, gender,
       COUNT(*) AS total,
       SUM(CASE WHEN is_mortality_case THEN 1 ELSE 0 END) AS deaths,
       ROUND(100.0 * SUM(CASE WHEN is_mortality_case THEN 1 ELSE 0 END) / COUNT(*), 2) AS mortality_rate
FROM fact_admissions
GROUP BY age_bucket, gender
ORDER BY age_bucket, gender;

-- Query 6: Outlier Admissions Based on LOS (Statistical Threshold)
WITH stats AS (
    SELECT AVG(length_of_stay) AS mean_los,
           STDDEV_SAMP(length_of_stay) AS std_los
    FROM fact_admissions
)
SELECT f.*
FROM fact_admissions f, stats
WHERE f.length_of_stay > stats.mean_los + 2 * stats.std_los
ORDER BY f.length_of_stay DESC;

-- Query 7: Department-Wise Yearly Admissions Trend
SELECT department,
       EXTRACT(YEAR FROM doa) AS year,
       COUNT(*) AS admission_count
FROM fact_admissions
GROUP BY department, EXTRACT(YEAR FROM doa)
ORDER BY department, year;

-- Query 8: Cohort Mortality Tracking by First Admission Week
WITH first_adm AS (
    SELECT mrd_no, MIN(admission_week) AS first_week
    FROM fact_admissions
    GROUP BY mrd_no
),
cohort AS (
    SELECT f.*, fa.first_week
    FROM fact_admissions f
    JOIN first_adm fa ON f.mrd_no = fa.mrd_no
)
SELECT first_week,
       COUNT(*) AS total_cases,
       COUNT(*) FILTER (WHERE is_mortality_case) AS deaths,
       ROUND(100.0 * COUNT(*) FILTER (WHERE is_mortality_case) / COUNT(*), 2) AS mortality_rate
FROM cohort
GROUP BY first_week
ORDER BY first_week;

-- Query 9: Pollution Impact Simulation (Low vs High Week Segmentation)
WITH pollution_flags AS (
    SELECT admission_week,
           ROUND(AVG(pm25), 2) AS avg_pm25
    FROM fact_admissions
    WHERE pm25 IS NOT NULL
    GROUP BY admission_week
),
categorized AS (
    SELECT f.*, 
           CASE
               WHEN p.avg_pm25 > 100 THEN 'High Pollution'
               ELSE 'Normal Pollution'
           END AS pollution_flag
    FROM fact_admissions f
    JOIN pollution_flags p ON f.admission_week = p.admission_week
)
SELECT pollution_flag,
       COUNT(*) AS total_adm,
       ROUND(AVG(length_of_stay), 2) AS avg_los,
       ROUND(100.0 * SUM(CASE WHEN is_mortality_case THEN 1 ELSE 0 END) / COUNT(*), 2) AS mortality_rate
FROM categorized
GROUP BY pollution_flag;

-- Query 10: High Mortality Diagnosis Clusters (Min Threshold 20 Cases)
SELECT diagnosis,
       COUNT(*) AS total,
       COUNT(*) FILTER (WHERE is_mortality_case) AS deaths,
       ROUND(100.0 * COUNT(*) FILTER (WHERE is_mortality_case)/COUNT(*), 2) AS mortality_rate
FROM fact_admissions
GROUP BY diagnosis
HAVING COUNT(*) >= 20
ORDER BY mortality_rate DESC
LIMIT 10;

-- Query 11: Weekly LOS Distribution with Z-score Outlier Detection
WITH los_stats AS (
    SELECT admission_week,
           AVG(length_of_stay) AS mean_los,
           STDDEV_SAMP(length_of_stay) AS stddev_los
    FROM fact_admissions
    GROUP BY admission_week
),
flagged AS (
    SELECT f.*, s.mean_los, s.stddev_los,
           (f.length_of_stay - s.mean_los) / NULLIF(s.stddev_los, 0) AS z_score
    FROM fact_admissions f
    JOIN los_stats s ON f.admission_week = s.admission_week
)
SELECT * FROM flagged
WHERE z_score > 2
ORDER BY admission_week, z_score DESC;

-- Query 12: Admissions Falling into Bottom 10% of LOS by Department
WITH percentiles AS (
    SELECT department,
           PERCENTILE_CONT(0.1) WITHIN GROUP (ORDER BY length_of_stay) AS p10
    FROM fact_admissions
    GROUP BY department
)
SELECT f.*
FROM fact_admissions f
JOIN percentiles p ON f.department = p.department
WHERE f.length_of_stay <= p.p10
ORDER BY f.department, f.length_of_stay;

-- Query 13: Dynamic Risk Index (LOS + Mortality Flag) by Patient
SELECT mrd_no,
       COUNT(*) AS admission_count,
       SUM(length_of_stay) AS total_los,
       SUM(CASE WHEN is_mortality_case THEN 1 ELSE 0 END) AS mortality_events,
       ROUND(0.5 * SUM(length_of_stay) + 10 * SUM(CASE WHEN is_mortality_case THEN 1 ELSE 0 END), 2) AS risk_index
FROM fact_admissions
GROUP BY mrd_no
ORDER BY risk_index DESC
LIMIT 50;

-- Query 14: Department Ranking by Deaths per 1000 Patient-Days
SELECT department,
       COUNT(*) FILTER (WHERE is_mortality_case) AS total_deaths,
       SUM(length_of_stay) AS total_patient_days,
       ROUND(1000.0 * COUNT(*) FILTER (WHERE is_mortality_case) / NULLIF(SUM(length_of_stay), 0), 2) AS deaths_per_1000_days
FROM fact_admissions
GROUP BY department
ORDER BY deaths_per_1000_days DESC;

-- Query 15: Recovery Efficiency Score by Department
SELECT department,
       ROUND(AVG(CASE WHEN is_mortality_case THEN NULL ELSE length_of_stay END), 2) AS avg_recovery_los,
       ROUND(100.0 * COUNT(*) FILTER (WHERE NOT is_mortality_case) / COUNT(*), 2) AS discharge_rate,
       ROUND(100.0 * COUNT(*) FILTER (WHERE NOT is_mortality_case) / NULLIF(AVG(CASE WHEN is_mortality_case THEN NULL ELSE length_of_stay END), 0), 2) AS efficiency_score
FROM fact_admissions
GROUP BY department
ORDER BY efficiency_score DESC;

-- Query 16: Monthly Outbreak-like Surge Detector
WITH monthly_counts AS (
    SELECT DATE_TRUNC('month', doa) AS month,
           COUNT(*) AS admission_count
    FROM fact_admissions
    GROUP BY 1
),
outliers AS (
    SELECT *,
           ROUND(AVG(admission_count) OVER (), 2) AS overall_avg,
           ROUND(STDDEV_SAMP(admission_count) OVER (), 2) AS overall_std
    FROM monthly_counts
)
SELECT *, 
       CASE WHEN admission_count > overall_avg + 2 * overall_std THEN 'Surge Month' ELSE 'Normal' END AS surge_flag
FROM outliers
ORDER BY month;

-- Query 17: LOS and Mortality Flags by Age Bucket & Pollution Category
SELECT age_bucket, pollution_category,
       COUNT(*) AS total_adm,
       ROUND(AVG(length_of_stay), 2) AS avg_los,
       ROUND(100.0 * COUNT(*) FILTER (WHERE is_mortality_case) / COUNT(*), 2) AS mortality_rate
FROM fact_admissions
GROUP BY age_bucket, pollution_category
ORDER BY age_bucket, pollution_category;

-- Query 18: Forecasting Feature Input Table (Aggregated Time Series)
SELECT DATE_TRUNC('week', doa) AS week_start,
       COUNT(*) AS admissions,
       ROUND(AVG(length_of_stay), 2) AS avg_los,
       COUNT(*) FILTER (WHERE is_mortality_case) AS deaths,
       ROUND(100.0 * COUNT(*) FILTER (WHERE is_mortality_case)/COUNT(*), 2) AS mortality_rate
FROM fact_admissions
GROUP BY 1
ORDER BY 1;

-- Query 19: Patient-Level Event Timeline (With Dense Ranking)
SELECT mrd_no, doa, dod, department, is_mortality_case,
       DENSE_RANK() OVER (PARTITION BY mrd_no ORDER BY doa) AS admission_sequence
FROM fact_admissions
ORDER BY mrd_no, admission_sequence;

-- Query 20: High-Risk Elderly Patients (Multi-condition Filter)
SELECT *
FROM fact_admissions
WHERE age >= 70
  AND is_mortality_case = TRUE
  AND length_of_stay >= 10
  AND pollution_category = 'Severe'
ORDER BY length_of_stay DESC;

-- Query 21: Department-Wise Risk Clusters Based on LOS and Mortality
WITH base AS (
    SELECT department,
           ROUND(AVG(length_of_stay), 2) AS avg_los,
           ROUND(100.0 * SUM(CASE WHEN is_mortality_case THEN 1 ELSE 0 END)/COUNT(*), 2) AS mortality_rate
    FROM fact_admissions
    GROUP BY department
)
SELECT *,
       CASE
           WHEN avg_los > 10 AND mortality_rate > 10 THEN 'Critical'
           WHEN avg_los > 10 THEN 'High LOS'
           WHEN mortality_rate > 10 THEN 'High Mortality'
           ELSE 'Normal'
       END AS risk_cluster
FROM base
ORDER BY risk_cluster;

-- Query 22: Week-over-Week Departmental Volume Shifts
WITH dept_weeks AS (
    SELECT department, admission_week, COUNT(*) AS adm_count
    FROM fact_admissions
    GROUP BY department, admission_week
),
delta AS (
    SELECT *,
           adm_count - LAG(adm_count) OVER (PARTITION BY department ORDER BY admission_week) AS week_diff
    FROM dept_weeks
)
SELECT * FROM delta
WHERE week_diff IS NOT NULL
ORDER BY department, admission_week;

-- Query 23: Gender-Age Interaction Impact on Mortality (Normalized)
SELECT gender, age_bucket,
       COUNT(*) AS total,
       SUM(CASE WHEN is_mortality_case THEN 1 ELSE 0 END) AS deaths,
       ROUND(100.0 * SUM(CASE WHEN is_mortality_case THEN 1 ELSE 0 END)/COUNT(*), 2) AS mortality_rate,
       ROUND(SUM(CASE WHEN is_mortality_case THEN 1 ELSE 0 END) * 1.0 / SUM(SUM(CASE WHEN is_mortality_case THEN 1 ELSE 0 END)) OVER (), 4) AS contribution_pct
FROM fact_admissions
GROUP BY gender, age_bucket
ORDER BY mortality_rate DESC;

-- Query 24: Pollution-Driven LOS Shift (Multi-Year View)
SELECT EXTRACT(YEAR FROM doa) AS year,
       pollution_category,
       COUNT(*) AS total_cases,
       ROUND(AVG(length_of_stay), 2) AS avg_los
FROM fact_admissions
WHERE pollution_category IS NOT NULL
GROUP BY year, pollution_category
ORDER BY year, pollution_category;

-- Query 25: LOS Curve by Diagnosis Category (Filtered)
SELECT diagnosis,
       COUNT(*) AS total,
       ROUND(AVG(length_of_stay), 2) AS avg_los,
       ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY length_of_stay), 2) AS p90_los
FROM fact_admissions
WHERE diagnosis IS NOT NULL
GROUP BY diagnosis
HAVING COUNT(*) >= 20
ORDER BY p90_los DESC
LIMIT 15;

-- Query 26: Departmental Week Lag Between Admissions and Mortality Peaks
WITH weekly_stats AS (
    SELECT department, admission_week,
           COUNT(*) AS total,
           COUNT(*) FILTER (WHERE is_mortality_case) AS deaths
    FROM fact_admissions
    GROUP BY department, admission_week
),
ranked AS (
    SELECT *,
           RANK() OVER (PARTITION BY department ORDER BY total DESC) AS adm_peak,
           RANK() OVER (PARTITION BY department ORDER BY deaths DESC) AS death_peak
    FROM weekly_stats
)
SELECT department,
       MAX(CASE WHEN adm_peak = 1 THEN admission_week END) AS admission_peak_week,
       MAX(CASE WHEN death_peak = 1 THEN admission_week END) AS mortality_peak_week,
       (MAX(CASE WHEN death_peak = 1 THEN admission_week END) - MAX(CASE WHEN adm_peak = 1 THEN admission_week END)) AS lag_weeks
FROM ranked
GROUP BY department
ORDER BY lag_weeks DESC NULLS LAST;

-- Query 27: Patient Case Timeline Summary (LOS, Mortality, Readmission Flag)
WITH patient_summary AS (
    SELECT mrd_no,
           MIN(doa) AS first_adm,
           MAX(dod) AS last_disch,
           COUNT(*) AS admission_count,
           SUM(length_of_stay) AS total_stay,
           MAX(is_mortality_case::int) AS ever_died
    FROM fact_admissions
    GROUP BY mrd_no
)
SELECT *,
       CASE
           WHEN admission_count > 1 THEN 'Repeat Visitor'
           ELSE 'Single Admission'
       END AS visit_type
FROM patient_summary
ORDER BY total_stay DESC;

-- Query 28: Pollution-Adaptive Risk Banding by PM2.5 Levels
WITH pollution_bands AS (
    SELECT *,
           CASE
               WHEN pm25 >= 150 THEN 'Hazardous'
               WHEN pm25 >= 100 THEN 'Severe'
               WHEN pm25 >= 60 THEN 'High'
               ELSE 'Normal'
           END AS pm25_band
    FROM fact_admissions
    WHERE pm25 IS NOT NULL
)
SELECT pm25_band,
       COUNT(*) AS total_cases,
       ROUND(AVG(length_of_stay), 2) AS avg_los,
       ROUND(100.0 * SUM(CASE WHEN is_mortality_case THEN 1 ELSE 0 END)/COUNT(*), 2) AS mortality_rate
FROM pollution_bands
GROUP BY pm25_band
ORDER BY mortality_rate DESC;

-- Query 29: Department-Wise Median LOS with Interquartile Range
SELECT department,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY length_of_stay) AS median_los,
       PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY length_of_stay) -
       PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY length_of_stay) AS iqr
FROM fact_admissions
WHERE department IS NOT NULL
GROUP BY department
ORDER BY iqr DESC;

-- Query 30: Time to Mortality Distribution (First vs Final Admission)
WITH death_cases AS (
    SELECT mrd_no, MIN(doa) AS first_adm, MAX(dod) AS last_disch
    FROM fact_admissions
    WHERE is_mortality_case = TRUE
    GROUP BY mrd_no
),
timing AS (
    SELECT *,
           last_disch - first_adm AS time_to_death
    FROM death_cases
    WHERE last_disch IS NOT NULL AND first_adm IS NOT NULL
)
SELECT time_to_death,
       COUNT(*) AS case_count
FROM timing
GROUP BY time_to_death
ORDER BY time_to_death;

