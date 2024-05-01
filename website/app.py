"""This app loads the webpage and acts as an API for the RDS."""
from os import environ as ENV

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from utils import get_details_from_post_code
from utils_db import get_db_connection, get_id, setup_user_location, get_value_from_db

app = Flask(__name__)


@app.route('/submit-location', methods=['POST'])
def submit_user():
    """When a request is sent, the users new location is sent to the database."""
    data = request.json
    postcode = data['postcode']
    email = data['email'].lower()
    password = data['password']
    id = get_id('user_details', 'password', password, conn)
    if id == -1:
        response = jsonify({'error': 'Invalid credentials'})
        response.status_code = 400
        return response
    details = get_details_from_post_code(postcode)
    conn = get_db_connection(ENV)
    user_id = get_id('user_details', 'email', email, conn)

    alert_on = get_value_from_db(
        'user_location_assignment', 'alert_opt_in', user_id, 'user_id', conn)
    report_on = get_value_from_db(
        'user_location_assignment', 'report_opt_in', user_id, 'user_id', conn)
    name = get_value_from_db(
        'user_details', 'name', user_id, 'user_id', conn)
    setup_user_location(details, name, email, report_on,
                        alert_on, password, conn)
    return 'Location added!'


@ app.route('/submit-user', methods=['POST'])
def submit_location():
    """When a user signs-up, it gets sent through here and uploaded
       to the database."""
    data = request.json
    location_value = data['location']
    name = data['name']
    email = data['email'].lower()
    sub_newsletter = data['newsletter']
    sub_alerts = data['alerts']
    password = data['password']
    details = get_details_from_post_code(location_value)
    conn = get_db_connection(ENV)
    setup_user_location(details, name, email,
                        sub_newsletter, sub_alerts, password, conn)


if __name__ == '__main__':
    load_dotenv()
    app.run(host='0.0.0.0')
