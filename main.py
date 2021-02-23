'''
This is module that generates a map with twitter friends
'''

from flask import Flask
from flask import render_template, request, redirect
import requests
import json
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderUnavailable
import folium
import os

app = Flask(__name__, template_folder='static')

@app.route('/', methods = ["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get('user_name')
        token = request.form.get('token')
        try:
            data = get_twitter_accounts(name, token)
        except KeyError:
            return render_template("fail.html")

        coords =  get_coordinates(data)
        generate_map(coords, name)

        return render_template(f"{name}_map.html")

    maps = []
    for i in os.listdir('map_generator/static'):
        if i[-9:] == "_map.html":
            maps.append(f"{i}")

    if len(maps) == 0:
        maps = None


    return render_template("index.html", maps=maps)


def get_twitter_response(username: str, bearer_token: str):
    '''
    Get response from twitter with friends
    '''
    base_url = "https://api.twitter.com/"

    url_search = f'{base_url}1.1/friends/list.json'

    search_headers = {
        'Authorization': f'Bearer {bearer_token}',
        "charset": "utf-8"
    }
    search_params = {
        'screen_name': f"@{username}",
        'count': 15
    }

    return requests.get(url_search, headers=search_headers, params=search_params).json()

def get_twitter_accounts(name: str, token: str):
    '''
    Get twitter account
    '''
    friend_locations = {}
    j_file = get_twitter_response(name, token)

    for friend in j_file["users"]:
        if friend['location']:
            friend_locations[friend['screen_name']] = [friend['location']]

    return friend_locations

def get_coordinates(locations: dict):
    '''
    Get coordinated of each location
    '''
    res = {}
    geolocator = Nominatim(user_agent = "friends_map")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds = 0.5)

    for location in locations:
        while True:
            try:
                loc_friend = geolocator.geocode(locations[location][0])

                friend_location = (loc_friend.latitude, loc_friend.longitude)
                res[location] = [locations[location][0], friend_location]

            except (GeocoderUnavailable, AttributeError):
                pass
            break

    return res

def generate_map(locations: list, username: str) -> None:
    '''
    Generate map with markers
    '''
    gen_map = folium.Map(zoom_start=30)

    markers = folium.FeatureGroup(name="Markers")

    for location in locations:
        folium.Marker(location=locations[location][1], popup=location).add_to(markers)

    markers.add_to(gen_map)

    gen_map.add_child(folium.LayerControl())

    gen_map.save(f"map_generator/static/{username}_map.html")

@app.route('/remove')
def remove_map():
    '''
    Remove map
    '''
    maps = request.args.get('maps')
    dirname = os.path.dirname(__file__)
    os.remove(f"{dirname}/static/{maps}")
    return redirect("/")


if __name__ == "__main__":
    app.run("0.0.0.0", 8000, debug=True)
