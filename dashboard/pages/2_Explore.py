from datetime import datetime
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
                    GROUP BY "Forecast time", l.loc_id, "County", "Country", "Weather"
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)

    return data_f


def get_locations_with_alerts():
    """Get the loc_id and alert type if they exist in database"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute("""SELECT AL.name as "Alert type", SL.severity_level as "Severity", 
                    L.loc_name as "Location", L.loc_id, MIN(F.forecast_timestamp) as min_time, MAX(F.forecast_timestamp) as max_time
                    FROM weather_alert AS WA
                    JOIN forecast AS F ON (WA.forecast_id = F.forecast_id)
                    JOIN severity_level AS SL ON (WA.severity_level_id = SL.severity_level_id)
                    JOIN alert_type AS AL ON (WA.alert_type_id = AL.alert_type_id)
                    JOIN weather_report AS WR ON (F.weather_report_id = WR.weather_report_id)
                    JOIN location AS L ON (WR.loc_id = L.loc_id)
                    WHERE SL.severity_level_id != 4
                    GROUP BY L.loc_id, "Alert type", "Severity", SL.severity_level_id
                    ORDER BY SL.severity_level_id DESC, L.loc_id ASC
                    ;""")

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)

    return data_f


def get_all_alerts():
    """Returns alert data as DataFrame from database."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute("""SELECT SL.severity_level as "Severity", 
                    L.loc_name, AL.name as "Alert type", L.latitude, L.longitude, 
                    L.loc_name as "Location", C.name as "County", CO.name as "Country",
                    F.forecast_timestamp as "Forecast time"
                    FROM weather_alert AS WA
                    JOIN severity_level AS SL ON (WA.severity_level_id = SL.severity_level_id)
                    JOIN forecast AS F ON (WA.forecast_id = F.forecast_id)
                    JOIN alert_type AS AL ON (WA.alert_type_id = AL.alert_type_id)
                    JOIN weather_report AS WR ON (F.weather_report_id = WR.weather_report_id)
                    JOIN location AS L ON (WR.loc_id = L.loc_id)
                    JOIN county AS C ON (L.county_id = C.county_id)
                    JOIN country as CO ON (C.country_id = CO.country_id)
                    GROUP BY L.latitude, L.longitude, "Location", "County", "Country", "Forecast time", "Severity", "Alert type"
                    ORDER BY "Forecast time"
                    ;""")

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


def get_map(loc_data, lat, lon, location_type):
    if location_type == 'Location':
        zoom = 11
    elif location_type == 'County':
        zoom = 10
    elif location_type == 'Country':
        zoom = 6.5
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=zoom,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                'HexagonLayer',
                data=loc_data,
                get_position="[latitude, longitude]",
                radius=200,
                elevation_scale=4,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
            ),
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
    st.title('Explore')
    with connect_to_db(ENV) as conn:
        forecast_d = get_location_forecast_data(conn)
    with st.sidebar:
        by_loc = st.checkbox("Search by location")
        if by_loc:
            loc_type = st.selectbox('Search by:',
                                    ['Location', 'County', 'Country'])
            if loc_type == 'Location':
                location = st.selectbox('Locations',
                                        forecast_d['Location'].sort_values().unique())
            elif loc_type == 'County':
                location = st.selectbox('Counties',
                                        forecast_d['County'].sort_values().unique())
            elif loc_type == 'Country':
                location = st.selectbox('Locations',
                                        forecast_d['Country'].sort_values().unique())

    if by_loc:
        lat, lon, county = forecast_d[forecast_d[loc_type] == location][[
            'latitude', 'longitude', 'County']].values[0]
        forecast_d = forecast_d[forecast_d['Forecast time']
                                == time_rounder(datetime.now())]
        w_map = get_map(forecast_d, lat, lon, loc_type)
    else:
        alerts = get_locations_with_alerts()
        for _, alert in alerts.iterrows():
            if alert["Severity"] == "Alert":
                icon = "❕"
            elif alert["Severity"] == "Warning":
                icon = "⚠️"
            elif alert["Severity"] == "Severe Warning":
                icon = "🚨"
            st.warning(
                f'**{alert["Location"]}** has a **{alert["Alert type"]} {alert["Severity"]}** from **{alert["min_time"]}** to **{alert["max_time"]}**', icon=icon)
