"""Create and host a streamlit dashboard"""

import pydeck as pdk
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from psycopg2 import connect
import pandas as pd
import altair as alt
from os import environ as ENV
import streamlit as st
from vega_datasets import data


def intro():

    st.write("# Welcome to the Climate Monitor! :sun_small_cloud:")
    st.markdown(
        f"""
        **👈 Select a page from the menu on the left** to explore the dashboard!

        **Home**: Quick search - get the coming forecast and find weather alerts by location!

        **Explore**: Explore the current climate across the UK.

        **Alerts across the UK**: Get the latest weather alerts, including floods and air quality warnings.

        ### Want to sign up to daily newsletters, or receive notifications about weather alerts near you?

        - Then check out the **Sign Up** page!""")
    st.page_link('pages/4_Sign_Up.py')
    st.markdown("""

        ### Contributors
        Project manager: **Dom Chambers**

        Quality Assurance: **Arjun Babhania**

        Architect: **Nathan McKittrick**

        Architect: **Dana Weetman**
    """
                )


@st.cache_resource
def connect_to_db(config):
    """Returns a live database connection."""
    return connect(
        host=config["DB_HOST"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        database=config["DB_NAME"],
        port=config["DB_PORT"]
    )


@st.cache_data
def get_data_from_db(_conn, table_name) -> pd.DataFrame:
    """Returns data as DataFrame from database."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"SELECT * FROM {table_name};")
        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)
    return data_f


@st.cache_data
def get_location_data(_conn) -> pd.DataFrame:
    """Returns location data as DataFrame from database."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:

        cur.execute(f"""SELECT l.latitude, l.longitude, l.loc_name as Location, c.name as County, co.name as Country
                    FROM location AS l
                    JOIN county as c
                    ON (l.county_id=c.county_id)
                    JOIN country as co
                    ON (c.country_id=co.country_id)
                    WHERE l.loc_id IN (
                    SELECT loc_id from weather_report
                    )
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)

    return data_f


@st.cache_data
def get_location_forecast_data(_conn) -> pd.DataFrame:
    """Returns location data as DataFrame from database."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:

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
        clipExtent=[[0, 0], [600, 600]],    # [[left, top], [right, bottom]]
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
    intro()
    load_dotenv()
    with connect_to_db(dict(ENV)) as connection:
        forecast_data = get_data_from_db(connection, 'forecast')
        forecast_d = get_location_forecast_data(connection)
        st.title('About the Data')
        locations = get_location_data(connection)
        print(locations)
        w_map = uk_map(get_location_data(
            connection), ['location', 'county'])
        st.altair_chart(w_map, use_container_width=True)
        st.write(
            f"This climate monitor is currently tracking {locations['location'].count()} locations across the UK.")
        st.write(
            "If you want to add more locations, 👈 navigate to the **Sign Up** page!")
