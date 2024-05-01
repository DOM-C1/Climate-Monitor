import streamlit as st
import requests

USER_URL = "http://18.134.12.20:5000/submit-user"
HEADERS = {'Content-Type': 'application/json'}

st.title('Sign-up for our newsletter')
st.subheader(
    'Already have an account? Add a location or update your preferences here.')

with st.form(key='user_form'):
    name = st.text_input('Name', placeholder='Enter your name')
    email = st.text_input('Email', placeholder='Enter your email')
    location = st.text_input(
        'Location - Please enter your full postcode', placeholder='e.g. AB12 3CD')
    sign_newsletter = st.checkbox('Sign-up for the daily newsletter')
    sign_alerts = st.checkbox('Sign-up for alerts')
    submit_button = st.form_submit_button('Submit')
    if submit_button:
        data = data = {'location': location, 'email': email, 'name': name,
                       'newsletter': sign_newsletter, 'alerts': sign_alerts}
        response = requests.post(
            USER_URL, json=data, headers=HEADERS)
        if response.status_code == 200:
            st.success('Details successfully added.', icon="✅")
        else:
            st.error('Something went wrong', icon='🤖')
