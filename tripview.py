#!/usr/bin/env python

import json
import math
import os
import sys
import urllib

import polyline


# All maps requests start here
MAPS_API_URL = 'http://maps.googleapis.com/maps/api'

# Max distance allowed between points before we do linear interpolation
MAX_DISTANCE = 0.00025


def get_route(a, b):
    """Fetches the directions between the two addresses for point A and point
    B. Example URL:

        http://maps.googleapis.com/maps/api/directions/json?
            origin=117+Henry+St,+New+York, NY 10002&
            destination=Los+Angeles,CA&
            sensor=false
    """
    params = {
        'origin': a,
        'destination': b,
        'sensor': 'false'
        }
    status, body = http_req('GET', MAPS_API_URL + '/directions/json', params)
    assert 200 <= status <= 299, 'HTTP error: %r: %r' % (status, body)
    directions = json.loads(body)
    assert directions['routes'], 'No directions between %r and %r' % (a, b)
    return directions['routes'][0]

def iter_points(route, max_dist=0):
    """A generator that yields each (lat, lon) pair along the given route.

    If max_dist is non-zero, additional points will be linearly-interpolated
    between any two points in the route that are farther than max_dist apart.
    """
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
    angle = math.degrees(math.atan2(x1-x2, y1-y2)) + 90
    return angle + 360 if angle < 0 else angle

def get_frame_url(point, heading):
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
    return MAPS_API_URL + '/streetview?' + urllib.urlencode(params)

def http_req(method, url, params={}):
    """Makes an HTTP request, returning a 2-tuple of (status, body). Only
    makes GET and POST requests because a) fuck Python's HTTP libs and b) I
    didn't want a dependency on the `requests` lib.
    """
    assert method in ('GET', 'POST'), 'Unsupported HTTP method: %s' % method
    if method == 'GET' and params:
        url = url + '?' + urllib.urlencode(params, True)
        params = None
    resp = urllib.urlopen(url, data=params)
    return resp.code, resp.read()

def main(start, end):
    try:
        route = get_route(start, end)
    except Exception, e:
        print >> sys.stderr, 'Error fetching directions: %s' % e
        return 1
    else:
        prev_point = None
        for i, point in enumerate(iter_points(route, MAX_DISTANCE)):
            heading = get_heading(point, prev_point) if prev_point else 0
            url = get_frame_url(point, heading)
            print >> sys.stdout, '%s\t%s' % (i, url)
            prev_point = point
        return 0

if __name__ == '__main__':
    if not len(sys.argv) == 3:
        print >> sys.stderr, """Invalid command. Usage:

    %s start_address end_address
""" % os.path.basename(sys.argv[0])
        sys.exit(1)
    else:
        start, end = sys.argv[1:]
        sys.exit(main(start, end))