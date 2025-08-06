-- View: vw_high_risk_admissions
CREATE OR REPLACE VIEW vw_high_risk_admissions AS
SELECT *
FROM fact_admissions
WHERE length_of_stay > 15 OR is_mortality_case = TRUE;

-- Function: fn_classify_risk
CREATE OR REPLACE FUNCTION fn_classify_risk(length_of_stay INT, is_mortality BOOLEAN)
RETURNS VARCHAR AS $$
BEGIN
    IF is_mortality THEN
        RETURN 'Critical';
    ELSIF length_of_stay >= 15 THEN
        RETURN 'High';
    ELSIF length_of_stay BETWEEN 7 AND 14 THEN
        RETURN 'Moderate';
    ELSE
        RETURN 'Low';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Table: monthly_admission_summary
CREATE TABLE IF NOT EXISTS monthly_admission_summary (
    summary_month DATE PRIMARY KEY,
    total_admissions INT,
    avg_los FLOAT,
    mortality_rate FLOAT
);

-- Procedure: sp_generate_monthly_summary
CREATE OR REPLACE PROCEDURE sp_generate_monthly_summary()
LANGUAGE SQL
AS $$
    INSERT INTO monthly_admission_summary (summary_month, total_admissions, avg_los, mortality_rate)
    SELECT
        DATE_TRUNC('month', doa) AS summary_month,
        COUNT(*) AS total_admissions,
        ROUND(AVG(length_of_stay), 2) AS avg_los,
        ROUND(100.0 * SUM(CASE WHEN is_mortality_case THEN 1 ELSE 0 END)/COUNT(*), 2) AS mortality_rate
    FROM fact_admissions
    GROUP BY summary_month;
$$;

-- Trigger Function: trg_check_los_outlier
CREATE OR REPLACE FUNCTION trg_check_los_outlier()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.length_of_stay > 30 THEN
        RAISE NOTICE 'Outlier Detected: LOS = % for patient %', NEW.length_of_stay, NEW.mrd_no;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: tg_flag_los_outlier
DROP TRIGGER IF EXISTS tg_flag_los_outlier ON fact_admissions;

CREATE TRIGGER tg_flag_los_outlier
BEFORE INSERT ON fact_admissions
FOR EACH ROW
EXECUTE FUNCTION trg_check_los_outlier();

-- Materialized View: mv_department_summary
CREATE MATERIALIZED VIEW mv_department_summary AS
SELECT
    department,
    COUNT(*) AS total_admissions,
    ROUND(AVG(length_of_stay), 2) AS avg_los,
    COUNT(*) FILTER (WHERE is_mortality_case) AS deaths,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_mortality_case)/COUNT(*), 2) AS mortality_rate
FROM fact_admissions
GROUP BY department;

-- Function: fn_department_efficiency
CREATE OR REPLACE FUNCTION fn_department_efficiency(dept TEXT)
RETURNS TABLE (
    department TEXT,
    avg_los FLOAT,
    mortality_rate FLOAT,
    efficiency_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        department,
        ROUND(AVG(length_of_stay), 2),
        ROUND(100.0 * SUM(CASE WHEN is_mortality_case THEN 1 ELSE 0 END)/COUNT(*), 2),
        ROUND((100.0 * SUM(CASE WHEN NOT is_mortality_case THEN 1 ELSE 0 END)) / NULLIF(AVG(length_of_stay), 0), 2)
    FROM fact_admissions
    WHERE department = dept
    GROUP BY department;
END;
$$ LANGUAGE plpgsql;

-- View: vw_weekly_mortality_ma
CREATE OR REPLACE VIEW vw_weekly_mortality_ma AS
WITH base AS (
    SELECT admission_week,
           COUNT(*) AS total_admissions,
           COUNT(*) FILTER (WHERE is_mortality_case) AS deaths
    FROM fact_admissions
    GROUP BY admission_week
),
moving_avg AS (
    SELECT *,
           ROUND(AVG(deaths) OVER (ORDER BY admission_week ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS death_ma
    FROM base
)
SELECT * FROM moving_avg;
