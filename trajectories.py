import traffic
import math
import numpy as np
from traffic.core import Traffic
from traffic.data.samples import belevingsvlucht
from traffic.data import opensky
from IPython.display import display
import pandas as pd
from tqdm import tqdm
from datetime import datetime
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from shapely.geometry import Point
from geopy.distance import geodesic
import matplotlib.animation as animation
from IPython.display import HTML
from geopy.distance import distance
from matplotlib.collections import LineCollection
import os

# ---------------------------------------------------------------
# define constants
sfo_lat, sfo_lon = 37.6188, -122.375

date_ranges = [
    ("2024-04-22 17:00", "2024-4-22 20:59"),
    ("2024-08-22 17:00", "2024-8-22 20:59"),
    ("2024-12-22 17:00", "2024-12-22 20:59"),
]
nm_radius = 240
km_radius = nm_radius * 1.852

lat_deg = km_radius / 111
lon_deg = km_radius / (111 * math.cos(math.radians(sfo_lat)))

bounds = (
    sfo_lon - lon_deg,
    sfo_lat - lat_deg,
    sfo_lon + lon_deg,
    sfo_lat + lat_deg,
)

# initial approach fixes (IAFS)
iafs = {
    "ARCHI": (37.490797, -121.875542),  # 28R, 28L
    "SIDBY": (37.450711, -122.144747),  # 28R, 28L
    "EDDYY": (37.374903, -122.118750),  # 28R, 28L
    "FAITH": (37.401217, -121.861900),  # 28L
    "STINS": (37.823678, -122.756683),  # 10R, 10L
    "UPEND": (38.031983, -122.097067)   # 19L, 19R
}
#print(f"Bounds: {bounds}")

# standard terminal arrivals (STARs)
alwys_three = {
    "INYOE": (37.895622, -118.764992), # entry fix
    "RUSME": (37.494167, -117.520000), # entry fix
    "DYAMD": (37.699161, -120.404428),
    "LAANE": (37.658983, -120.747392),
    "ALWYS": (37.633419, -120.959431),
    "HEFLY": (37.682722, -121.224895),
    "ARRTU": (37.733622, -121.502989),
    "ADDMM": (37.770972, -121.708586),
    "COGGR": (37.819536, -121.976144),
    "BERKS": (37.860861, -122.211678)
}

bdega_four = {
    "AMAKR": (39.000000, -123.750000), # entry fix
    "QUINN": (38.515233, -123.132597), # AMAKR
    "MLBEC": (38.874772, -122.958989), # entry fix
    "JONNE": (38.622864, -122.884433), # MLBEC
    "MRRLO": (38.897547, -122.578233), # entry fix
    "MSCAT": (38.623758, -122.655617), # MSCAT
    "LEGGS": (39.336625, -121.095764), # entry fix
    "PYLLE": (38.542158, -122.440536), # LEGGS
    "BGGLO": (38.224589, -122.767506),
    "LOZIT": (37.899325, -122.673194),
    "BDEGA": (37.823025, -122.592200),
    "CORKK": (37.733589, -122.497550),
    "BRIXX": (37.617844, -122.374528)
}

dyamd_five = {
    "INYOE": (37.895622, -118.764992), # entry fix
    "RUSME": (37.494167, -117.520000), # entry fix
    "DYAMD": (37.699161, -120.404428),
    "LAANE": (37.658983, -120.747392),
    "ALWYS": (37.633419, -120.959431),
    "FLOWZ": (37.592519, -121.264750),
    "CEDES": (37.550822, -121.624586),
    "FRELY": (37.510053, -121.795325),
    "ARCHI": (37.490797, -121.875542)  # IAF
}

pirat_three = {
    "PAINT": (38.000000, -125.500000), # entry fix
    "WUSES": (37.655797, -124.001633), # entry fix
    "ALCOA": (37.833253, -125.834525), # entry fix
    "SUPER": (37.302664, -123.812964), # PAINT, WUSES, ALCOA
    "CINNY": (36.181667, -124.760000), # entry fix
    "HUNTS": (36.929167, -123.566667), # CINNY
    "PASIF": (37.193889, -123.133333),
    "PIRAT": (37.257650, -122.863352),
    "BRINY": (37.304761, -122.661656),
    "ARGGG": (37.392422, -122.281630)
}

risti_one = {
    "ORRCA": (38.443658, -121.551622), # entry fix
    "HAIRE": (37.907136, -121.480378), # ORCCA
    "BYRON": (37.823975, -121.469369), # HAIRE
    "TRACY": (37.731439, -121.459303), # BYRON
    "TIPRE": (38.205833, -121.035833), # entry fix
    "OOWEN": (37.707991, -121.274781), # TIPRE
    "MOVDD": (37.661356, -121.448203),
    "RISTI": (37.607014, -121.533278),
    "CEDES": (37.550822, -121.624586)
    }

serfr_four = {
    "SERFR": (36.068306, -121.364664), # entry fix
    "NRRLI": (36.495600, -121.699400),
    "WWAVS": (36.741531, -121.894233),
    "EPICK": (36.950822, -121.952673),
    "FOLET": (37.274781, -122.079294),
    "EDDYY": (37.374903, -122.118750) # IAF
}

