"""This app loads the webpage and acts as an API for the RDS datanase."""
from os import environ as ENV

from dotenv import load_dotenv
from flask import Flask, request, render_template

from utils import get_long_lat, get_location_name, add_to_databse, get_df, get_db_connection


app = Flask(__name__)


@app.route('/')
def homepage():
    """This displays the homepage"""
    return render_template('newsletter.html')


@app.route('/submit-email', methods=['POST'])
def submit_user(conn):
    """When a request is sent, the user name and email is parsed and uploaded
    to the database."""
    email = request.form['email']
    name = request.form['name']
    conn = get_db_connection(ENV)
    add_to_databse('user', (name, email), conn)
    return f"Thank you {name} your email {email} has been added to the database! "


@app.route('/location')
def location_page():
    """Displays the HTML on the website for the location route."""
    return render_template('location_form.html')


@app.route('/submit-location', methods=['POST'])
def submit_location():
    """When users submit a location, the information gets directed here, where it
    get parsed and uploaded."""
    df = get_df()
    location_type = request.form['locationType']
    location_value = request.form[location_type]
    if location_type == 'postcode':
        longitude, latitude = get_long_lat(location_value.upper(), df)
        location_name = get_location_name(location_value.upper(), df)
        conn = get_db_connection(ENV)
        add_to_databse('location', (location_name, longitude, latitude), conn)
    return f"Location submitted: {location_type} - {location_value}"


if __name__ == '__main__':
    load_dotenv()
    app.run(debug=True)
