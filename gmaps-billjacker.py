import requests

API_KEY = input("Enter the API Key: ").strip()

streetview_url = "https://maps.googleapis.com/maps/api/streetview?size=600x300&location=46.414382,10.013988&key=" + API_KEY

for i in range (2):
    r = requests.get(streetview_url)
    print(i+1, ":", r)






