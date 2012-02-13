import json
import math
import os

import requests
import polyline


# Max distance allowed between points before we do linear interpolation
MAX_DISTANCE = 0.00025


def get_directions(origin, destination):
    """Fetches the directions between the two addresses. Example URL:

        http://maps.googleapis.com/maps/api/directions/json?
            origin=117+Henry+St,+New+York, NY 10002&
            destination=Los+Angeles,CA&
            waypoints=Joplin,MO|Oklahoma+City,OK&
            sensor=false
    """
    params = {
        'origin': origin,
        'destination': destination,
        'sensor': 'false'
        }
    return maps_api_request('/directions/json', params)

def iter_points(directions, max_dist=0):
    """A generator that yields each (lat, lon) pair along the given
    directions.

    If max_dist is non-zero, additional points will be linearly-interpolated
    between any two points in the route that are farther than max_dist apart.
    """
    route = directions['routes'][0]
    prev_point = None
    for leg in route['legs']:
        for step in leg['steps']:
            points = step['polyline']['points']
            for point in polyline.decode(points):
                if prev_point and max_dist > 0:
                    # Do we need to interpolate between the previous point and
                    # the current one?
                    dist = distance_between(point, prev_point)
                    if dist > max_dist:
                        steps = math.ceil(dist / max_dist)
                        # Unpack coordinates from our point tuples and do
                        # simple linear interpolation of the lat and long
                        # coordinates individually.
                        next_lat, next_lon = point
                        prev_lat, prev_lon = prev_point
                        lat_dist = next_lat - prev_lat
                        lon_dist = next_lon - prev_lon
                        for i in xrange(int(steps)):
                            cur_lat = prev_lat + (1/steps * lat_dist)
                            cur_lon = prev_lon + (1/steps * lon_dist)
                            yield (cur_lat, cur_lon)
                            prev_lat, prev_lon = cur_lat, cur_lon
                yield point
                prev_point = point

def distance_between((x1, y1), (x2, y2)):
    """Calculates the Euclidean distance between the two points."""
    dx = x1 - x2
    dy = y1 - y2
    return math.hypot(dx, dy)

def get_heading((x1, y1), (x2, y2)):
    """Calculates the heading between the two points."""
    angle = math.degrees(math.atan2(x1-x2, y1-y2)) - 90
    if angle < 0:
        angle += 360
    return angle

def get_frame(point, heading):
    """Fetches a single still for the given point and heading from the
    streetview API. Example URL:

        http://maps.googleapis.com/maps/api/streetview?
            size=600x300&
            location=56.960654,-2.201815&
            heading=250&
            sensor=false

    See http://code.google.com/apis/maps/documentation/streetview/ for more
    info.
    """
    params = {
        'location': '%s,%s' % point,
        'heading': heading,
        'size': '600x300',
        'sensor': 'false',
    }
    return maps_api_request('/streetview', params)

def maps_api_request(path, params={}):
    """Makes a request to the Google Maps API. Will automatically parse
    JSON responses.
    """
    url = 'http://maps.googleapis.com/maps/api/' + path.lstrip('/')
    resp = requests.get(url, params=params)
    assert 200 <= resp.status_code < 300
    if 'application/json' in resp.headers['Content-Type']:
        return json.loads(resp.content)
    return resp.content

if __name__ == '__main__':
    os.system('rm -f *.jpg trip.mp4')
    a = '101 Henry St, New York, NY 10002'
    b = '171 Henry St, New York, NY 10002'
    directions = get_directions(a, b)
    prev_point = None
    for i, point in enumerate(iter_points(directions, MAX_DISTANCE)):
        lon, lat = point
        heading = get_heading(point, prev_point) if prev_point else None
        print '%s %s (%s)' % (lon, lat, heading)
        if heading:
            open('%05d.jpg' % i, 'wb').write(get_frame(point, heading))
        prev_point = point
    os.system('/usr/local/bin/ffmpeg -y -i "%05d.jpg" -sameq trip.mp4')
    os.system('open trip.mp4')