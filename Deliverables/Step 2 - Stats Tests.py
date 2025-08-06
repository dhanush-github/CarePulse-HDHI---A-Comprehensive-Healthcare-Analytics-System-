import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest
import warnings

warnings.filterwarnings("ignore")

class CarePulseStatTests:
    def __init__(self, data):
        self.df = data.copy()
        self.clean_data()

    def clean_data(self):
        numeric_cols = ['duration_of_stay', 'age', 'urea', 'creatinine', 'bnp', 'tlc', 'glucose', 'platelets']
        for col in numeric_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        self.df.dropna(subset=[
            'duration_of_stay', 'gender', 'age', 'htn', 'ckd', 'dm', 'outcome',
            'age_bucket', 'type_of_admissionemergencyopd'
        ], inplace=True)

    def run_all_tests(self):
        self.htn_vs_mortality()
        self.gender_vs_los_ttest()
        self.ckd_vs_los_ttest()
        self.anova_agebucket_los()
        self.admission_type_vs_mortality_chi2()
        self.los_correlation_with_age()
        # self.urea_creatinine_correlation()
        self.shapiro_los()
        self.shapiro_age()
        self.levene_variance_gender_los()
        self.ks_test_normality_los()
        self.mannwhitney_los_ckd()
        self.kruskal_los_age_bucket()
        self.proportion_test_smoking_outcome()
        self.dm_mortality_chi2()
        self.glucose_vs_outcome_ttest()
        self.platelets_anova_agebucket()
        self.outcome_vs_gender_chi2()
        self.bnp_correlation_los()
        self.los_diff_by_shock()
        self.icu_stay_ttest_by_outcome()
        self.af_vs_outcome_chi2()
        self.age_bucket_vs_ckd_chi2()
        self.hfref_vs_outcome_chi2()
        self.stemi_vs_outcome_chi2()

    def htn_vs_mortality(self):
        chi2, p, _, _ = stats.chi2_contingency(pd.crosstab(self.df['htn'], self.df['outcome']))
        print(f"1. HTN vs Mortality: Chi2 = {chi2:.2f}, p = {p:.4f}")

    def gender_vs_los_ttest(self):
        t, p = stats.ttest_ind(self.df[self.df['gender']=='M']['duration_of_stay'],
                               self.df[self.df['gender']=='F']['duration_of_stay'])
        print(f"2. LOS by Gender: T = {t:.2f}, p = {p:.4f}")

    def ckd_vs_los_ttest(self):
        t, p = stats.ttest_ind(self.df[self.df['ckd']==1]['duration_of_stay'],
                               self.df[self.df['ckd']==0]['duration_of_stay'])
        print(f"3. LOS by CKD: T = {t:.2f}, p = {p:.4f}")

    def anova_agebucket_los(self):
        groups = [g['duration_of_stay'] for _, g in self.df.groupby('age_bucket')]
        f, p = stats.f_oneway(*groups)
        print(f"4. LOS by Age Bucket (ANOVA): F = {f:.2f}, p = {p:.4f}")

    def admission_type_vs_mortality_chi2(self):
        chi2, p, _, _ = stats.chi2_contingency(pd.crosstab(self.df['type_of_admissionemergencyopd'], self.df['outcome']))
        print(f"5. Admission Type vs Mortality: Chi2 = {chi2:.2f}, p = {p:.4f}")

    def los_correlation_with_age(self):
        corr, p = stats.pearsonr(self.df['duration_of_stay'], self.df['age'])
        print(f"6. LOS vs Age (Pearson): r = {corr:.2f}, p = {p:.4f}")

    
    # def urea_creatinine_correlation(self):
    #     print("7. Urea vs Creatinine (Pearson):")
    #     df_valid = self.df[['urea', 'creatinine']].dropna()
    #     if len(df_valid) < 2:
    #         print("   Not enough data after removing NaNs.")
    #         return
    # corr, p = stats.pearsonr(df_valid['urea'], df_valid['creatinine'])
    # print(f"   Pearson correlation = {corr:.2f}, p-value = {p:.4f}")


    def shapiro_los(self):
        stat, p = stats.shapiro(self.df['duration_of_stay'].sample(min(500, len(self.df))))
        print(f"8. Normality Test for LOS (Shapiro): W = {stat:.3f}, p = {p:.4f}")

    def shapiro_age(self):
        stat, p = stats.shapiro(self.df['age'].sample(min(500, len(self.df))))
        print(f"9. Normality Test for Age (Shapiro): W = {stat:.3f}, p = {p:.4f}")

    def levene_variance_gender_los(self):
        stat, p = stats.levene(self.df[self.df['gender'] == 'M']['duration_of_stay'],
                               self.df[self.df['gender'] == 'F']['duration_of_stay'])
        print(f"10. Levene’s Test (LOS by Gender): stat = {stat:.2f}, p = {p:.4f}")

    def ks_test_normality_los(self):
        los = self.df['duration_of_stay'].dropna()
        standardized = (los - los.mean()) / los.std()
        stat, p = stats.kstest(standardized, 'norm')
        print(f"11. KS Test for LOS: stat = {stat:.2f}, p = {p:.4f}")

    def mannwhitney_los_ckd(self):
        stat, p = stats.mannwhitneyu(self.df[self.df['ckd']==1]['duration_of_stay'],
                                     self.df[self.df['ckd']==0]['duration_of_stay'])
        print(f"12. Mann-Whitney: LOS by CKD: U = {stat:.2f}, p = {p:.4f}")

    def kruskal_los_age_bucket(self):
        groups = [g['duration_of_stay'] for _, g in self.df.groupby('age_bucket')]
        stat, p = stats.kruskal(*groups)
        print(f"13. Kruskal-Wallis: LOS by Age Bucket: H = {stat:.2f}, p = {p:.4f}")

    def proportion_test_smoking_outcome(self):
        deaths = self.df[self.df['outcome'] == 'DEATH']
        alive = self.df[self.df['outcome'] != 'DEATH']
        count = np.array([deaths['smoking'].sum(), alive['smoking'].sum()])
        nobs = np.array([len(deaths), len(alive)])
        stat, p = proportions_ztest(count, nobs)
        print(f"14. Proportion Test: Smoking vs Mortality: Z = {stat:.2f}, p = {p:.4f}")

    def dm_mortality_chi2(self):
        chi2, p, _, _ = stats.chi2_contingency(pd.crosstab(self.df['dm'], self.df['outcome']))
        print(f"15. DM vs Mortality: Chi2 = {chi2:.2f}, p = {p:.4f}")

    def glucose_vs_outcome_ttest(self):
        t, p = stats.ttest_ind(self.df[self.df['outcome']=='DEATH']['glucose'].dropna(),
                               self.df[self.df['outcome']!='DEATH']['glucose'].dropna())
        print(f"16. Glucose vs Outcome: T = {t:.2f}, p = {p:.4f}")

    def platelets_anova_agebucket(self):
        groups = [pd.to_numeric(g['platelets'], errors='coerce').dropna() for _, g in self.df.groupby('age_bucket')]
        f, p = stats.f_oneway(*groups)
        print(f"17. Platelets by Age Bucket: F = {f:.2f}, p = {p:.4f}")

    def outcome_vs_gender_chi2(self):
        chi2, p, _, _ = stats.chi2_contingency(pd.crosstab(self.df['gender'], self.df['outcome']))
        print(f"18. Gender vs Outcome: Chi2 = {chi2:.2f}, p = {p:.4f}")

    def bnp_correlation_los(self):
        corr, p = stats.spearmanr(self.df['bnp'], self.df['duration_of_stay'])
        print(f"19. BNP vs LOS (Spearman): r = {corr:.2f}, p = {p:.4f}")

    def los_diff_by_shock(self):
        t, p = stats.ttest_ind(self.df[self.df['shock'] == 1]['duration_of_stay'],
                               self.df[self.df['shock'] == 0]['duration_of_stay'])
        print(f"20. LOS by Shock: T = {t:.2f}, p = {p:.4f}")

    def icu_stay_ttest_by_outcome(self):
        t, p = stats.ttest_ind(self.df[self.df['outcome'] == 'DEATH']['duration_of_intensive_unit_stay'],
                               self.df[self.df['outcome'] != 'DEATH']['duration_of_intensive_unit_stay'])
        print(f"21. ICU Stay vs Outcome: T = {t:.2f}, p = {p:.4f}")

    def af_vs_outcome_chi2(self):
        chi2, p, _, _ = stats.chi2_contingency(pd.crosstab(self.df['af'], self.df['outcome']))
        print(f"22. AF vs Outcome: Chi2 = {chi2:.2f}, p = {p:.4f}")

    def age_bucket_vs_ckd_chi2(self):
        chi2, p, _, _ = stats.chi2_contingency(pd.crosstab(self.df['age_bucket'], self.df['ckd']))
        print(f"23. Age Bucket vs CKD: Chi2 = {chi2:.2f}, p = {p:.4f}")

    def hfref_vs_outcome_chi2(self):
        chi2, p, _, _ = stats.chi2_contingency(pd.crosstab(self.df['hfref'], self.df['outcome']))
        print(f"24. HFREF vs Outcome: Chi2 = {chi2:.2f}, p = {p:.4f}")

    def stemi_vs_outcome_chi2(self):
        chi2, p, _, _ = stats.chi2_contingency(pd.crosstab(self.df['stemi'], self.df['outcome']))
        print(f"25. STEMI vs Outcome: Chi2 = {chi2:.2f}, p = {p:.4f}")


if __name__ == "__main__":
    df = pd.read_csv("master_hospital_data.csv")
    tester = CarePulseStatTests(df)
    tester.run_all_tests()

