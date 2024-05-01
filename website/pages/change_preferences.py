import streamlit as st
from streamlit import session_state
import streamlit as st
from streamlit import session_state
import requests
from hashlib import blake2b
from os import environ as ENV

from dotenv import load_dotenv

USER_URL = "http://18.134.12.20:5000/submit-user"
HEADERS = {'Content-Type': 'application/json'}
st.title('You can update your preferences and add a new location here.')

if session_state.get('is_logged_in') == True:
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
            data = {'location': location, 'email': email, 'name': name,
                    'newsletter': sign_newsletter, 'alerts': sign_alerts, password: hash_password}
            response = requests.post(
                USER_URL, json=data, headers=HEADERS)
            if response.status_code == 200:
                st.success('Details successfully added.', icon="✅")
            else:
                st.error('Something went wrong', icon='🤖')
else:
    st.write('Please sign-in to update your preferences')
