from autogluon.timeseries import TimeSeriesPredictor, TimeSeriesDataFrame
from datetime import datetime, timedelta, date
import requests
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.location import Location
import pandas as pd
import os

# Define constants for readability
LAST_DAY_OF_MONTH = 9
YEARS_OF_HISTORICAL_DATA = 20

# Define date ranges for historical irradiation data
today = datetime.today()
if today.day > LAST_DAY_OF_MONTH:
    end_date = date(today.year, today.month, 1) - timedelta(days=1)
else:
    last_month = date(today.year, today.month, 1) - timedelta(days=1)
    end_date = date(last_month.year, last_month.month, 1) - timedelta(days=1)

start_date = (today - timedelta(days=365 * YEARS_OF_HISTORICAL_DATA)).strftime('%Y-%m-%d')

# Load pre-trained time series model
MODEL_PATH = os.path.abspath("./autogluon-m4-monthly")
model = TimeSeriesPredictor.load(MODEL_PATH)

# Initialize geolocator and rate limiter
geolocator = Nominatim(user_agent="draw2text2", timeout=2)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


def predict_city_irradiation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Predict the shortwave radiation sum for a city using a pre-trained time series model.

    Args:
        df (pandas.DataFrame): A pandas DataFrame containing historical shortwave radiation sum data.

    Returns:
        pandas.DataFrame: A pandas DataFrame containing the predicted shortwave radiation sum for the given city.
    """
    # Convert input DataFrame to TimeSeriesDataFrame
    city = TimeSeriesDataFrame.from_data_frame(
        df,
        id_column="ibge_code",
        timestamp_column="time"
    )

    # Use pre-trained model to make predictions
    return model.predict(city, model='AutoGluonTabular').reset_index()


def get_ibge_code(lat: float, lon: float) -> str:
    """
    Get the IBGE code for the municipality located at the given latitude and longitude.

    Args:
        lat (float): The latitude of the municipality.
        lon (float): The longitude of the municipality.

    Returns:
        str: The IBGE code of the municipality as a string.
    """
    # Use IBGE API to get municipality data based on lat/long
    url = f'http://servicodados.ibge.gov.br/api/v1/localidades/municipios?lat={lat}&lon={lon}'
    response = requests.get(url, verify=False)

    if response.status_code == 200:
        # Parse JSON response to get IBGE code
        data = response.json()
        codigo_ibge = data[0]['id']
        return codigo_ibge
    else:
        raise ValueError('Could not find ibge code for city')


def get_historical_data(lat: float, lon: float) -> pd.DataFrame:
    """
    Get historical irradiation data for a given location.

    Args:
        lat: The latitude of the location.
        lon: The longitude of the location.

    Returns:
        A pandas DataFrame containing historical irradiation data.
    """
    url = (f'https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}'
           f'&start_date={start_date}&end_date={end_date}&daily=weathercode,shortwave_radiation_sum'
           '&timezone=America%2FSao_Paulo')

    response = requests.get(url)
    response.raise_for_status()

    df = pd.DataFrame(response.json()['daily'])
    ibge_code = get_ibge_code(lat, lon)
    df = df.assign(ibge_code=ibge_code, time=pd.to_datetime(df['time'], format='%Y-%m-%d'))
    return df


def get_irrad_data(lat: float, lon: float) -> pd.DataFrame:
    """
    Get actual and predicted shortwave radiation sum data for a given location.

    Args:
        lat: The latitude of the location.
        lon: The longitude of the location.

    Returns:
        A pandas DataFrame containing actual and predicted shortwave radiation sum data for the given location.
    """
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


def get_location_from_addr(addr: str) -> Location:
    """
    Get latitude and longitude of a given address.

    Args:
        addr (str): The address for which to get the latitude and longitude.

    Returns:
        geopy.location.Location: Geopy location object
    """
    location = geocode(addr, addressdetails=True)
    return location
