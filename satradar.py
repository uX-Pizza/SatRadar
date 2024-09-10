from sgp4.api import Satrec, jday
from astropy import units as u
from astropy.coordinates import TEME, ITRS, CartesianRepresentation, EarthLocation
from astropy.time import Time
from AltAzRange import AltAzimuthRange
import pyproj

import math
import matplotlib.pyplot as plt
import datetime
import json
import time
import requests

filename = "data/orbital_data.json"
selected_group = "noaa"

data = []
data_timestamp = 0

observer_lat = 52.29
observer_lon = 8.91
observer_elevation = 70
alt_az_range = AltAzimuthRange()
alt_az_range.observer(observer_lat, observer_lon, observer_elevation)

geodesic = pyproj.Geod(ellps='WGS84')


def update_orbital_data(group):
    with open(filename, "r") as f:
        contents = json.load(f)
    for i in contents:
        if i["group"] == group:
            if time.time() - i["timestamp"] >= 7200:
                tle_json = []
                print(f"Downloading TLE data for {i['group']}")
                request = requests.get(f'http://celestrak.org/NORAD/elements/gp.php?GROUP={i["group"]}&FORMAT=tle')
                tmp_dict = {}
                for j in request.text.split('\n'):
                    try:
                        if j[0] == '1':
                            tmp_dict['tle_1'] = j.strip()
                        elif j[0] == '2':
                            tmp_dict['tle_2'] = j.strip()
                        else:
                            tmp_dict['satellite_name'] = j.strip()

                        if "tle_1" in tmp_dict and "tle_2" in tmp_dict and "satellite_name" in tmp_dict:
                            tle_json.append(tmp_dict)
                            tmp_dict = {}
                        else:
                            pass
                    except:
                        pass
                i["data"] = tle_json
                i["timestamp"] = time.time()
        with open(filename, "w") as f:
            json.dump(contents, f, indent=2)


def format_year(last_two): # Get full year from last 2 digits
    if int(last_two) > 57:
        return int("19" + f"{last_two}")
    elif int(last_two) < 57:
        return int("20" + f"{last_two}")


def dms2dd(d, m, s): # Convert coordinates from day minute second (dms) format to decimal degree (dd)
    if d[0] == "-":
        dd = int(d) - (int(m)/60) - (float(s)/3600)
    else:
        dd = int(d) + (int(m)/60) + (float(s)/3600)
    return dd


update_orbital_data(selected_group)

def load_orbital_data():
    global data, data_timestamp
    with open(f"{filename}", "r") as file: # Load JSON TLE data
        loaded = json.load(file)
        data = []
        for i in loaded:
            if i["group"] == selected_group:
                data = i["data"]
                data_timestamp = i["timestamp"]
        if not data:
            print(f"No Orbital Data available for group {selected_group}")


load_orbital_data()


fig = plt.figure(dpi=100)
ax = fig.add_subplot(projection='polar')
ax.set_ylim((90, 0))
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)


plt_data = []

while True:
    for sat in data:
        if time.time() - data_timestamp > 7200:
            update_orbital_data(selected_group)
            load_orbital_data()

        line_1 = sat["tle_1"]
        line_2 = sat["tle_2"]
        satellite = Satrec.twoline2rv(line_1, line_2)
        year = format_year(satellite.epochyr)
        jd, fr = jday(datetime.datetime.utcnow().year, datetime.datetime.utcnow().month, datetime.datetime.utcnow().day, datetime.datetime.utcnow().hour, datetime.datetime.utcnow().minute, datetime.datetime.utcnow().second + (datetime.datetime.utcnow().microsecond / 1000000))
        e, r, v = satellite.sgp4(jd, fr)
        date= datetime.datetime.utcnow()
        now = Time(date, scale="utc")
        teme = TEME(CartesianRepresentation(r[0], r[1], r[2], unit=u.km), obstime=now)
        itrs = teme.transform_to(ITRS(obstime=now))
        loc = EarthLocation(*itrs.cartesian.xyz)

        lat_day_split = str(loc.lat).split("d")
        lat_min_split = lat_day_split[1].split("m")
        lat_day = lat_day_split[0]
        lat_min = lat_min_split[0]
        lat_sec = lat_min_split[1].strip("s")
        lon_day_split = str(loc.lon).split("d")
        lon_min_split = lon_day_split[1].split("m")
        lon_day = lon_day_split[0]
        lon_min = lon_min_split[0]
        lon_sec = lon_min_split[1].strip("s")
        lat_dd = dms2dd(lat_day, lat_min, lat_sec)
        lon_dd = dms2dd(lon_day, lon_min, lon_sec)
        alt_az_range.target(lat_dd, lon_dd, float(str(loc.height).strip(" km")) * 1000)
        calc = alt_az_range.calculate()

        try:
            if calc["elevation"] >= 0:
                for i in plt_data:
                    if i["satellite_name"] == sat["satellite_name"]:
                        plt_data.remove(i)
                temp_dict = {"satellite_name": sat['satellite_name'], "azimuth": calc['azimuth'], "elevation": calc['elevation']}
                plt_data.append(temp_dict)
            else:
                for i in plt_data:
                    if sat["satellite_name"] == i["satellite_name"]:
                        print(f"{sat['satellite_name']} dropped below the horizon")
                        plt_data.remove(i)
        except TypeError:
            pass

    for i in plt_data:
        print(i)
        plt.plot(math.radians(i["azimuth"]), i["elevation"], marker=".", color=(0, 0, 0))
        ax.annotate(f"{i['satellite_name']}", xy=(math.radians(i["azimuth"]), i["elevation"]), fontsize=7, horizontalalignment="left", verticalalignment="top")

    ax.set_ylim((90, 0))
    ax.set_theta_direction(-1)
    ax.set_theta_zero_location("N")
    plt.show(block=False)
    plt.pause(0.0001)
    plt.cla()
    plt_azimuth = []
    plt_elev = []