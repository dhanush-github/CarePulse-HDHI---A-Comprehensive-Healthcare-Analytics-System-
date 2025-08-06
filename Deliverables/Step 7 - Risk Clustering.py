import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings

warnings.filterwarnings("ignore")

class HospitalForecasting:
    def __init__(self, data_path):
        self.data = pd.read_csv(data_path, parse_dates=["admission_date"])
        self.monthly_df = None

    def preprocess(self):
        print("Preprocessing and aggregating monthly trends...")
        self.data['month'] = self.data['admission_date'].dt.to_period('M').dt.to_timestamp()
        self.monthly_df = self.data.groupby('month').agg({
            'mrd_no': 'count',
            'los': 'mean',
            'mortality_flag': 'sum'
        }).rename(columns={
            'mrd_no': 'monthly_admissions',
            'los': 'avg_los',
            'mortality_flag': 'monthly_mortality'
        }).reset_index()
        print(self.monthly_df.head())

    def plot_trends(self):
        print("Plotting monthly trends...")
        fig, axs = plt.subplots(3, 1, figsize=(12, 10))
        sns.lineplot(x='month', y='monthly_admissions', data=self.monthly_df, ax=axs[0])
        axs[0].set_title("Monthly Admissions")

        sns.lineplot(x='month', y='avg_los', data=self.monthly_df, ax=axs[1])
        axs[1].set_title("Average LOS per Month")

        sns.lineplot(x='month', y='monthly_mortality', data=self.monthly_df, ax=axs[2])
        axs[2].set_title("Monthly Mortality Count")

        plt.tight_layout()
        plt.show()

    def forecast_with_sarima(self, column):
        print(f"\n--- Forecasting {column} using SARIMA ---")
        ts = self.monthly_df.set_index('month')[column]

        model = SARIMAX(ts, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
        results = model.fit()

        forecast = results.get_forecast(steps=6)
        pred = forecast.predicted_mean
        ci = forecast.conf_int()

        plt.figure(figsize=(10, 4))
        plt.plot(ts, label='Observed')
        plt.plot(pred, label='Forecast', color='red')
        plt.fill_between(ci.index, ci.iloc[:, 0], ci.iloc[:, 1], color='pink', alpha=0.3)
        plt.title(f"6-Month Forecast for {column} (SARIMA)")
        plt.legend()
        plt.show()

    def forecast_with_prophet(self, column):
        print(f"\n--- Forecasting {column} using Facebook Prophet ---")
        prophet_df = self.monthly_df[['month', column]].rename(columns={'month': 'ds', column: 'y'})
        model = Prophet()
        model.fit(prophet_df)

        future = model.make_future_dataframe(periods=6, freq='M')
        forecast = model.predict(future)

        model.plot(forecast)
        plt.title(f"6-Month Forecast for {column} (Prophet)")
        plt.show()

    def evaluate(self, column):
        print(f"\nEvaluating model performance on {column} (Prophet)...")
        prophet_df = self.monthly_df[['month', column]].rename(columns={'month': 'ds', column: 'y'})
        model = Prophet()
        model.fit(prophet_df)

        future = model.make_future_dataframe(periods=6, freq='M')
        forecast = model.predict(future)

        actual = prophet_df['y'][-6:].values
        predicted = forecast['yhat'][-12:-6].values  # Compare with last 6 known

        mae = mean_absolute_error(actual, predicted)
        rmse = mean_squared_error(actual, predicted, squared=False)
        print(f"MAE: {mae:.2f} | RMSE: {rmse:.2f}")

    def run_all(self):
        self.preprocess()
        self.plot_trends()

        for column in ['monthly_admissions', 'avg_los', 'monthly_mortality']:
            self.forecast_with_sarima(column)
            self.forecast_with_prophet(column)
            self.evaluate(column)


if __name__ == "__main__":
    forecaster = HospitalForecasting("master_hospital_data.csv")
    forecaster.run_all()
