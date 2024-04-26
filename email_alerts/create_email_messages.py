"""Create the html messages for different types of weather alerts."""

import datetime


def get_alert_msg(alert, type):
    """Creates an alert message depending on severity and type of alert."""

    if alert == 'Alert':
        return f'{alert}! Higher {type}'
    if alert == 'Warning':
        return f'{alert}! High {type}'
    if alert == 'Severe Warning':
        return f'{alert}! Extreme {type}'
    return alert


def get_alert_visual(alert):
    """creates a html span for a warning sign to signify the level of alert."""

    visual = """<span style = 'color: {}; font-size: 30px; '>&#x26A0</span>"""
    if alert == 'Alert':
        return visual.format('#f3d300')
    if alert == 'Warning':
        return visual.format('orange')
    if alert == 'Severe Warning':
        return visual.format('red')
    return ''


def create_html_table_weather(user_alerts: list[list[str]]) -> str:
    """creates an html table for weather warnings in an area."""

    table_style = "'border: 1px solid  black;text-align: left;padding: 8px;'"""

    table = f"""<table style=
    'font-family: arial, sans-serif;
    border-collapse: collapse;
    padding: 2rem 0.5rem;
    background-color: white;'>
    <tr><th></th><th></th><th></th></tr>"""

    for alert in user_alerts:
        if alert[0] != 'weather_alert':
            continue
        alert_msg = get_alert_msg(alert[2], alert[5])
        table += f"""<tr>
        <td style={table_style}>{get_alert_visual(alert[2])}</td>
        <td style={table_style}>{alert[6].strftime("%H:%M:%S")}</td>
        <td style={table_style}>{alert[3]}</td>
        <td style={table_style}>{alert_msg} {alert[-1]}</td>
        </tr>"""
    table += "</table>"
    return table


def create_html_air_quality(user_alerts: list[list[str]]) -> str:
    """creates the html message for air quality in the area."""

    html_string = """"""
    for alert in user_alerts:
        if alert[0] != 'air_quality':
            continue
        air_warning = """<h3>{} {} in {}</h3>"""
        air_warning = air_warning.format(get_alert_visual(alert[2]), get_alert_msg(
            alert[2], 'Pollution Levels'), alert[3])
        html_string += air_warning
    return html_string


def create_html_flood_alerts(user_alerts: list[list[str]]) -> str:
    """Create the html message for flood warnings in an area."""

    html_string = """"""
    for alert in user_alerts:
        if alert[0] != 'flood_warnings':
            continue
        flood_alert = """<h3>{} {} in {} - {}</h3>"""
        flood_alert = flood_alert.format(get_alert_visual(alert[2]), get_alert_msg(
            alert[2], 'Risk of Flooding'), alert[3], alert[5].strftime("%H:%M:%S"))
        html_string += flood_alert
    return html_string


def create_full_html_per_user(users_weather: list[list]) -> str:
    """Creates a html message based on a user's weather alerts."""

    html_msg = """<h1>!!!!!Weather Alerts!!!!!</h1>"""
    weather_alerts = create_html_table_weather(users_weather)
    air_quality = create_html_air_quality(users_weather)
    flood_warning = create_html_flood_alerts(users_weather)

    html_msg += air_quality + flood_warning + weather_alerts

    html_msg = html_msg.replace('\n', '')
    return html_msg


def assign_messages_to_recipients(recipients: dict) -> dict:
    """create a new dict with the html messages as values."""
    html_messages = {}
    for key in recipients.keys():
        html_messages[key] = create_full_html_per_user(recipients.get(key))

    return html_messages


if __name__ == '__main__':

    test_data = {'nathan@gmail.com': [['weather_alert', 1, 'Alert', 'Liverpool', 'Liverpool City Region', 'UV-index', datetime.datetime(2024, 4, 25, 15, 42), 'Clear Sky', datetime.datetime(2024, 4, 25, 15, 42, 42, 19560), 3.3, '&#x1F506'], ['weather_alert', 2, 'Alert', 'Liverpool', 'Liverpool City Region', 'UV-index', datetime.datetime(2024, 4, 25, 15, 57), 'Clear Sky', datetime.datetime(2024, 4, 25, 15, 42, 42, 19560), 3.0, '&#x1F506'], [
        'weather_alert', 3, 'Alert', 'Liverpool', 'Liverpool City Region', 'UV-index', datetime.datetime(2024, 4, 25, 16, 12), 'Mainly Clear', datetime.datetime(2024, 4, 25, 15, 42, 42, 19560), 2.75, '&#x1F506'], ['weather_alert', 4, 'Alert', 'Liverpool', 'Liverpool City Region', 'UV-index', datetime.datetime(2024, 4, 25, 16, 27), 'Partly Cloudy', datetime.datetime(2024, 4, 25, 15, 42, 42, 19560), 2.55, '&#x1F506'], ['air_quality', 1, 'Alert', 'Liverpool', 'Liverpool City Region', 102], ['flood_warnings', 1, 'Warning', 'Liverpool', 'Liverpool City Region', datetime.datetime(2024, 4, 25, 15, 42)]]
    }
    x = assign_messages_to_recipients(test_data)
    file = open("output.html", "w")

    file.write(x.get('nathan@gmail.com'))
    file.close()
