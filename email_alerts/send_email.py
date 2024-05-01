"""The main email alert script, calls every other script and sends the emails."""

from os import environ as ENV
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

from create_email_messages import assign_messages_to_recipients
from email_alert_setup import set_up_email_data
from update_alerts import update_all_alert_tables


def send_email(email: str, message: str):
    """Sends an email report of plant sensor faults using AWS SES."""

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
    except ClientError as error:
        print("Could not send email:", error.response['Error']['Message'])
    else:
        print("Email sent! Message ID:", response['MessageId'])


def send_to_each_recipient(config: dict, tables: list[str]) -> None:
    """Gets all the alert information, sorts it and then sends it to all the recipients.
    The function then updates the respective rows to show that the warning has been notified."""

    recipients_alerts = set_up_email_data(config, tables)
    recipients_msg = assign_messages_to_recipients(recipients_alerts, tables)
    for key in recipients_msg:
        if not recipients_msg.get(key):
            continue
        send_email(key, recipients_msg.get(key))
        print(recipients_msg.get(key))
    update_all_alert_tables(config, recipients_alerts)


def handler(event: list[dict], context: dict = None) -> None:
    """AWS Lambda handler to run the script."""

    load_dotenv()
    flood_alert = ENV['FLOOD_WARNING_TABLE']
    air_quality = ENV['AIR_QUALITY_TABLE']
    weather_alert = ENV['WEATHER_WARNING_TABLE']

    send_to_each_recipient(ENV, [weather_alert, air_quality, flood_alert])
