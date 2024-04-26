"""Create the html messages for different types of weather alerts."""

from os import environ as ENV


ALERT = 'Alert'
WARNING = 'Warning'
S_WARNING = 'Severe Warning'


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
    """gets the warning severity level colour."""

    if alert == ALERT:
        return '#f3d300'
    if alert == WARNING:
        return '#FF8300'
    if alert == S_WARNING:
        return 'red'
    return ''


def create_html_table_weather(user_alerts: list[list[str]]) -> str:
    """creates an html table for weather warnings in an area."""

    weather_alert = ENV['WEATHER_WARNING_TABLE']
    table_style = "'border: 1px solid  black;text-align: left;padding: 8px;'"""

    table = """<table style=
    border-collapse: collapse;
    padding: 2rem 0.5rem;
    background-color: white;'>
    <tr><th></th><th></th><th></th></tr>"""

    for alert in user_alerts:
        if alert[0] != weather_alert:
            continue
        alert_msg = get_alert_msg(alert[2], alert[5])
        table += f"""<tr>
        <td style='border: 1px solid  black;text-align: left;padding: 8px;
        background-color: {get_alert_visual(alert[2])}; font-size: 30px;'>!</td>
        <td style={table_style}>{alert_msg} {alert[-1]}</td>
        <td style={table_style}>{alert[3]}</td>
        <td style={table_style}>{alert[6].strftime("%H:%M:%S")}</td>
        </tr>"""
    table += "</table>"
    return table


def create_html_air_quality(user_alerts: list[list[str]]) -> str:
    """creates the html message for air quality in the area."""

    air_quality = ENV['AIR_QUALITY_TABLE']
    html_string = """"""
    for alert in user_alerts:
        if alert[0] != air_quality:
            continue
        if alert[2] == 'Warning no longer in force':
            continue
        air_warning = """<h3><span style='border: 1px solid  black;
        background-color: {}; text-align: center; font-size: 35px;
        display: inline-block; width:20px;'>!</span> {} in {}</h3>"""
        air_warning = air_warning.format(get_alert_visual(alert[2]), get_alert_msg(
            alert[2], 'Pollution Levels'), alert[3])
        html_string += air_warning
    return html_string


def create_html_flood_alerts(user_alerts: list[list[str]]) -> str:
    """Create the html message for flood warnings in an area."""

    flood_alert = ENV['FLOOD_WARNING_TABLE']
    html_string = """"""
    for alert in user_alerts:
        if alert[0] != flood_alert:
            continue
        if alert[2] == 'Warning no longer in force':
            continue
        flood_alert = """<h3><span style='border: 1px solid  black;
        background-color: {}; text-align: center; font-size: 35px;
        display: inline-block; width:20px;'>!</span> {} in {} - {}</h3>"""
        flood_alert = flood_alert.format(get_alert_visual(alert[2]), get_alert_msg(
            alert[2], 'Risk of Flooding'), alert[3], alert[5].strftime("%H:%M:%S"))
        html_string += flood_alert
    return html_string


def create_full_html_per_user(users_weather: list[list]) -> str:
    """Creates a html message based on a user's weather alerts."""

    html_msg = """<!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-16">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head><body style=''font-family: arial, sans-serif; background-color:
    white; justify-content: center;align-items: center;'>
    <h1>!!!!!Weather Alerts!!!!!</h1>"""
    weather_alerts_data = create_html_table_weather(users_weather)
    air_quality_data = create_html_air_quality(users_weather)
    flood_warning_data = create_html_flood_alerts(users_weather)

    html_msg += air_quality_data + flood_warning_data + weather_alerts_data
    html_msg += """</body>"""
    html_msg = html_msg.replace('\n', '')
    return html_msg


def assign_messages_to_recipients(recipients: dict) -> dict:
    """create a new dict with the html messages as values."""
    html_messages = {}
    for key in recipients.keys():
        html_messages[key] = create_full_html_per_user(recipients.get(key))

    return html_messages
