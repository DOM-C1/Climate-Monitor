"""This app loads the webpage and acts as an API for the RDS."""
from os import environ as ENV

from dotenv import load_dotenv
from flask import Flask, request, render_template

from utils import get_details_from_post_code
from utils_db import get_db_connection, get_id, setup_user_location, get_value_from_db


app = Flask(__name__)


@app.route('/')
def homepage():
    """This displays the homepage"""
    return render_template('newsletter.html')


@app.route('/submit-location', methods=['POST'])
def submit_user():
    """When a request is sent, the users new location is sent to the database."""
    email = request.form['email']
    postcode = request.form['postcode']
    details = get_details_from_post_code(postcode)
    conn = get_db_connection(ENV)
    user_id = get_id('user_details', 'email', email, conn)
    if user_id == -1:
        return render_template('user_not_found.html')

    if details['status'] != 200:
        return render_template('cant_be_found_page.html')
    alert_on = get_value_from_db(
        'user_location_assignment', 'alert_opt_in', user_id, 'user_id', conn)
    report_on = get_value_from_db(
        'user_location_assignment', 'report_opt_in', user_id, 'user_id', conn)
    name = get_value_from_db(
        'user_details', 'name', user_id, 'user_id', conn)
    setup_user_location(details, name, email, report_on, alert_on, conn)
    return 'Location added!'


@app.route('/location')
def location_page():
    """Displays the HTML on the website for the location route."""
    return render_template('location_form.html')


@app.route('/submit-user', methods=['POST'])
def submit_location():
    """When a user signs-up, it gets sent through here and uploaded
       to the database."""
    location_value = request.form['location']
    name = request.form['name']
    email = request.form['email']
    sub_newsletter = request.form.get('newsletter', 'off') == 'on'
    sub_alerts = request.form.get('alerts', 'off') == 'on'
    details = get_details_from_post_code(location_value)
    conn = get_db_connection()
    if details['status'] == 200:
        setup_user_location(details, name, email,
                            sub_newsletter, sub_alerts, conn)
    return render_template('cant_be_found_page.html')


if __name__ == '__main__':
    load_dotenv()
    app.run(debug=True)
