import streamlit as st
from datetime import datetime
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from utils import predict_city_irradiation
from functions_models import xgboost_regressor

st.set_page_config(page_title='Energy Generation Predictor', layout='wide', page_icon='🔌')

if 'pressed_change_addr' not in st.session_state:
    st.session_state.pressed_change_addr = False
if 'loc_name' not in st.session_state:
    st.session_state.loc_name = 'São Paulo, SP'
if 'loc_lat' not in st.session_state:
    st.session_state.loc_lat = -23.55
if 'loc_lon' not in st.session_state:
    st.session_state.loc_lon = -46.64

st.header('🔌 Energy Generation Predictor')

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

col_main1, col_main2 = st.columns([3, 1])

with col_main1:
    col_mainsub1, col_mainsub2 = st.columns(2)
    with col_mainsub1:
        st.metric(label='Total Estimated Generated Energy', value=f'⚡ {18_240:,} kW/h')

    with col_mainsub2:
        st.metric(label='Estimated saving', value=f'💲 R$ {11_965.44:,.2f}')

    #### TO BE REPLACED ######
    # # CSV's
    # df_irrad = pd.read_csv('data/openw_irradiation_2005_2020.csv')
    # df_irrad.drop(['day', 'weather_id'], axis=1, inplace=True)
    #
    # y_pred = xgboost_regressor(df_irrad)  # irradiation predictions
    #
    # # y_pred = [118.130264, 114.73563 , 101.42404 , 176.47775 , 112.80841 ,
    # #        157.99327 , 110.982155, 108.196976, 110.56889 , 137.60085 ,
    # #        110.87699 , 109.21667 , 102.76564 , 104.48606 , 167.93588 ,
    # #        109.639755, 188.73145 , 113.77642 , 139.08853 , 114.32364 ,
    # #        150.87944 , 150.07391 , 167.99814 , 133.70808 , 118.03198 ,
    # #        133.8792  , 142.81291 , 151.81943 , 145.09813 , 150.08461 ,
    # #        108.7888  , 154.68489 , 131.83202 , 119.56206 , 156.33952 ,
    # #        113.300896, 167.98074 , 153.09451 , 132.89561 , 149.40417 ,
    # #        212.66118 , 115.48822 , 165.70786 , 158.96251 , 104.79509 ,
    # #        167.0878  ,  96.5487  , 133.39662]
    #
    # now = datetime.now()
    # current_month = now.month
    # current_year = now.year
    #
    # dates = [datetime(current_year + ((current_month + i - 1) // 12), (current_month + i) % 12 or 12, 1) for i in
    #          range(1, 33)]
    # df = pd.DataFrame({'data': dates,
    #                    'irrad kwh/m2': y_pred})
    #
    # ##########################################

    # st.line_chart(data=df, x='data', y='irrad kwh/m2')

with col_main2:
    # user inputs
    area = st.number_input('📐 Área total em m² dos painéis solares', step=5, min_value=2, value=18)
    rend = st.slider('💱 Eficiência média dos painéis solares', min_value=0, max_value=100, step=1, format='%d%%',
                     value=15)
    range_data = st.number_input('🗓️ Anos para previsão', min_value=1, max_value=20, step=1)

    col_desc_loc, col_alt_loc = st.columns(2)
    with col_desc_loc:
        st.markdown(f'📌 {st.session_state.loc_name}')
    with col_alt_loc:
        change_addr = st.button(label='Alterar', key='alt_loc')

    if change_addr or st.session_state.pressed_change_addr:
        st.session_state.pressed_change_addr = True
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
                st.session_state.loc_lat, st.session_state.loc_lon = float(location.raw['lat']), float(location.raw['lon'])
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


#######################App###################################
# st.dataframe(df)
#
# # calc_energy
# calc_energy = df['irrad kwh/m2'].sum() * area * rend / 100
# st.write(f'A energia gerada para os próximos {range_data} anos é', round(calc_energy, 2), 'kwh')
