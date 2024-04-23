from flask import Flask, request, render_template
from utils import get_long_lat, get_location_name


app = Flask(__name__)



@app.route('/')
def homepage():
    return render_template('newsletter.html')

@app.route('/submit-email', methods=['POST'])
def submit_email():
    email = request.form['email']
    name = request.form['name']
    return f"Thank you {name} your email {email} has been added to the database! "

@app.route('/location')
def location_page():
    return render_template('location_form.html')

@app.route('/submit-location', methods=['POST'])
def submit_location():
    location_type = request.form['locationType']
    location_value = request.form[location_type]
    if location_type == 'postcode':
        longitude,latitude = get_long_lat(location_value.upper())
        location_name = get_location_name(location_value.upper())
        print(location_name)
    return f"Location submitted: {location_type} - {location_value}"

if __name__ == '__main__':
    app.run(debug=True)

