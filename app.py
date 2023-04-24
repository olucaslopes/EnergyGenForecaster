import streamlit as st
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from utils import get_irrad_data
import plotly.express as px

st.set_page_config(page_title='Energy Generation Predictor', layout='wide', page_icon='🔌')

if 'pressed_change_addr' not in st.session_state:
    st.session_state.pressed_change_addr = False
if 'changed_addr' not in st.session_state:
    st.session_state.changed_addr = False
if 'loc_name' not in st.session_state:
    st.session_state.loc_name = 'São Paulo, SP'
if 'loc_lat' not in st.session_state:
    st.session_state.loc_lat = -23.55
if 'loc_lon' not in st.session_state:
    st.session_state.loc_lon = -46.64
if 'panels_area' not in st.session_state:
    st.session_state.panels_area = 18
if 'panels_rend' not in st.session_state:
    st.session_state.panels_rend = 15
if 'energy_price' not in st.session_state:
    st.session_state.energy_price = 0.656
if 'irrad_data' not in st.session_state or st.session_state.changed_addr:
    st.session_state.changed_addr = False
    st.session_state.irrad_data = get_irrad_data(st.session_state.loc_lat, st.session_state.loc_lon)
    # st.session_state.irrad_data = (irrad_data
    #                                .assign(type=irrad_data['true_label'].replace({0: 'predicted', 1: 'actual'}))
    #                                .drop(columns='true_value'))

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

#### SIDEBAR ###########

with st.sidebar:
    # user inputs
    st.session_state.panels_area = st.number_input('📐 Área total em m² dos painéis solares', step=5, min_value=2,
                                                   value=18)
    st.session_state.panels_rend = st.slider('💱 Eficiência média dos painéis solares', min_value=0, max_value=100,
                                             step=1, format='%d%%',
                                             value=15)
    number = st.number_input('💵 Tarifa média por kWh (R$)', min_value=0.05, max_value=2., step=0.001, value=0.656,
                             format='%.3f')
    st.session_state.energy_price = number

    col_desc_loc, col_alt_loc = st.columns(2)
    with col_desc_loc:
        st.markdown(f'📌 {st.session_state.loc_name}')
    with col_alt_loc:
        change_addr = st.button(label='Alterar', key='alt_loc')

    if change_addr or st.session_state.pressed_change_addr:
        st.session_state.pressed_change_addr = True
        st.session_state.changed_addr = True
        loc_input = st.text_input('Digite a localização')
        if loc_input:
            st.session_state.pressed_change_addr = False
            try:
                geolocator = Nominatim(user_agent="draw2text2")
                location = geolocator.geocode(loc_input, addressdetails=True)
                new_loc_name = f"{location.raw['address']['city']}, {location.raw['address']['ISO3166-2-lvl4'][-2:]}"
            except BaseException:
                st.error('Could not find address')
            else:
                st.session_state.loc_name = new_loc_name
                lat, lon = float(location.raw['lat']), float(location.raw['lon'])
                st.session_state.loc_lat, st.session_state.loc_lon = lat, lon
                st.experimental_rerun()

    m = folium.Map(location=[st.session_state.loc_lat, st.session_state.loc_lon],
                   zoom_start=10,
                   zoom_control=False,
                   scrollWheelZoom=False,
                   dragging=False)
    folium.Marker(
        [st.session_state.loc_lat, st.session_state.loc_lon]
    ).add_to(m)
    st_folium(m, height=100, width=None)

##########################
st.header('🔌 Energy Generation Predictor')

if 'irrad_data' not in st.session_state or st.session_state.changed_addr:
    st.session_state.changed_addr = False
    st.session_state.irrad_data = get_irrad_data(st.session_state.loc_lat, st.session_state.loc_lon)
    # st.session_state.irrad_data = (irrad_data
    #                                .assign(type=irrad_data['true_label'].replace({0: 'predicted', 1: 'actual'}))
    #                                .drop(columns='true_value'))

pred_irrad_sum = st.session_state.irrad_data.query('type == "predicted"')['shortwave_radiation_sum'].sum()

# Calculate generated energy
gen_energy = pred_irrad_sum * st.session_state.panels_area * st.session_state.panels_rend / 100
savings = gen_energy * st.session_state.energy_price

col_mainsub1, col_mainsub2 = st.columns(2)
with col_mainsub1:
    st.metric(label='Total Estimated Generated Energy', value=f'⚡ {gen_energy:,.0f} kW/h')

with col_mainsub2:
    st.metric(label='Estimated saving', value=f'💲 R$ {savings:,.2f}')

st.subheader('Monthly Potential Generated Energy')

ten_years_ago = datetime.today() - timedelta(days=365 * 10)

st.session_state.irrad_data = st.session_state.irrad_data.assign(
    kWh=st.session_state.irrad_data[
            'shortwave_radiation_sum'] * st.session_state.panels_area * st.session_state.panels_rend / 100
)
fig1 = px.line(
    st.session_state.irrad_data[(st.session_state.irrad_data['time'] >= ten_years_ago)],
    x='time', y='kWh',
    color='type',
    height=300
)
fig1.update_layout(legend=dict(
    orientation="h",
    entrywidth=70,
    yanchor="bottom",
    y=1.02,
    xanchor="right",
    x=1
))

st.plotly_chart(fig1, theme="streamlit", use_container_width=True)
