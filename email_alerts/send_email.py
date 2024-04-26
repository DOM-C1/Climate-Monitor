

import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from os import environ as ENV
from dotenv import load_dotenv
import datetime

from create_email_messages import assign_messages_to_recipients
from email_alert_setup import set_up_email_data
from update_alerts import update_all_alert_tables


def send_email(email: str, message: str):
    """sends an email report of plant sensor faults using AWS SES"""
    region = ENV['REGION']
    ses = boto3.client('ses', region_name=region)
    from_email = ENV['SENDER_EMAIL']

    try:
        response = ses.send_email(
            Destination={
                'ToAddresses': [email],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': 'UTF-8',
                        'Data': f'{message}',
                    },
                },
                'Subject': {
                    'Charset': 'UTF-8',
                    'Data': "Weather Alert",
                },
            },
            Source=from_email,
        )
    except ClientError as e:
        print("Error sending email:", e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:", response['MessageId'])


def send_to_each_recipient(config: dict) -> None:

    recipients_alerts = set_up_email_data(config)
    recipients_msg = assign_messages_to_recipients(recipients_alerts)
    for key in recipients_msg.keys():
        send_email(key, recipients_msg.get(key))
    update_all_alert_tables(config, recipients_alerts)


if __name__ == '__main__':
    load_dotenv()
    test_data = {'trainee.nathan.mckittrick@sigmalabs.co.uk': [['weather_alert', 1, 'Severe Warning', 'Liverpool', 'Liverpool City Region', 'UV-index', datetime.datetime(2024, 4, 25, 15, 42), 'Clear Sky', datetime.datetime(2024, 4, 25, 15, 42, 42, 19560), 3.3, '&#x1F506;'], ['weather_alert', 2, 'Alert', 'Liverpool', 'Liverpool City Region', 'UV-index', datetime.datetime(2024, 4, 25, 15, 57), 'Clear Sky', datetime.datetime(2024, 4, 25, 15, 42, 42, 19560), 3.0, '&#x1F506;'], [
        'weather_alert', 3, 'Warning', 'Liverpool', 'Liverpool City Region', 'UV-index', datetime.datetime(2024, 4, 25, 16, 12), 'Mainly Clear', datetime.datetime(2024, 4, 25, 15, 42, 42, 19560), 2.75, '&#x1F506;'], ['weather_alert', 4, 'Alert', 'Liverpool', 'Liverpool City Region', 'UV-index', datetime.datetime(2024, 4, 25, 16, 27), 'Partly Cloudy', datetime.datetime(2024, 4, 25, 15, 42, 42, 19560), 2.55, '&#x1F506;'], ['air_quality', 1, 'Alert', 'Liverpool', 'Liverpool City Region', 102], ['flood_warnings', 1, 'Warning', 'Liverpool', 'Liverpool City Region', datetime.datetime(2024, 4, 25, 15, 42)]]
    }
    send_to_each_recipient(ENV)
