from streamlit import session_state
import streamlit as st
import requests
from os import environ as ENV
import pandas as pd

from dotenv import load_dotenv

DETAILS_URL = "http://13.42.32.229:5000/get_details"
USER_URL = "http://13.42.32.229:5000/submit-user"
HEADERS = {'Content-Type': 'application/json'}
st.title('Track your locations and change preferences')
if st.session_state.get('is_logged_in'):
    if st.button('Reload Page'):
        st.experimental_rerun()
    if st.session_state.get('is_logged_in') == True:
        data = {'email': session_state['email'],
                'password': session_state['hash_password']}
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
        email = session_state['email']
        hash_password = session_state['hash_password']
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
