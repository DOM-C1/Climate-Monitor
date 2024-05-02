"""This file sends the daily report to users asynchronously."""
import asyncio
from datetime import datetime
from os import environ as ENV

import aioboto3
import pandas as pd
from boto3 import client
from dotenv import load_dotenv
from psycopg2 import connect
from psycopg2.extensions import connection

WEATHER_EMOJIS = {
    "Clear Sky": "☀️",
    "Mainly Clear": "🌤",
    "Partly Cloudy": "⛅",
    "Overcast": "☁️",
    "Fog": "🌫️",
    "Depositing Rime Fog": "🌫️",
    "Light Drizzle": "🌦️",
    "Moderate Drizzle": "🌧️",
    "Dense Drizzle": "🌧️",
    "Light Freezing Drizzle": "🌧️",
    "Dense Freezing Drizzle": "🌨️",
    "Slight Rain": "🌦️",
    "Moderate Rain": "🌧️",
    "Heavy Rain": "🌧️",
    "Light Freezing Rain": "🌧️",
    "Heavy Freezing Rain": "🌨️",
    "Slight Snowfall": "🌨️",
    "Moderate Snowfall": "🌨️",
    "Heavy Snowfall": "❄️",
    "Snow grains": "❄️",
    "Slight Rain Showers": "🌦️",
    "Moderate Rain Showers": "🌦️",
    "Violent Rain Showers": "🌧️",
    "Slight Snow Showers": "🌨️",
    "Heavy Snow Showers": "🌨️",
    "Thunderstorm": "⛈️",
    "Thunderstorm with Slight Hail": "⛈️",
    "Thunderstorm with Heavy Hail": "⛈️"
}


def handler(event: dict = None, context: dict = None) -> None:
    """This is designed to be compatible with the AWS Lambda function format."""
    asyncio.run(main())


async def main() -> None:
    """Designed to asynchronously send emails."""
    load_dotenv()
    conn = get_db_connection(ENV)
    df = prepare_data_frame(conn)
    async with aioboto3.Session().client('ses', aws_access_key_id=ENV['AWS_KEY'],
                                         aws_secret_access_key=ENV['AWS_SKEY'],
                                         region_name='eu-west-2') as ses:
        tasks = [asyncio.create_task(send_email(ses, await format_forecast_report(df, email), email))
                 for email in df['email'].unique()]
        await asyncio.gather(*tasks)
    conn.close()


def get_db_connection(config: dict) -> connection:
    """Establishes a database connection using provided configuration."""
    return connect(
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        database=config["DB_NAME"]
    )


def execute_query(conn: connection, query: str) -> pd.DataFrame:
    """Executes a SQL query and returns the results as a pandas DataFrame."""
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

    return pd.DataFrame(rows, columns=columns)


def prepare_data_frame(conn: connection) -> pd.DataFrame:
    """Prepares a complete data frame combining user details with weather forecasts."""
    user_details_query = """
        SELECT *
        FROM user_details AS UD
        JOIN user_location_assignment ON UD.user_id = user_location_assignment.user_id
        JOIN location ON user_location_assignment.loc_id = location.loc_id
        JOIN weather_report ON location.loc_id = weather_report.loc_id
    """
    forecast_query = """
        SELECT *
        FROM forecast AS F
        JOIN weather_code WC ON F.weather_code_id = WC.weather_code_id
        JOIN weather_report WR ON F.weather_report_id = WR.weather_report_id
    """
    user_details = execute_query(conn, user_details_query)
    forecast_details = execute_query(conn, forecast_query)
    forecast_details = forecast_details.loc[:,
                                            ~forecast_details.columns.duplicated()]

    combined_df = pd.merge(user_details, forecast_details,
                           on='weather_report_id', suffixes=('_user', '_forecast'))
    combined_df = combined_df.loc[:,
                                  ~combined_df.columns.duplicated()]
    return combined_df[combined_df['report_opt_in'] == True]


def add_unicode(cell: str) -> str:
    """Adds emojis to the end of the weather description."""
    return f"{cell} {WEATHER_EMOJIS[cell]}"


async def send_email(ses: client, html_content: str, recipient: str) -> None:
    """Async function to send email using AWS SES."""
    try:
        response = await ses.send_email(

            Source='trainee.dominic.chambers@sigmalabs.co.uk',
            Destination={'ToAddresses': [recipient]},
            Message={
                'Subject': {'Data': 'Your Weather Forecast for the day'},
                'Body': {'Html': {'Data': html_content}}
            }
        )
        print("Email sent! Message ID:", response['MessageId'])
    except Exception as e:
        print("Error sending email:", e)


def format_time(hour: int) -> str:
    if hour < 10:
        return f"0{hour}:00"
    return f"{hour}:00"


def format_html(report: str) -> str:
    return f"""
    <html>
    <head>
    <style>
        table {{
            width: 80%;
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 0.9em;
            font-family: sans-serif;
            min-width: 400px;
            box-shadow: 0 0 20px rgba(0,0,0,0.15);
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #dddddd;
        }}
        th {{
            background-color: #009879;
            color: #ffffff;
        }}
        tr:nth-of-type(even) {{
            background-color: #f3f3f3;
        }}
        tr:last-of-type {{
            border-bottom: 2px solid #009879;
        }}
    </style>
    </head>
    <body>
        {report}
    </body>
    </html>
    """


async def format_forecast_report(df: pd.DataFrame, target_email: str) -> str:
    """Formats the filtered forecast data into HTML for sending as an email."""
    filtered_df = df[df['email'] == target_email]
    today = datetime.now().date()
    reports = ""

    for location in filtered_df['loc_name'].unique():
        loc_df = filtered_df[filtered_df['loc_name'] == location]
        loc_df = loc_df[loc_df['forecast_timestamp'].dt.date == today]
        loc_df['forecast_timestamp'] = loc_df['forecast_timestamp'].dt.hour
        loc_df = loc_df[loc_df['forecast_timestamp'] >= 7]
        loc_df = loc_df.sort_values(by='forecast_timestamp', ascending=True)
        loc_df['forecast_timestamp'] = loc_df['forecast_timestamp'].apply(
            format_time)

        aggregated_df = loc_df.groupby('forecast_timestamp').agg({
            'temperature': 'mean',
            'precipitation_prob': 'first',
            'description': 'first'
        }).reset_index()

        aggregated_df['description'] = aggregated_df['description'].apply(
            add_unicode)
        aggregated_df['temperature'] = aggregated_df['temperature'].apply(
            lambda x: round(x, 1))

        html = aggregated_df.rename(columns={
            'forecast_timestamp': 'Hour of Forecast',
            'temperature': 'Temperature (°C)',
            'precipitation_prob': 'Chance of rain (%)',
            'description': 'Weather Description'
        }).to_html(index=False)

        reports += f"<h2>{location}</h2>{html}"
    return format_html(reports)

load_dotenv()
conn = get_db_connection(ENV)
df = prepare_data_frame(conn)
print(df[df['email'] == 'example@example.com']['loc_id_user'].unique())
conn.close()
