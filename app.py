import streamlit as st
from datetime import datetime, timedelta
from streamlit_folium import st_folium
from utils import get_irrad_data, get_location_from_addr
from helpers import get_map, plot_monthly_energy_generated

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
if 'irrad_data' not in st.session_state or st.session_state.changed_addr:
    st.session_state.changed_addr = False
    st.session_state.irrad_data = get_irrad_data(st.session_state.loc_lat, st.session_state.loc_lon)

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

#### SIDEBAR ###########

with st.sidebar:
    # user inputs
    panels_area = st.number_input(
        "📐 Área total em m² dos painéis solares",
        step=5,
        min_value=2,
        value=18,
    )
    panels_rend = st.slider(
        "💱 Eficiência média dos painéis solares",
        min_value=0,
        max_value=100,
        step=1,
        format="%d%%",
        value=15,
    )
    energy_price = st.number_input(
        "💵 Tarifa média por kWh (R$)",
        min_value=0.05,
        max_value=2.0,
        step=0.001,
        value=0.656,
        format="%.3f",
    )

    col_desc_loc, col_alt_loc = st.columns(2)
    with col_desc_loc:
        st.markdown(f'📌 {st.session_state.loc_name}')
    with col_alt_loc:
        change_addr = st.button(label='Alterar', key='alt_loc')

    if change_addr or st.session_state.pressed_change_addr:
        st.session_state.pressed_change_addr = True
        with st.form("change_loc_form"):
            loc_input = st.text_input('Digite a nova localização')
            submit_new_loc = st.form_submit_button('Procurar')
            if submit_new_loc:
                st.session_state.pressed_change_addr = False
                try:
                    location = get_location_from_addr(loc_input)
                    new_loc_name = (
                        f"{location.raw['address']['city']}, "
                        f"{location.raw['address']['ISO3166-2-lvl4'][-2:]}"
                    )
                except BaseException:
                    st.error('Could not find address')
                else:
                    st.session_state.loc_name = new_loc_name
                    lat, lon = float(location.raw['lat']), float(location.raw['lon'])
                    if lat == st.session_state.loc_lat and lon == st.session_state.loc_lon:
                        # If lat and lon doesn't change, ignore
                        pass
                    else:
                        # Else update app
                        st.session_state.changed_addr = True
                        st.session_state.loc_lat, st.session_state.loc_lon = lat, lon
                        st.experimental_rerun()

    if not st.session_state.pressed_change_addr:
        m = get_map(st.session_state.loc_lat, st.session_state.loc_lon)
        st_folium(m, height=100, width=None)

##########################
st.header('🔌 Energy Generation Predictor')

pred_irrad_sum = st.session_state.irrad_data.query('type == "predicted"')['shortwave_radiation_sum'].sum()

# Calculate generated energy
gen_energy = pred_irrad_sum * panels_area * panels_rend / 100
savings = gen_energy * energy_price

col_mainsub1, col_mainsub2 = st.columns(2)
with col_mainsub1:
    st.metric(label='Total Estimated Generated Energy', value=f'⚡ {gen_energy:,.0f} kW/h')

with col_mainsub2:
    st.metric(label='Estimated saving', value=f'💲 R$ {savings:,.2f}')

st.subheader('Monthly Potential Generated Energy')

ten_years_ago = datetime.today() - timedelta(days=365 * 10)

st.session_state.irrad_data = st.session_state.irrad_data.assign(
    kWh=st.session_state.irrad_data[
            'shortwave_radiation_sum'] * panels_area * panels_rend / 100
)
fig1 = plot_monthly_energy_generated(
    # Plot last 10 years of data and predicted values
    data=st.session_state.irrad_data[(st.session_state.irrad_data['time'] >= ten_years_ago)]
)

st.plotly_chart(fig1, theme="streamlit", use_container_width=True)
