import folium
import plotly.express as px


def get_map(lat, lon):
    """
    Generates a Folium map with a marker at the current location.
    """
    m = folium.Map(
        location=[lat, lon],
        zoom_start=10,
        zoom_control=False,
        scrollWheelZoom=False,
        dragging=False,
    )
    folium.Marker([lat, lon]).add_to(m)
    return m


def plot_monthly_energy_generated(data):
    fig = px.line(
        data,
        x='time', y='kWh',
        color='type',
        height=300
    )
    fig.update_layout(legend=dict(
        orientation="h",
        entrywidth=70,
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ))
    return fig