"""Allow the user to sign up, log in and make changes to their account."""

import streamlit as st
import requests
from hashlib import blake2b
from os import environ as ENV
from dotenv import load_dotenv
import pandas as pd
load_dotenv()


DETAILS_URL = "http://3.10.176.50:5000/get_details"
LOGIN_URL = "http://3.10.176.50:5000/login"
USER_URL = "http://3.10.176.50:5000/submit-user"
LOC_URL = "http://3.10.176.50:5000/update_notifs"
DEL_URL = "http://3.10.176.50:5000/delete_user"
HEADERS = {'Content-Type': 'application/json'}

st.title('Here you can find all things user located!')

if not st.session_state.get('is_logged_in'):
    if 'already_signed_up' not in st.session_state:
        st.session_state['already_signed_up'] = False

    if st.button('Already signed up? Click here to Login'):
        st.session_state['already_signed_up'] = True

    if st.button('Need to create an account? Sign up here'):
        st.session_state['already_signed_up'] = False

    if st.session_state['already_signed_up']:
        with st.form(key='login_form'):
            st.subheader('Login Here!')
            email = st.text_input('Email', placeholder='Enter your email')
            password = st.text_input('Password', type='password')
            submit_button = st.form_submit_button('Submit')

            if submit_button and email and password:
                try:
                    hash_key = bytes(ENV['HASH_KEY'], 'utf-8')
                    hash_password = blake2b(
                        key=hash_key, digest_size=16)
                    hash_password.update(bytes(password, 'utf-8'))
                    hashed_output = hash_password.hexdigest()

                    data = {'email': email, 'password': hashed_output}
                    response = requests.post(
                        LOGIN_URL, json=data, headers=HEADERS)

                    if response.status_code == 200:
                        st.success('Login Successful', icon="✅")
                        st.session_state['is_logged_in'] = True
                        st.session_state['email'] = email
                        st.session_state['hash_password'] = hashed_output
                        st.session_state['name'] = response.json()['name']
                        st.rerun()
                    else:
                        st.error(
                            'Login failed. Please check your credentials.', icon='🚫')
                except requests.RequestException as e:
                    st.error(f"Request failed: {str(e)}", icon="🚫")
    else:
        st.subheader('Sign-up for our service or update your details')
        with st.form(key='signup_form'):
            name = st.text_input('Name', placeholder='Enter your name')
            email = st.text_input('Email', placeholder='Enter your email')
            password = st.text_input(
                'Password minimum 8 characters', placeholder='Password', type='password')
            if password:
                hash_key = bytes(ENV['HASH_KEY'], 'utf-8')
                hash_password = blake2b(key=hash_key, digest_size=16)
                hash_password.update(bytes(password, 'utf-8'))
                hash_password = hash_password.hexdigest()

            location = st.text_input(
                'Location - Please enter your full postcode', placeholder='e.g. AB12 3CD')
            sign_newsletter = st.checkbox('Sign-up for the daily newsletter')
            sign_alerts = st.checkbox('Sign-up for alerts')
            submit_button = st.form_submit_button('Submit')

            if submit_button:
                if len(password) < 8:
                    st.error("Please make the password at least 8 characters.")
                else:
                    data = {'location': location, 'email': email, 'name': name,
                            'newsletter': sign_newsletter, 'alerts': sign_alerts, 'password': hash_password}
                    response = requests.post(
                        USER_URL, json=data, headers=HEADERS)
                    if response.status_code == 200:
                        st.success('Details successfully added.', icon="✅")
                        st.session_state['is_logged_in'] = True
                        st.session_state['email'] = email
                        st.session_state['hash_password'] = hash_password
                        st.session_state['name'] = name
                        st.rerun()

                    else:
                        st.error('Something went wrong', icon='🤖')
else:
    with st.sidebar:
        if st.button('Sign Out'):
            st.session_state['is_logged_in'] = False
            st.session_state['email'] = None
            st.session_state['hash_password'] = None
            st.session_state['name'] = None
            st.rerun()

    st.subheader('Track your locations and change preferences')
if st.session_state.get('is_logged_in'):
    data = {'email': st.session_state['email'],
            'password': st.session_state['hash_password']}
    response = requests.post(DETAILS_URL, headers=HEADERS, json=data)
    if response.status_code == 200:
        df = response.json().get('df')
        df = pd.read_json(df, orient='records')
        for location in df['loc_name'].unique():
            location_data = df[df['loc_name'] == location]
            default_alert = location_data['alert_opt_in'].unique()[0]
            default_report = location_data['report_opt_in'].unique()[0]

            cols = st.columns(3)
            cols[0].write(location)

            alert_key = f"alerts_{location}"
            report_key = f"reports_{location}"

            if alert_key not in st.session_state:
                st.session_state[alert_key] = bool(default_alert)
            if report_key not in st.session_state:
                st.session_state[report_key] = bool(default_report)

            alerts = cols[1].checkbox(
                'Sign-up for alerts', key=alert_key)
            reports = cols[2].checkbox(
                'Sign-up for daily newsletter', key=report_key)

        if st.button('Submit Changes'):
            changes = {'alerts': [], 'reports': [
            ], 'email': st.session_state['email'], 'password': st.session_state['hash_password']}
            for location in df['loc_name'].unique():
                location_data = df[df['loc_name'] == location]
                _id = location_data['user_location_id'].tolist()[0]
                alert_value = st.session_state.get(f"alerts_{location}")
                report_value = st.session_state.get(
                    f"daily newsletter_{location}")
                if alert_value:
                    changes['alerts'].append({'id': _id, 'value': alert_value})
                if report_value:
                    changes['reports'].append(
                        {'id': _id, 'value': report_value})
            response = requests.post(
                LOC_URL, json=changes, headers=HEADERS)
            if response.status_code == 200:
                st.success('Details changed successfully.')

            else:
                st.error('Error')
        st.title('Add a location.')

    with st.form(key='user_form'):
        load_dotenv()
        location = st.text_input(
            'Location - Please enter the full postcode', placeholder='e.g. AB12 3CD')
        sign_newsletter = st.checkbox('Sign-up for the daily newsletter')
        sign_alerts = st.checkbox('Sign-up for alerts')
        email = st.session_state['email']
        hash_password = st.session_state['hash_password']
        submit_button = st.form_submit_button('Submit')
        if submit_button:
            data = {'location': location, 'email': email, 'name': st.session_state['name'],
                    'newsletter': sign_newsletter, 'alerts': sign_alerts, 'password': hash_password}
            response = requests.post(
                USER_URL, json=data, headers=HEADERS)
            if response.status_code == 200:
                st.success(
                    'Your preferences have successfully been updated.', icon="✅")
                st.rerun()
            else:
                st.error('Something went wrong', icon='🤖')

    with st.popover('Delete Acount'):
        if st.button('Are you sure you want to delete your account?'):
            data = {'email': st.session_state['email'],
                    'password': st.session_state['hash_password']}
            response = requests.post(DEL_URL, json=data, headers=HEADERS)
            if response.status_code == 200:
                st.success('User deleted successfully')
                st.session_state['is_logged_in'] = False
                st.session_state['email'] = None
                st.session_state['hash_password'] = None
                st.rerun()
            else:
                st.error('Error: Unable to delete user')
else:
    st.write('Please sign-in to update your preferences')
