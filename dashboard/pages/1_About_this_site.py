"""Write some information for the user about this dashboard."""

from os import environ as ENV

import altair as alt
from dotenv import load_dotenv
import pandas as pd
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection
import streamlit as st
from vega_datasets import data


def intro() -> None:
    """Write some streamlit text about the dashboard."""
    st.write("# Welcome to the Climate Monitor! :sun_small_cloud:")

    st.markdown(
        """<span style="font-size:1.3em;">
        <br/>
        <b>👈 Select a page from the menu on the left</b> to explore the dashboard!<br/><br/>
        <b>Home</b> Quick search - get the coming forecast and find weather alerts by location!<br/>
        <b>Explore</b>: Explore the current climate across the UK.<br/>
        <b>Alerts across the UK</b>: Get the latest weather alerts, 
        including floods and air quality warnings.<br/>
        <b>Sign Up</b>: Want to sign up to daily newsletters, or receive notifications about weather alerts 
        near you? Then sign up here!<br/><br/></span>""", unsafe_allow_html=True)
    st.markdown("""<span style="font-size:1.3em;">
        <b> Contributors: </b><br/>
        Dom Chambers<br/>
        Arjun Babhania<br/>
        Nathan McKittrick<br/>
        Dana Weetman</span>
    """, unsafe_allow_html=True
                )


@st.cache_resource
def connect_to_db(config: dict) -> connection:
    """Returns a live database connection."""
    return connect(
        host=config["DB_HOST"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        database=config["DB_NAME"],
        port=config["DB_PORT"]
    )


@st.cache_data
def get_data_from_db(_conn: connection, table_name: str) -> pd.DataFrame:
    """Returns data as DataFrame from database."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"SELECT * FROM {table_name};")
        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)
    return data_f


@st.cache_data
def get_location_data(_conn: connection) -> pd.DataFrame:
    """Returns location data as DataFrame from database."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:

        cur.execute("""SELECT l.latitude, l.longitude, l.loc_name as Location,
                    c.name as County, co.name as Country
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
def get_location_forecast_data(_conn: connection) -> pd.DataFrame:
    """Returns location data as DataFrame from database."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:

        cur.execute("""SELECT l.latitude, l.longitude, l.loc_name as Location, c.name as County,
                    co.name as Country,
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


def uk_map(loc_data: pd.DataFrame, tooltips: list[str]) -> alt.LayerChart:
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
        w_map = uk_map(get_location_data(
            connection), ['location', 'county'])
        st.altair_chart(w_map, use_container_width=True)
        st.markdown(
            f"""<span style="font-size: 1.3em">
            This climate monitor is currently tracking {locations['location'].count()} 
            locations across the UK.<br/>
            If you want to add more locations, 👈 navigate to the <b>Sign Up</b> 
            page!</span>""", unsafe_allow_html=True)
    st.toast('Remember to sign up to become a user!')
