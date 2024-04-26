"""The main email alert script, calls every other script and sends the emails"""

from os import environ as ENV
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

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
    except ClientError as error:
        print("Error sending email:", error.response['Error']['Message'])
    else:
        print("Email sent! Message ID:", response['MessageId'])


def send_to_each_recipient(config: dict) -> None:
    """Gets all the alert information, sorts it and then sends it to all the recipients.
    The function then updates the respective rows to show that the warning has been notified."""

    recipients_alerts = set_up_email_data(config)
    recipients_msg = assign_messages_to_recipients(recipients_alerts)
    for key in recipients_msg:
        send_email(key, recipients_msg.get(key))
    update_all_alert_tables(config, recipients_alerts)


if __name__ == '__main__':
    load_dotenv()
    send_to_each_recipient(ENV)
