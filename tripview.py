import json
import logging
import math
import pprint

import requests
import polyline

MAPS_API_BASE = 'http://maps.googleapis.com/maps/api'

config = {
   #'verbose': sys.stderr
    }


def get_directions(origin, destination):
    """
    http://maps.googleapis.com/maps/api/directions/json?
    origin=117+Henry+St,+New+York, NY 10002&
    destination=Los+Angeles,CA&waypoints=Joplin,MO|Oklahoma+City,OK&
    sensor=false
    """
    params = {
        'origin': origin,
        'destination': destination,
        'sensor': 'false'
        }
    url = MAPS_API_BASE + '/directions/json'
    resp = requests.get(url, params=params, config=config)
    data = json.loads(resp.content)
    return data

def iter_points(directions):
    """A generator that yields each (lat, lng) pair along the given
    directions.
    """
    route = directions['routes'][0]
    for leg in route['legs']:
        for step in leg['steps']:
            points = step['polyline']['points']
            for point in polyline.decode(points):
                yield point

if __name__ == '__main__':
    a = '120 Henry St, New York, NY 10002'
    b = '11 Pike St, New York, NY 10002'
    directions = get_directions(a, b)
    prev_lat, prev_lon = None, None
    for lat, lon in iter_points(directions):
        if None not in (prev_lat, prev_lon):
            lat_d = lat - prev_lat
            lon_d = lon - prev_lon
            try:
                angle = math.degrees(math.atan(lon_d / lat_d))
            except ZeroDivisionError:
                pass
        else:
            angle = None
        print '%s %s (%s)' % (lon, lat, angle)
        prev_lat, prev_lon = lat, lon
