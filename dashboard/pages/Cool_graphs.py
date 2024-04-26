"""Create and host a streamlit dashboard"""

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


def get_data_from_db(conn, table_name) -> pd.DataFrame:
    """Returns data as DataFrame from database."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"SELECT * FROM {table_name};")
        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)
    return data_f


def get_data_from_db(conn, table_name) -> pd.DataFrame:
    """Returns data as DataFrame from database."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"SELECT * FROM {table_name};")
        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)
    return data_f


def get_location_data(conn) -> pd.DataFrame:
    """Returns location data as DataFrame from database."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:

        cur.execute(f"""SELECT l.latitude, l.longitude, l.loc_name as Location, c.name as County, co.name as Country
                    FROM location AS l
                    JOIN county as c
                    ON (l.county_id=c.county_id)
                    JOIN country as co
                    ON (c.country_id=co.country_id)
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)

    return data_f


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


def get_sidebar(some_data):
    """Set up streamlit sidebar with headers and filters."""
    st.sidebar.title('Filters')
    st.sidebar.subheader('Data analysis of plant conditions')
    sort_ed = st.sidebar.checkbox('Sorted',
                                  True)
    with st.sidebar.expander('Filter by location'):
        all_options = st.checkbox("Start from all plants", True, True)
        if all_options:
            plants = st.multiselect('Counties',
                                    some_data['Plant'].sort_values().unique(),
                                    default=some_data['Plant'].sort_values(
                                    ).unique())
        else:
            plants = st.multiselect('Plants',
                                    some_data['Plant'].sort_values().unique(),
                                    default=None)
    return plants, sort_ed


if __name__ == "__main__":

    load_dotenv()
    with connect_to_db(ENV) as connection:
        forecast_data = get_data_from_db(connection, 'forecast')
        forecast_d = get_location_forecast_data(connection)
        button_home, button_location, third_button = st.columns([1, 3, 5])
        with button_home:
            st.button("Home", type="primary")
        with button_location:
            button_loc = st.checkbox(
                'Pick a specific location')
        if button_loc:
            location = st.selectbox('Locations',
                                    ['Select a location...'] + list(forecast_d['location'].sort_values().unique()))
            print(location)
            if location != 'Select a location...':
                st.write('some stuff')
            else:
                st.warning('No location selected!')
        else:

            # Title
            st.title('Dashboard')

            # Sidebar
            # plant_list, sorted_plants = get_sidebar(basic_stats)

            # World Map
            w_map = uk_map(get_location_data(
                connection), ['location', 'county'])
            st.altair_chart(w_map, use_container_width=True)

            w_map = uk_map(forecast_d, ['location', 'weather'])
            st.altair_chart(w_map, use_container_width=True)

            # Average temperatures graph
            # average_temps = basic_stats.groupby(
            #     ['Plant'])['Temperature'].mean().reset_index()

            # if sorted_plants:
            #     X_AVG_TEMP = alt.X('Plant:N').sort('-y')
            # else:
            #     X_AVG_TEMP = alt.X('Plant:N')
            # avg_temp = alt.Chart(average_temps[average_temps['Plant'].isin(plant_list)],
            #                      title='Average Temperatures').mark_bar().encode(
            #     x=X_AVG_TEMP,
            #     y='Temperature',
            #     color='Plant:N',
            #     tooltip=['Plant', 'Temperature']
            # )

            # st.altair_chart(avg_temp, use_container_width=True)

            # # Temperature over time graph
            # temps = alt.Chart(basic_stats[basic_stats['Plant'].isin(plant_list)],
            #                   title='Temperature over time').mark_line().encode(
            #     x='hours(Time):O',
            #     y=alt.Y('mean(Temperature):Q').scale(zero=False),
            #     color='Plant:N',
            #     tooltip='Plant'
            # )

            # st.altair_chart(temps, use_container_width=True)

            # # Soil moisture over time graph

            # moist = alt.Chart(basic_stats.loc[basic_stats['Plant'].isin(plant_list)],
            #                   title='Soil moisture over time').mark_line().encode(
            #     x='hours(Time):T',
            #     y='mean(Soil moisture):Q',
            #     color='Plant:N',
            #     tooltip=['Plant', 'mean(Soil moisture):Q']
            # )

            # st.altair_chart(moist, use_container_width=True)

            # # All data in last 24 hours table

            # st.write(basic_stats[basic_stats['Plant'].isin(
            #     plant_list)], use_container_width=True)
    connection.close()
