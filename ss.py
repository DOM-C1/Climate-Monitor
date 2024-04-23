from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="climate_tracker")
location = geolocator.geocode("london")
print((location.latitude, location.longitude))
print(location.address)