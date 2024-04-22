data = ['http://environment.data.gov.uk/flood-monitoring/id/floods']
import requests
def fetch_data_with_authentication(url):
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Failed to retrieve data: {response.status_code}"


api_key = "your_api_key_here"


data = fetch_data_with_authentication(data[0])
for item in data['items']:
    print(item.keys())