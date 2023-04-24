from autogluon.timeseries import TimeSeriesPredictor, TimeSeriesDataFrame
from datetime import datetime, timedelta, date
import requests
import pandas as pd
import os

# Define date ranges for historical irradiation data

today = datetime.today()
if today.day > 9:
    # last_day_of_last_month
    end_date = date(today.year, today.month, 1) - timedelta(days=1)
else:
    # last day of last 2nd month
    last_month = date(today.year, today.month, 1) - timedelta(days=1)
    end_date = date(last_month.year, last_month.month, 1) - timedelta(days=1)

start_date = (today - timedelta(days=365 * 20)).strftime('%Y-%m-%d')

# Load pre-trained time series model
full_path = os.path.abspath("./autogluon-m4-monthly")
model = TimeSeriesPredictor.load(full_path)

def predict_city_irradiation(df_):
    city = TimeSeriesDataFrame.from_data_frame(
        df_,
        id_column="ibge_code",
        timestamp_column="time"
    )

    return model.predict(city, model='AutoGluonTabular').reset_index()


def get_ibge_code(lat, lon):
    url = f'http://servicodados.ibge.gov.br/api/v1/localidades/municipios?lat={lat}&lon={lon}'

    response = requests.get(url, verify=False)

    if response.status_code == 200:
        data = response.json()
        codigo_ibge = data[0]['id']
        return codigo_ibge
    else:
        raise ValueError('Could not find ibge code for city')


def get_historical_data(lat, lon):
    url = (f'https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}'
           f'&start_date={start_date}&end_date={end_date}&daily=weathercode,shortwave_radiation_sum'
           '&timezone=America%2FSao_Paulo')

    response = requests.get(url)
    df = pd.DataFrame(response.json()['daily'])
    ibge_code = get_ibge_code(lat, lon)
    df = df.assign(ibge_code=ibge_code, time=pd.to_datetime(df['time'], format='%Y-%m-%d'))
    return df


def get_irrad_data(lat, lon):
    irrad_past = get_historical_data(lat, lon)

    monthly_irrad_past = irrad_past.groupby(
        ['ibge_code', pd.Grouper(key='time', freq='M')]
    )['shortwave_radiation_sum'].sum().to_frame().reset_index()

    irrad_pred = predict_city_irradiation(monthly_irrad_past)[['timestamp', 'mean']]

    irrad_pred = irrad_pred.rename(
        columns={'timestamp': 'time', 'mean': 'shortwave_radiation_sum'}
    ).assign(type='predicted')

    irrad_past = monthly_irrad_past[['time', 'shortwave_radiation_sum']].assign(type='actual')

    return pd.concat([irrad_past, irrad_pred])
