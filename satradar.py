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

observer_lat = 52.29
observer_lon = 8.91
observer_elevation = 70
alt_az_range = AltAzimuthRange()
alt_az_range.observer(observer_lat, observer_lon, observer_elevation)

geodesic = pyproj.Geod(ellps='WGS84')


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


with open("celes_tle.json", "r") as file: # Load JSON TLE data
    data = json.load(file)


fig = plt.figure(dpi=100)
ax = fig.add_subplot(projection='polar')
ax.set_ylim((90, 0))
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)


plt_data = []

while True:
    for sat in data:
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
        # delta_lat = abs(observer_lat - lat_dd)
        # delta_lon = abs(observer_lon - lon_dd)
        # print(lat_dd, lon_dd, loc.height, sat["satellite_name"])
        # fwd_azimuth, back_azimuth, distance = geodesic.inv(observer_lon, observer_lat, lon_dd, lat_dd)
        # slant_range = math.sqrt(distance**2 + (float(str(loc.height).strip(" km")) - observer_elevation)**2)
        # print(fwd_azimuth, slant_range)
        alt_az_range.target(lat_dd, lon_dd, float(str(loc.height).strip(" km")) * 1000)
        calc = alt_az_range.calculate()
        # print(sat["satellite_name"], lat_dd, lon_dd, loc.height)
        try:
            if calc["elevation"] >= 0:
                for i in data:
                    if i["satellite_name"] == sat["satellite_name"]:
                        data.remove(i)
                temp_dict = {"satellite_name": sat['satellite_name'], "azimuth": calc['azimuth'], "elevation": calc['elevation']}
                plt_data.append(temp_dict)
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