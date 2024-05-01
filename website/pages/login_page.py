import streamlit as st
import requests
from hashlib import blake2b
from os import environ as ENV

from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

LOGIN_URL = "http://18.170.71.100:5000/login"
HEADERS = {'Content-Type': 'application/json'}

st.title('Login Here!')

with st.form(key='user_form'):
    email = st.text_input('Email', placeholder='Enter your email')
    password = st.text_input('Password', type='password')
    submit_button = st.form_submit_button('Submit')

    if submit_button and email and password:
        try:
            hash_key = bytes(ENV['HASH_KEY'], 'utf-8')
            hash_password = blake2b(
                key=hash_key, digest_size=16)
            hashed_output = hash_password.hexdigest()

            data = {'email': 'trainee.dominic.chambers@sigmalabs.co.uk',
                    'password': 'ccb5ad7b7e3172975f4576e5c5910f50'}
            response = requests.post(LOGIN_URL, json=data, headers=HEADERS)

            if response.status_code == 200:
                st.success('Login Successful', icon="✅")
                st.session_state['is_logged_in'] = True
                st.session_state['email'] = email
                st.session_state['hash_password'] = hashed_output
            else:
                st.error('Login failed. Please check your credentials.', icon='🚫')
        except requests.RequestException as e:
            st.error(f"Request failed: {str(e)}", icon="🚫")
