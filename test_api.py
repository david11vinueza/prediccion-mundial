import requests

API_KEY = "4c13ad48e7484c4b9dae8d50fea972fa"

url = "https://api.football-data.org/v4/competitions/WC/standings"
headers = {"X-Auth-Token": API_KEY}

r = requests.get(url, headers=headers)
print("Status:", r.status_code)
print("JSON:", r.json())
