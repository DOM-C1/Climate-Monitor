import streamlit as st
import requests

USER_URL = "http://18.133.125.119:5000/submit-user"
LOCATION_URL = "http://18.133.125.119:5000/submit-location"
HEADERS = {'Content-Type': 'application/json'}

st.title('Sign-up for our newsletter')

if st.button('Already a user and want to add a location?'):
    st.subheader('Add a location')
    with st.form(key='location_form'):
        st.write('Already a user? Add a location below')
        email = st.text_input('Email', placeholder='Enter your email')
        postcode = st.text_input(
            'Location - postcode', placeholder='Enter your postcode')
        submit_location = st.form_submit_button('Submit Location')
        if submit_location:
            print('hello')

            data = {'postcode': postcode, 'email': email}
            try:
                response = requests.post(
                    LOCATION_URL, json=data, headers=HEADERS)
                if response.status_code == 200:
                    st.success('Location added successfully!')
                else:
                    st.error(
                        f"Something went wrong! Status code: {response.status_code}")
            except Exception as e:
                st.error(f"An error occurred: {e}")

with st.form(key='user_form'):
    name = st.text_input('Name', placeholder='Enter your name')
    email = st.text_input('Email', placeholder='Enter your email')
    location = st.text_input(
        'Location - Please enter your full postcode', placeholder='e.g. AB12 3CD')
    sign_newsletter = st.checkbox('Sign-up for the daily newsletter')
    sign_alerts = st.checkbox('Sign-up for alerts')
    submit_button = st.form_submit_button('Submit')
