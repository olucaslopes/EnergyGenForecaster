from autogluon.timeseries import TimeSeriesPredictor, TimeSeriesDataFrame
from datetime import datetime, timedelta
import requests
import pandas as pd

# Define date ranges for historical irradiation data

today = datetime.today()
end_date = (datetime.today() - timedelta(days=8)).strftime('%Y-%m-%d')
start_date = (today - timedelta(days=365 * 20)).strftime('%Y-%m-%d')

# Load pre-trained time series model
model = TimeSeriesPredictor.load('models/autogluon-m4-monthly')


def predict_city_irradiation(df_):
    city = TimeSeriesDataFrame.from_data_frame(
        df_,
        id_column="ibge_code",
        timestamp_column="time"
    )
    return model.predict(city)


def get_ibge_code(lat, lon):
    url = f'https://servicodados.ibge.gov.br/api/v1/localidades/municipios?lat={lat}&lon={lon}'

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        codigo_ibge = data[0]['id']
        return codigo_ibge
    else:
        raise ValueError('Could not find ibge code for city')


def get_irradiation_data(lat, lon):
    url = (f'https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}'
           f'&start_date={start_date}&end_date={end_date}&daily=weathercode,shortwave_radiation_sum'
           '&timezone=America%2FSao_Paulo')

    response = requests.get(url)
    df = pd.DataFrame(response.json()['daily'])
    ibge_code = get_ibge_code(lat, lon)
    df['ibge_code'] = ibge_code
    return df

