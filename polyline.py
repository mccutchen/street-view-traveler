"""A line-for-line port of Mark McClure's JavaScript polyline decoder:
http://facstaff.unca.edu/mcmcclur/GoogleMaps/EncodePolyline/decode.js
"""

def decode(encoded):
    """Decodes the given polyline string and returns a list of (lat, lng)
    pairs.
    """
    length = len(encoded)
    index = 0
    points = []
    lat = 0
    lng = 0

    while index < length:
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            result |= (b & 0x1f) << shift
            shift += 5
            index += 1
            if b < 0x20:
                break
        dlat = ~(result >> 1) if result & 1 else result >> 1
        lat += dlat

        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            result |= (b & 0x1f) << shift
            shift += 5
            index += 1
            if b < 0x20:
                break
        dlng = ~(result >> 1) if result & 1 else result >> 1
        lng += dlng

        points.append((lat * 1e-5, lng * 1e-5))

    return points
