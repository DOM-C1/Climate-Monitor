import streamlit as st
import requests
from hashlib import blake2b
from os import environ as ENV
from dotenv import load_dotenv
import pandas as pd
load_dotenv()
DETAILS_URL = "http://13.42.32.229:5000/get_details"
LOGIN_URL = "http://13.42.32.229:5000/login"
USER_URL = "http://13.42.32.229:5000/submit-user"
HEADERS = {'Content-Type': 'application/json'}

st.title('Welcome to Our Service!')

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
                    else:
                        st.error('Something went wrong', icon='🤖')
else:
    st.title('Track your locations and change preferences')
if st.session_state.get('is_logged_in'):
    if st.button('Reload Page'):
        st.experimental_rerun()
    if st.session_state.get('is_logged_in') == True:
        data = {'email': st.session_state['email'],
                'password': st.session_state['hash_password']}
        response = requests.post(DETAILS_URL, headers=HEADERS, json=data)
        df = response.json()['df']
        df = pd.read_json(df, orient='records')
        for location in df['loc_name'].unique().tolist():
            alert = df[df['loc_name'] ==
                       location]['report_opt_in'].unique()[0]
            report = alert = df[df['loc_name'] ==
                                location]['report_opt_in'].unique()[0]
            cols = st.columns(3)

            cols[0].write(location)
            alerts = cols[1].checkbox(
                'Sign-up for alerts', key=f"alerts_{location}", value=bool(alert))
            reports = cols[2].checkbox(
                'Sign-up for reports', key=f"reports_{location}", value=bool(report))
            print(reports)
    st.title('Add a location.')

    with st.form(key='user_form'):
        load_dotenv()
        location = st.text_input(
            'Location - Please enter your full postcode', placeholder='e.g. AB12 3CD')
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
                st.success('Details successfully added.', icon="✅")
            else:
                st.error('Something went wrong', icon='🤖')
else:
    st.write('Please sign-in to update your preferences')
