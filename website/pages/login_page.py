import streamlit as st
from streamlit import session_state
import requests
from hashlib import blake2b
from os import environ as ENV

from dotenv import load_dotenv

USER_URL = "http://18.134.12.20:5000/submit-user"
HEADERS = {'Content-Type': 'application/json'}

st.title('Login Here!')

with st.form(key='user_form'):
    load_dotenv()
    email = st.text_input('Email', placeholder='Enter your email')
    password = st.text_input('Password')
    hash_password = blake2b(
        key=bytes(ENV['HASH_KEY'], 'utf-8'), digest_size=16)
    hash_password = hash_password.hexdigest()
    submit_button = st.form_submit_button('Submit')
    if submit_button:
        data = {'email': email, password: hash_password}
        response = requests.post(
            USER_URL, json=data, headers=HEADERS)
        if response.status_code == 200:
            st.success('Login Successful', icon="✅")
            st.session_state['is_logged_in'] = True
            session_state['email'] = email
            session_state['hash_password'] = hash_password
        else:
            st.error('Something went wrong', icon='🤖')
