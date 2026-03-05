"""
TRMNL Solar System Viewer — Vercel Serverless Function

Shows real-time planet positions around the Sun using Keplerian orbital mechanics.
No external API needed — positions computed from NASA/JPL orbital elements.
"""

from http.server import BaseHTTPRequestHandler
import json
import math
from datetime import datetime, timezone

# NASA/JPL Keplerian elements for approximate planetary positions
# Source: https://ssd.jpl.nasa.gov/planets/approx_pos.html
# Format: [value_at_J2000, rate_per_century]
PLANETS = {
    "Mercury": {
        "a": [0.38709927, 0.00000037],
        "e": [0.20563593, 0.00001906],
        "L": [252.25032350, 149472.67411175],
        "w_bar": [77.45779628, 0.16047689],
        "Omega": [48.33076593, -0.12534081],
    },
    "Venus": {
        "a": [0.72333566, 0.00000390],
        "e": [0.00677672, -0.00004107],
        "L": [181.97909950, 58517.81538729],
        "w_bar": [131.60246718, 0.00268329],
        "Omega": [76.67984255, -0.27769418],
    },
    "Earth": {
        "a": [1.00000261, 0.00000562],
        "e": [0.01671123, -0.00004392],
        "L": [100.46457166, 35999.37244981],
        "w_bar": [102.93768193, 0.32327364],
        "Omega": [0.0, 0.0],
    },
    "Mars": {
        "a": [1.52371034, 0.00001847],
        "e": [0.09339410, 0.00007882],
        "L": [-4.55343205, 19140.30268499],
        "w_bar": [-23.94362959, 0.44441088],
        "Omega": [49.55953891, -0.29257343],
    },
    "Jupiter": {
        "a": [5.20288700, -0.00011607],
        "e": [0.04838624, -0.00013253],
        "L": [34.39644051, 3034.74612775],
        "w_bar": [14.72847983, 0.21252668],
        "Omega": [100.47390909, 0.20469106],
    },
    "Saturn": {
        "a": [9.53667594, -0.00125060],
        "e": [0.05386179, -0.00050991],
        "L": [49.95424423, 1222.49362201],
        "w_bar": [92.59887831, -0.41897216],
        "Omega": [113.66242448, -0.28867794],
    },
    "Uranus": {
        "a": [19.18916464, -0.00196176],
        "e": [0.04725744, -0.00004397],
        "L": [313.23810451, 428.48202785],
        "w_bar": [170.95427630, 0.40805281],
        "Omega": [74.01692503, 0.04240589],
    },
    "Neptune": {
        "a": [30.06992276, 0.00026291],
        "e": [0.00859048, 0.00005105],
        "L": [-55.12002969, 218.45945325],
        "w_bar": [44.96476227, -0.32241464],
        "Omega": [131.78422574, -0.00508664],
    },
}

PLANET_SYMBOLS = {
    "Mercury": "\u263f", "Venus": "\u2640", "Earth": "\u2641", "Mars": "\u2642",
    "Jupiter": "\u2643", "Saturn": "\u2644", "Uranus": "\u2645", "Neptune": "\u2646",
}


def julian_centuries_since_j2000():
    now = datetime.now(timezone.utc)
    a = (14 - now.month) // 12
    y = now.year + 4800 - a
    m = now.month + 12 * a - 3
    jd = (now.day + (153 * m + 2) // 5 + 365 * y
           + y // 4 - y // 100 + y // 400 - 32045)
    jd += (now.hour - 12) / 24.0 + now.minute / 1440.0 + now.second / 86400.0
    return (jd - 2451545.0) / 36525.0


def solve_kepler(M_deg, e):
    M = math.radians(M_deg)
    E = M
    for _ in range(50):
        dE = (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
        E -= dE
        if abs(dE) < 1e-8:
            break
    return E


def compute_planet(name, elems, T):
    a = elems["a"][0] + elems["a"][1] * T
    e = elems["e"][0] + elems["e"][1] * T
    L = elems["L"][0] + elems["L"][1] * T
    w_bar = elems["w_bar"][0] + elems["w_bar"][1] * T
    Omega = elems["Omega"][0] + elems["Omega"][1] * T

    M = ((L - w_bar + 180) % 360) - 180
    E = solve_kepler(M, e)

    x_orb = a * (math.cos(E) - e)
    y_orb = a * math.sqrt(1 - e * e) * math.sin(E)

    w = math.radians(w_bar - Omega)
    Omega_rad = math.radians(Omega)

    x_ecl = x_orb * math.cos(w) - y_orb * math.sin(w)
    y_ecl = x_orb * math.sin(w) + y_orb * math.cos(w)

    x = x_ecl * math.cos(Omega_rad) - y_ecl * math.sin(Omega_rad)
    y = x_ecl * math.sin(Omega_rad) + y_ecl * math.cos(Omega_rad)

    dist = math.sqrt(x * x + y * y)
    angle = math.degrees(math.atan2(y, x)) % 360

    # Clock position (1-12) for intuitive display
    clock = int(((90 - angle) % 360) / 30) + 1
    if clock > 12:
        clock = 12

    # Compass direction
    dirs = ["E", "ENE", "NE", "NNE", "N", "NNW", "NW", "WNW",
            "W", "WSW", "SW", "SSW", "S", "SSE", "SE", "ESE"]
    direction = dirs[int(((angle + 11.25) % 360) / 22.5)]

    return {
        "name": name,
        "symbol": PLANET_SYMBOLS.get(name, ""),
        "distance": f"{dist:.2f}",
        "angle": f"{angle:.0f}",
        "direction": direction,
        "clock": f"{clock} o'clock",
    }


def build_response():
    T = julian_centuries_since_j2000()
    now = datetime.now(timezone.utc)

    planets = []
    for name, elems in PLANETS.items():
        planets.append(compute_planet(name, elems, T))

    return {
        "planets": planets,
        "count": len(planets),
        "date": now.strftime("%b %d, %Y"),
        "time_utc": now.strftime("%H:%M UTC"),
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            data = build_response()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "s-maxage=3600, stale-while-revalidate=600")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
