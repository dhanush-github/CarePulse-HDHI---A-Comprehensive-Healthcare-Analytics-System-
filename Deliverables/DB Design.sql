-- --------------------------------------------------------
-- CarePulse HDHI: MASTER DATA INGESTION SCRIPT (PUBLIC SCHEMA)
-- --------------------------------------------------------

-- STEP 0: CLEAN RESET
-- Drop in dependency-safe order
DROP TABLE IF EXISTS fact_admissions;
DROP TABLE IF EXISTS dim_patient CASCADE;
DROP TABLE IF EXISTS dim_department CASCADE;
DROP TABLE IF EXISTS dim_pollution CASCADE;
DROP TABLE IF EXISTS stg_master_hospital_data;

-- --------------------------------------------------------------------------
-- STEP 1: CREATE STAGING TABLE (Including all colums in master table)
-- --------------------------------------------------------------------------

CREATE TABLE stg_master_hospital_data (
    sno INT,
    mrd_no VARCHAR(255),
    doa DATE,
    dod DATE,
    age INT,
    gender VARCHAR(255),
    rural VARCHAR(255),
    type_of_admissionemergencyopd VARCHAR(255),
    month_year VARCHAR(255),
    duration_of_stay INT,
    duration_of_intensive_unit_stay INT,
    outcome VARCHAR(255),
    smoking INT,
    alcohol INT,
    dm INT,
    htn INT,
    cad INT,
    prior_cmp INT,
    ckd INT,
    hb VARCHAR(255),
    tlc VARCHAR(255),
    platelets VARCHAR(255),
    glucose VARCHAR(255),
    urea VARCHAR(255),
    creatinine VARCHAR(255),
    bnp VARCHAR(255),
    raised_cardiac_enzymes INT,
    ef VARCHAR(255),
    severe_anaemia INT,
    anaemia INT,
    stable_angina INT,
    acs INT,
    stemi INT,
    atypical_chest_pain INT,
    heart_failure INT,
    hfref INT,
    hfnef INT,
    valvular INT,
    chb INT,
    sss INT,
    aki INT,
    cva_infract INT,
    cva_bleed INT,
    af INT,
    vt INT,
    psvt INT,
    congenital INT,
    uti INT,
    neuro_cardiogenic_syncope INT,
    orthostatic INT,
    infective_endocarditis INT,
    dvt INT,
    cardiogenic_shock INT,
    shock INT,
    pulmonary_embolism INT,
    chest_infection VARCHAR(255),
    age_bucket VARCHAR(255)
);

-- At this point, use pgAdmin GUI to import data from path.

-- --------------------------------------------------------
-- STEP 2: DIMENSION TABLES
-- --------------------------------------------------------

CREATE TABLE dim_patient (
    mrd_no VARCHAR(20) PRIMARY KEY,
    age INT,
    gender VARCHAR(10)
);

CREATE TABLE dim_department (
    department VARCHAR(100) PRIMARY KEY,
    specialty VARCHAR(100)  -- Optional
);

CREATE TABLE dim_pollution (
    recorded_date DATE PRIMARY KEY,
    pm25 FLOAT,
    pm10 FLOAT,
    no2 FLOAT,
    so2 FLOAT,
    pollution_category VARCHAR(20)
);

-- --------------------------------------------------------
-- STEP 3: FACT TABLE
-- --------------------------------------------------------

CREATE TABLE fact_admissions (
    admission_id SERIAL PRIMARY KEY,
    mrd_no VARCHAR(20),
    doa DATE,
    dod DATE,
    age INT,
    age_bucket VARCHAR(10),
    gender VARCHAR(10),
    department VARCHAR(100),
    diagnosis TEXT,
    length_of_stay INT,
    admission_week INT,
    is_mortality_case BOOLEAN,
    pm25 FLOAT,
    pm10 FLOAT,
    no2 FLOAT,
    so2 FLOAT,
    pollution_category VARCHAR(20),

    CONSTRAINT fk_patient FOREIGN KEY (mrd_no) REFERENCES dim_patient(mrd_no),
    CONSTRAINT fk_department FOREIGN KEY (department) REFERENCES dim_department(department)
);

-- --------------------------------------------------------
-- STEP 4: POPULATE DIMENSIONS
-- --------------------------------------------------------
-- Insert into dim_patient with conflict handling
INSERT INTO dim_patient (mrd_no, age, gender)
SELECT DISTINCT 
    mrd_no::VARCHAR(20),
    age::INT,
    gender::VARCHAR(10)
FROM stg_master_hospital_data
WHERE mrd_no IS NOT NULL
ON CONFLICT (mrd_no) DO NOTHING;

-- Insert into dim_department with conflict handling
INSERT INTO dim_department (department)
SELECT DISTINCT 
    type_of_admissionemergencyopd::VARCHAR(100)
FROM stg_master_hospital_data
WHERE type_of_admissionemergencyopd IS NOT NULL
ON CONFLICT (department) DO NOTHING;

-- Insert into dim_pollution (dummy data for now)
INSERT INTO dim_pollution (recorded_date, pm25, pm10, no2, so2, pollution_category)
SELECT DISTINCT 
    doa::DATE,
    NULL::FLOAT,
    NULL::FLOAT,
    NULL::FLOAT,
    NULL::FLOAT,
    'Unknown'::VARCHAR(20)
FROM stg_master_hospital_data
WHERE doa IS NOT NULL
ON CONFLICT (recorded_date) DO NOTHING;



-- --------------------------------------------------------
-- STEP 5: POPULATE FACT TABLE
-- --------------------------------------------------------

INSERT INTO fact_admissions (
    mrd_no, doa, dod, age, age_bucket, gender, department, diagnosis,
    length_of_stay, admission_week, is_mortality_case,
    pm25, pm10, no2, so2, pollution_category
)
SELECT
    mrd_no::VARCHAR(20),
    doa::DATE,
    dod::DATE,
    age::INT,
    age_bucket::VARCHAR(10),
    gender::VARCHAR(10),
    type_of_admissionemergencyopd::VARCHAR(100),
    outcome::TEXT,
    duration_of_stay::INT,
    EXTRACT(WEEK FROM doa::DATE)::INT,
    CASE WHEN LOWER(outcome) LIKE '%death%' THEN TRUE ELSE FALSE END,
    NULL::FLOAT, NULL::FLOAT, NULL::FLOAT, NULL::FLOAT,
    'Unknown'::VARCHAR(20)
FROM stg_master_hospital_data
WHERE mrd_no IS NOT NULL AND doa IS NOT NULL;


SELECT * FROM dim_pollution;

