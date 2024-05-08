"""This app loads the webpage and acts as an API for the RDS."""
from os import environ as ENV

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from utils import get_details_from_post_code
from utils_db import get_db_connection, get_id, setup_user_location, get_value_from_db, \
    check_row_exists, get_locations_for_user, update_loc_assignment, delete_user

app = Flask(__name__)


@app.route('/login', methods=['POST'])
def login_user():
    """This function validates the login of a user."""
    load_dotenv()
    conn = get_db_connection(ENV)
    data = request.json
    email = data['email'].lower()
    password = data['password']
    if not check_row_exists(conn, 'user_details', 'email', email, 'password', password):
        response = jsonify({'error': 'Invalid credentials'})
        response.status_code = 400
        return response
    _id = get_id('user_details', 'email', email, conn)
    name = get_value_from_db('user_details', 'name', _id, 'user_id', conn)
    conn.close()
    response = jsonify({'message': 'Login Successful', 'name': name})
    response.status_code = 200
    return response


@app.route('/submit-user', methods=['POST'])
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
    response = jsonify({'message': 'User location added successfully'})
    response.status_code = 200
    return response


@app.route('/get_details', methods=['POST'])
def get_details():
    """This returns a dataframe for a particular users details."""
    load_dotenv()
    email = request.json['email']
    password = request.json['password']

    try:
        conn = get_db_connection(ENV)
        df = get_locations_for_user(conn, email)
        if check_row_exists(conn, 'user_details', 'email', email, 'password', password):

            if df.empty:
                return jsonify({'message': 'No data found for the provided email'}), 404

            df_json = df.to_json(orient='records')
            return jsonify({'message': 'success', 'df': df_json}), 200
        else:
            return jsonify({'message': 'No data found for those credentials'}), 404

    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500


@app.route('/update_notifs', methods=['POST'])
def update_notifs():
    """Updates the notifications for a user."""
    load_dotenv()
    email = request.json['email']
    password = request.json['password']
    alerts = request.json['alerts']
    reports = request.json['reports']

    conn = get_db_connection(ENV)
    if check_row_exists(conn, 'user_details', 'email', email, 'password', password):
        for dict in alerts:
            _id = dict['id']
            value = dict['value']
            update_loc_assignment(
                conn, 'user_location_id ', _id, 'alert_opt_in', value)
        for dict in reports:
            _id = dict['id']
            value = dict['value']
            update_loc_assignment(
                conn, 'user_location_id ', _id, 'report_opt_in', value)

        return jsonify({'message': 'success'}), 200

    return jsonify({'message': 'No data found for those credentials'}), 404


@ app.route('/delete_user', methods=['POST'])
def del_user():
    """If a user wants to delete their account, they can do so through here."""
    email = request.json['email']
    password = request.json['password']
    load_dotenv()
    conn = get_db_connection(ENV)
    if check_row_exists(conn, 'user_details', 'email', email, 'password', password):
        _id = get_id('user_details', 'email', email, conn)
        delete_user(conn, _id)
        return jsonify({'message': 'success'}), 200
    return jsonify({'message': 'Error deleting user'}), 500


if __name__ == '__main__':
    load_dotenv()
    app.run(host='0.0.0.0')
