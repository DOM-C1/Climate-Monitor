"""This app loads the webpage and acts as an API for the RDS."""
from os import environ as ENV

from dotenv import load_dotenv
from flask import Flask, request, render_template

from utils import get_long_lat, get_location_name, get_details_from_post_code, get_country, get_county
from utils_db import get_db_connection, add_to_database, get_id


app = Flask(__name__)


@app.route('/')
def homepage():
    """This displays the homepage"""
    return render_template('newsletter.html')


@app.route('/submit-user', methods=['POST'])
def submit_user():
    """When a request is sent, the user name and email is parsed and uploaded
    to the database."""
    email = request.form['email']
    name = request.form['name']
    return f"Thank you {name} your email {email} has been added to the database! "


@app.route('/location')
def location_page():
    """Displays the HTML on the website for the location route."""
    return render_template('location_form.html')


@app.route('/submit-location', methods=['POST'])
def submit_location():
    """When users submit a location, the information gets directed here, where it
    get parsed and uploaded."""
    location_type = request.form['location']
    location_value = request.form[location_type]
    details = get_details_from_post_code(location_value)
    if details['status'] == 200:
        longitude, latitude = get_long_lat(location_value)
        location_name = get_location_name(location_value)
        country = get_country(location_value)
        county = get_county(location_value)
        conn = get_db_connection()
        country_id = get_id('country_id', 'name', county, conn)
        if country_id == -1:
            raise ValueError('Invalid Country')
        county_id = get_id('county', 'name', county)
        if county_id == -1:
            county_data = {'name': county, 'country_id': country}
            add_to_database('county', county_data, conn)
            county_id = get_id('county', 'name', county)
        location_data = {'loc_name': location_name,
                         'country_id': country_id, 'county_id': county_id, 'longitude': longitude, 'latitude': latitude}
        add_to_database('county', location_data, conn)
        conn.close()

    return "USER CREATED"


if __name__ == '__main__':
    load_dotenv()
    app.run(debug=True)