stlr_four = {
    "AMAKR": (39.000000, -123.750000), # entry fix
    "QUINN": (38.515233, -123.132597), # AMAKR
    "MLBEC": (38.874772, -122.958989), # entry fix
    "JONNE": (38.622864, -122.884433), # MLBEC
    "MRRLO": (38.897547, -122.578233), # entry fix
    "MSCAT": (38.623758, -122.655617), # MSCAT
    "LEGGS": (39.336625, -121.095764), # entry fix
    "PYLLE": (38.542158, -122.440536), # LEGGS
    "BGGLO": (38.224589, -122.767506),
    "LOZIT": (37.899325, -122.673194),
    "STLER": (37.701364, -122.711064),
    "PDROW": (37.643622, -122.722072), # STLER
    "WESLA": (37.664928, -122.480292), # STLER
    "MVRKK": (37.736972, -122.453339)  # WESLA
}

wwavs_two = {
    "SERFR": (36.068306, -121.364664), # entry fix
    "NRRLI": (36.495600, -121.699400),
    "WWAVS": (36.741531, -121.894233),
    "WPOUT": (37.119486, -122.292742),
    "PLLAR": (37.504386, -122.717667), # WPOUT
    "THEEZ": (37.501863, -122.424197), # WPOUT
    "WESLA": (37.664928, -122.480292), # THEEZ
    "MVRKK": (37.736972, -122.453339)  # WESLA
}

yosem_three = {
    "YOSEM": (37.762742, -118.766611), # entry fix
    "SNORA": (37.645556, -119.806294),
    "ZOMER": (37.545347, -120.631441),
    "FRIGG": (37.465508, -121.257289),
    "SOOIE": (37.428572, -121.607639),
    "FAITH": (37.401217, -121.861900)  # IAF
}

# ---------------------------------------------------------------
# filters data to within a specified radius of SFO
def filter_data(df_original, radius_nm):
    radius_km = radius_nm * 1.852
    
    def is_within_radius(row):
        point = (row['latitude'], row['longitude'])
        try:
            return geodesic((sfo_lat, sfo_lon), point).km <= radius_km
        except ValueError:
            return False
    
    mask = df_original.apply(is_within_radius, axis=1)
    return df_original[mask].copy()
#---------------------------------------------------------------
# plot line between two points
def plot_line(ax, star, fix1, fix2):
    ax.plot([star[fix1][1], star[fix2][1]],
            [star[fix1][0], star[fix2][0]],
            color="white",
            linewidth=1,
            linestyle="-",
            alpha=0.6,
            transform=ccrs.Geodetic()
        )
#---------------------------------------------------------------

# GET LIST OF FLIGHT ICAOS
SFO_flights = []

for start_str, stop_str in tqdm(date_ranges):
    #begin = datetime.fromisoformat(begin_str)
    #end = datetime.fromisoformat(end_str)

    flights = opensky.flightlist(
        start=start_str,
        stop=stop_str,
        arrival_airport="KSFO",
    )

    SFO_flights.append(flights)

df = pd.concat(SFO_flights)

print(f"Fetched {len(df)} flights.")

# ---------------------------------------------------------------
# GET TRAFFIC OBJECTS FROM ALL FLIGHTS IN DEFINED DATA/TIME RANGE
SFO_arrivals = []

for _, row in tqdm(df.iterrows(), total=len(df)):
    try:
        flight = opensky.history(
            icao24=row["icao24"],
            start=row["firstseen"],
            stop=row["lastseen"],
        )

        if flight is not None:
            SFO_arrivals.append(flight)
    
    except Exception as e:
        print(f"Error fetching flight: {e}")


combined_flights = Traffic.from_flights(SFO_arrivals)
combined_flights.data.to_csv("SFO_arrivals_full.csv", index=False)

# ---------------------------------------------------------------
# change current directory
os.chdir("/Users/nathanxue22/SFO_Trajectories/cartes")

# read csv into dataframe
#df = pd.read_csv("SFO_arrivals_full.csv", parse_dates=["timestamp"])
df = pd.read_csv("sfo_arrivals_20240101.csv", names=["icao24", "unix", "latitude", "longitude", "callsign"])
df["timestamp"] = pd.to_datetime(df["unix"], unit="s")
print(df.head())

# define relevant columns
cols = ["timestamp", "latitude", "longitude"]

# filter to only flights on 12/22
#df = df[df["timestamp"].dt.date == datetime(2024, 12, 22).date()]

print("Removing NaNs...")
# remove NaNs
flights = df.groupby("icao24").filter(
    lambda group: group[cols].notna().all().all()
)

print("Filtering data...")
# filter data to within a defined radius of SFO
df_filtered = filter_data(df, nm_radius)
flights = Traffic(df_filtered)
print(flights.data.head())

# ---------------------------------------------------------------

flight_objects = []

print("Removing gaps...")
# iterate over each flight
for icao, group in flights.data.groupby("icao24"):
    # for each flight, sort by time
    group = group.sort_values("timestamp")
    group["time_diff"] = group["timestamp"].diff().dt.total_seconds()
    group["flight_id"] = group["time_diff"].gt(600).cumsum()

    for fid, fgroup in group.groupby("flight_id"):
        fgroup = fgroup.dropna(subset=cols)
        if len(fgroup) > 1:
            # drop flights that have gaps in trajectories (likely errors)
            flight_objects.append(Traffic(fgroup.drop(columns=["time_diff", "flight_id"])))
            #print(f'columns: {flight_objects[0].data.columns}')
