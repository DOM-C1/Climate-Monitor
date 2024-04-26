from datetime import datetime, timedelta
from os import environ as ENV

import altair as alt
import pandas as pd
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import streamlit as st
from vega_datasets import data
import pydeck as pdk


def connect_to_db(config):
    """Returns a live database connection."""
    return connect(
        host=config["DB_HOST"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        database=config["DB_NAME"],
        port=config["DB_PORT"]
    )


def time_rounder(timestamp: datetime, get_fifteen: bool = True) -> datetime:
    """Obtains the most recent 15 min time, or the most recent hour"""
    if get_fifteen:
        return (timestamp.replace(second=0, microsecond=0, minute=(timestamp.minute // 15 * 15)))
    return (timestamp.replace(second=0, microsecond=0, minute=0))


def get_location_forecast_data(conn) -> pd.DataFrame:
    """Returns location data as DataFrame from database."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT l.latitude, l.longitude, l.loc_name as "Location", c.name as "County", co.name as "Country",
                    f.forecast_timestamp as "Forecast time", wc.description as "Weather"
                    FROM location AS l
                    JOIN county as c
                    ON (l.county_id=c.county_id)
                    JOIN country as co
                    ON (c.country_id=co.country_id)
                    JOIN weather_report as w
                    ON (l.loc_id=w.loc_id)
                    JOIN forecast as f
                    ON (f.weather_report_id=w.weather_report_id)
                    JOIN weather_code as wc
                    ON (f.weather_code_id=wc.weather_code_id)
                    WHERE F.forecast_timestamp < NOW() + interval '12 hours'
                    AND EXTRACT(minutes from F.forecast_timestamp) = 0
                    AND EXTRACT(hours from F.forecast_timestamp) % 2 = 0
                    GROUP BY "Forecast time", l.loc_id, "County", "Country", "Weather"
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)

    return data_f


def uk_map(loc_data, lat, lon, tooltips):
    """Generates a uk map of where the locations."""
    # Load GeoJSON data
    countries = alt.topo_feature(data.world_110m.url, 'countries')

    background = alt.Chart(countries).mark_geoshape(
        fill='lightgray',
        stroke='white',
        tooltip=None
    ).project(
        type='mercator',
        scale=1500,                          # Magnify
        center=[-2, 54],                     # [lon, lat]
        clipExtent=[[0, 0], [500, 500]],    # [[left, top], [right, bottom]]
    ).properties(
        width=500,
        height=500
    )
    points = alt.Chart(loc_data).mark_circle(color='red').encode(
        latitude='latitude:Q',
        longitude='longitude:Q',
        size=alt.value(20),
        tooltip=tooltips
    ).project(
        type='mercator',
        scale=1500,                          # Magnify
        center=[-2, 54],                     # [lon, lat]
        clipExtent=[[0, 0], [500, 500]],    # [[left, top], [right, bottom]]
    ).properties(
        width=500,
        height=500
    )
    return alt.layer(background, points).properties(title='Location map')


def get_map(loc_data, lat, lon):
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=12,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=loc_data,
                get_position="[longitude, latitude]",
                get_color='[200, 30, 0, 160]',
                get_text="location",
                get_radius=200,
                pickable=True
            ),
        ],
        tooltip={'html': '<b>Weather:</b> {Weather}\
                 <b>Location:</b> {Location}',
                 'style': {"backgroundColor": "navyblue", 'color': '#87CEEB', 'font-size': '100%'}}))


if __name__ == "__main__":
    load_dotenv()
    st.title('Quick Search')
    with connect_to_db(ENV) as conn:
        forecast_d = get_location_forecast_data(conn)
        location = st.selectbox('Locations',
                                ['Select a location...'] + list(forecast_d['Location'].sort_values().unique()))
        if location != 'Select a location...':
            print(forecast_d)
            print(location)
            lat, lon = forecast_d[forecast_d['Location'] ==
                                  location][['latitude', 'longitude']].values[0]
            w_map = get_map(forecast_d, lat, lon)
            forecast_d = forecast_d[forecast_d['Location'] == location]
            lat, lon = forecast_d[['latitude', 'longitude']].values[0]
            forecast_d = forecast_d
            st.markdown("# Today's forecast")
            st.write("average temp, modal weather code, etc.")
            st.write(forecast_d)
            st.markdown("# This week's forecast")
            st.write(forecast_d)
            w_map = get_map(forecast_d, lat, lon)
        else:
            st.write('Please pick a location!')
