import streamlit as st
from streamlit import session_state
import requests
from hashlib import blake2b
from os import environ as ENV

from dotenv import load_dotenv

load_dotenv()


USER_URL = "http://18.134.150.116:5000/submit-user"
HEADERS = {'Content-Type': 'application/json'}

st.title('Sign-up for our newsletter')
st.subheader(
    'Already have an account? Add a location or update your preferences here.')

with st.form(key='user_form'):
    name = st.text_input('Name', placeholder='Enter your name')
    email = st.text_input('Email', placeholder='Enter your email')
    password = st.text_input(
        'Password minimum 8 characters', placeholder='password')
    hash_password = blake2b(
        key=bytes(ENV['HASH_KEY'], 'utf-8'), digest_size=16)
    hash_password = hash_password.hexdigest()

    location = st.text_input(
        'Location - Please enter your full postcode', placeholder='e.g. AB12 3CD')
    sign_newsletter = st.checkbox('Sign-up for the daily newsletter')
    sign_alerts = st.checkbox('Sign-up for alerts')

    submit_button = st.form_submit_button('Submit')
    if submit_button:
        if len(password) < 8:
            st.error("Please make the password at least 8 characters.")
        data = {'location': location, 'email': email, 'name': name,
                'newsletter': sign_newsletter, 'alerts': sign_alerts, 'password': hash_password}
        response = requests.post(
            USER_URL, json=data, headers=HEADERS)
        if response.status_code == 200:
            st.success('Details successfully added.', icon="✅")
        else:
            st.error('Something went wrong', icon='🤖')
