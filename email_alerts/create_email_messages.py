"""Create the html messages for different types of weather alerts."""

from os import environ as ENV
from datetime import datetime


ALERT = 'Alert'
WARNING = 'Warning'
S_WARNING = 'Severe Warning'
ALERT_TYPE_NAME_POS = 4
ALERT_TYPE_POS = 0
SEV_LEVEL_POS = 2
LOC_NAME_POS = 3
TIMESTAMP_POS = 5


def get_alert_msg(alert, alert_type):
    """Creates an alert message depending on severity and type of alert."""

    if alert == ALERT:
        return f'{alert}! Elevated {alert_type}'
    if alert == WARNING:
        return f'{alert}! High {alert_type}'
    if alert == S_WARNING:
        return f'{alert}! Extreme {alert_type}'
    return alert


def get_alert_visual(alert):
    """Gets the warning severity level colour."""

    if alert == ALERT:
        return '#f3d300'
    if alert == WARNING:
        return '#FF8300'
    if alert == S_WARNING:
        return 'red'
    return ''


def get_time_range_msg(min_time: datetime, max_time: datetime) -> str:
    """Returns a message depending on the time ranges."""

    if min_time == max_time:
        return min_time.strftime("%H:%M:%S")

    return min_time.strftime("%H:%M:%S") + " - " + max_time.strftime("%H:%M:%S")


def create_html_table_weather(user_alerts: list[list[str]], weather_alert: str) -> str:
    """Creates an html table for weather warnings in an area."""

    table_style = "'border: 1px solid  black;text-align: left;padding: 8px;'"""

    output = ''
    table = """<h2>Extreme Weather:</h2><table style=
    border-collapse: collapse;
    padding: 2rem 0.5rem;
    background-color: white;'>
    <tr><th></th><th></th><th></th></tr>"""

    for alert in user_alerts:
        if alert[ALERT_TYPE_POS] != weather_alert:
            continue
        alert_msg = get_alert_msg(
            alert[SEV_LEVEL_POS], alert[ALERT_TYPE_NAME_POS])
        output += f"""<tr>
        <td style='border: 1px solid  black;text-align: left;padding: 8px;
        background-color: {get_alert_visual(alert[SEV_LEVEL_POS])}; font-size: 30px;'>!</td>
        <td style={table_style}>{alert_msg} {alert[-1]}</td>
        <td style={table_style}>{alert[LOC_NAME_POS]}</td>
        <td style={table_style}>{get_time_range_msg(alert[TIMESTAMP_POS], alert[TIMESTAMP_POS+1])}</td>
        </tr>"""
    if not output:
        return ""
    table += output + "</table>"
    return table


def create_html_air_quality(user_alerts: list[list[str]], air_quality: str) -> str:
    """Creates the html message for air quality in the area."""

    html_string = """"""
    for alert in user_alerts:
        if alert[ALERT_TYPE_POS] != air_quality:
            continue
        if alert[SEV_LEVEL_POS] == 'Warning no longer in force':
            continue
        air_warning = """<h2>Air Quality:</h2><h3><span style='border: 1px solid  black;
        background-color: {}; text-align: center; font-size: 35px;
        display: inline-block; width:20px;'>!</span> {} in {}</h3>"""
        air_warning = air_warning.format(get_alert_visual(alert[SEV_LEVEL_POS]), get_alert_msg(
            alert[SEV_LEVEL_POS], 'Pollution Levels'), alert[LOC_NAME_POS])
        html_string += air_warning
    return html_string


def create_html_flood_alerts(user_alerts: list[list[str]], flood_alert: str) -> str:
    """Create the html message for flood warnings in an area."""

    html_string = """"""
    for alert in user_alerts:
        if alert[ALERT_TYPE_POS] != flood_alert:
            continue
        if alert[SEV_LEVEL_POS] == 'Warning no longer in force':
            continue
        flood_alert = """<h2>Flood Alerts:</h2><h3><span style='border: 1px solid  black;
        background-color: {}; text-align: center; font-size: 35px;
        display: inline-block; width:20px;'>!</span> {} in {} - {}</h3>"""
        flood_alert = flood_alert.format(get_alert_visual(alert[SEV_LEVEL_POS]), get_alert_msg(
            alert[SEV_LEVEL_POS], 'Risk of Flooding'), alert[LOC_NAME_POS], alert[TIMESTAMP_POS].strftime("%H:%M:%S"))
        html_string += flood_alert
    return html_string


def create_full_html_per_user(users_weather: list[list], tables: list[str]) -> str:
    """Creates a html message based on a user's weather alerts."""

    html_msg = """<!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-16">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head><body style=''font-family: arial, sans-serif; background-color:
    white; justify-content: center;align-items: center;'>
    <h1>!-!-!-!-!- Weather Alerts -!-!-!-!-!</h1>"""
    weather_alerts_data = create_html_table_weather(users_weather, tables[0])
    air_quality_data = create_html_air_quality(users_weather, tables[1])
    flood_warning_data = create_html_flood_alerts(users_weather, tables[2])

    if not weather_alerts_data and not air_quality_data and not flood_warning_data:
        return ''

    html_msg += air_quality_data + flood_warning_data + weather_alerts_data
    html_msg += """</body>"""
    html_msg = html_msg.replace('\n', '')
    return html_msg


def assign_messages_to_recipients(recipients: dict, tables: list[str]) -> dict:
    """create a new dict with the html messages as values."""
    html_messages = {}
    for key in recipients.keys():
        html_messages[key] = create_full_html_per_user(
            recipients.get(key), tables)

    return html_messages
