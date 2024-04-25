
from os import environ as ENV

import altair as alt
import pandas as pd
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import streamlit as st
from vega_datasets import data


def connect_to_db(config):
    """Returns a live database connection."""
    return connect(
        host=config["DB_HOST"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        database=config["DB_NAME"],
        port=config["DB_PORT"]
    )


def get_location_forecast_data(conn) -> pd.DataFrame:
    """Returns location data as DataFrame from database."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:

        cur.execute(f"""SELECT l.latitude, l.longitude, l.loc_name as Location, c.name as County, co.name as Country,
                    f.forecast_timestamp as forecast_time, wc.description as weather
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
                    GROUP BY forecast_time, l.loc_id, County, Country, weather
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)

    return data_f


def uk_map(loc_data, tooltips):
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


if __name__ == "__main__":
    load_dotenv()
    with connect_to_db(ENV) as conn:
        forecast_d = get_location_forecast_data(conn)
        location = st.selectbox('Locations',
                                ['Select a location...'] + list(forecast_d['location'].sort_values().unique()))
        print(location)
        if location != 'Select a location...':
            w_map = uk_map(forecast_d, lat, lon, ['location', 'weather'])
            st.altair_chart(w_map, use_container_width=True)
        else:
            st.warning('No location selected!')
