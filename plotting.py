import math
from traffic.core import Traffic
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from geopy.distance import geodesic
import os
from shapely.geometry import Point
from geopy.distance import great_circle
from trajectories import sfo_lat, sfo_lon, alwys_three, \
    bdega_four, dyamd_five, pirat_three, risti_one, \
    serfr_four, stlr_four, wwavs_two, yosem_three, iafs

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
# filter flights to only points between two given fixes
def filter_near_fix(flight_list, fix1, fix2, radius_nm=2):

    result = []

    radius_deg = radius_nm/60

    for flight in flight_list:
        flight_df = flight.data

        flight_df = flight_df.copy()
        flight_df["dist_to_1"] = ((flight_df["latitude"] - fix1[0])**2 + (flight_df["longitude"] - fix1[1])**2)**0.5
        flight_df["dist_to_2"] = ((flight_df["latitude"] - fix2[0])**2 + (flight_df["longitude"] - fix2[1])**2)**0.5
        
        near1 = flight_df[flight_df["dist_to_1"] <= radius_deg]
        if near1.empty:
            continue
        start_idx = near1.index[0]

        after1 = flight_df.loc[start_idx:]
        near2 = after1[after1["dist_to_2"] <= radius_deg]

        if near2.empty:
            continue

        end_idx = near2.index[0]

        trimmed_df = flight_df.loc[start_idx:end_idx]
        if len(trimmed_df) > 1:
            result.append(Traffic(trimmed_df))

    return result
#---------------------------------------------------------------
# change current directory
os.chdir("/Users/nathanxue22/SFO_Trajectories/cartes")

# read csv into dataframe
#df = pd.read_csv("SFO_arrivals_full.csv", parse_dates=["timestamp"])
#df = pd.read_csv("sfo_arrivals_20240101.csv", names=["icao24", "unix", "latitude", "longitude", "callsign"])
#df["timestamp"] = pd.to_datetime(df["unix"], unit="s")
#print(df.head())
'''
df = pd.read_csv("filtered_flights.csv", parse_dates=["timestamp"])
flights = Traffic(df)



# define relevant columns
cols = ["timestamp", "latitude", "longitude"]


# filter to only flights on 12/22
df = df[df["timestamp"].dt.date == datetime(2024, 12, 22).date()]

print("Removing NaNs...")
# remove NaNs
flights = df.groupby("icao24").filter(
    lambda group: group[cols].notna().all().all()
)

print("Filtering data...")
# filter data to within a defined radius of SFO
df_filtered = filter_data(df, nm_radius)
flights = Traffic(df_filtered)
#print(flights.data.head())

# ---------------------------------------------------------------
'''
df = pd.read_csv("DYAMD_ARCHI.csv", parse_dates=["timestamp"])
flights = Traffic(df)
flight_objects = []

# define relevant columns
cols = ["timestamp", "latitude", "longitude"]

# split flights into individual trajectories
print("Splitting into individual trajectories...")
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

# filter to only flights between two specified fixes
filtered_flights = filter_near_fix(flight_objects, (37.699161, -120.404428), (37.490797, -121.875542))
print(f"Number of flights: {len(filtered_flights)}")

# combine flights into one traffic object for plotting
combined_df = pd.concat([flight.data for flight in filtered_flights], ignore_index=True)
flights = Traffic(df)
#flights.data.to_csv("DYAMD_ARCHI.csv", index=False)

# -------------------------------------------------------
# PLOTTING FIGURE 1
print("Plotting...")
# plotting formatting
fig = plt.figure(figsize=(15, 9), facecolor="black")
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_facecolor("black")
#ax.set_extent([-127.2, -117.3, 33, 42.5])
ax.set_extent([-126, -117.3, 36, 39.5])
#ax.set_extent([-132.2, -112.3, 28, 47.5])
ax.coastlines(linewidth=0.5, color="white", alpha=0.7)
gl = ax.gridlines(draw_labels=True, color="white", alpha=0.4)
ax.set_title("SFO Arrivals", color="white")
gl.top_labels = False
gl.right_labels = False
gl.xlabel_style = {"color": "white"}
gl.ylabel_style = {"color": "white"}

# plot SFO
ax.plot(sfo_lon, sfo_lat, marker="*", color="red", transform=ccrs.PlateCarree())
ax.text(sfo_lon, sfo_lat+0.05, "SFO", color="red", fontsize=12)

# plot flights
flights.plot(ax, linewidth=0.5, alpha=0.8, color="blue")

# plot all fixes
for dict in [alwys_three, bdega_four, dyamd_five, pirat_three, risti_one, serfr_four, stlr_four, wwavs_two, yosem_three, iafs]:
    for coords in dict.values():
        if dict != iafs:
            ax.plot(coords[1], coords[0], marker="o", color="white", alpha=0.6, markersize=3, transform=ccrs.Geodetic())
        else:
            ax.plot(coords[1], coords[0], marker="^", color="white", alpha=0.6, markersize=3, transform=ccrs.Geodetic())

# ---------------------------------------------------------------
# plot paths
plot_line(ax, alwys_three, "INYOE", "DYAMD")
plot_line(ax, alwys_three, "RUSME", "DYAMD")
plot_line(ax, alwys_three, "DYAMD", "LAANE")
plot_line(ax, alwys_three, "LAANE", "ALWYS")
plot_line(ax, alwys_three, "ALWYS", "HEFLY")
plot_line(ax, alwys_three, "HEFLY", "ARRTU")
plot_line(ax, alwys_three, "ARRTU", "ADDMM")
plot_line(ax, alwys_three, "ADDMM", "COGGR")
plot_line(ax, alwys_three, "COGGR", "BERKS")

plot_line(ax, bdega_four, "AMAKR", "QUINN")
plot_line(ax, bdega_four, "QUINN", "BGGLO")
plot_line(ax, bdega_four, "MLBEC", "JONNE")
plot_line(ax, bdega_four, "JONNE", "BGGLO")
plot_line(ax, bdega_four, "MRRLO", "MSCAT")
plot_line(ax, bdega_four, "MSCAT", "BGGLO")
plot_line(ax, bdega_four, "LEGGS", "PYLLE")
plot_line(ax, bdega_four, "PYLLE", "BGGLO")
plot_line(ax, bdega_four, "BGGLO", "LOZIT")
plot_line(ax, bdega_four, "LOZIT", "BDEGA")
plot_line(ax, bdega_four, "BDEGA", "CORKK")
plot_line(ax, bdega_four, "CORKK", "BRIXX")

plot_line(ax, dyamd_five, "DYAMD", "LAANE")
plot_line(ax, dyamd_five, "LAANE", "ALWYS")
plot_line(ax, dyamd_five, "ALWYS", "FLOWZ")
plot_line(ax, dyamd_five, "FLOWZ", "CEDES")
plot_line(ax, dyamd_five, "CEDES", "FRELY")
plot_line(ax, dyamd_five, "FRELY", "ARCHI")

plot_line(ax, pirat_three, "PAINT", "SUPER")
plot_line(ax, pirat_three, "WUSES", "SUPER")
plot_line(ax, pirat_three, "ALCOA", "SUPER")
plot_line(ax, pirat_three, "SUPER", "PASIF")
plot_line(ax, pirat_three, "CINNY", "HUNTS")
plot_line(ax, pirat_three, "HUNTS", "PASIF")
plot_line(ax, pirat_three, "PASIF", "PIRAT")
plot_line(ax, pirat_three, "PIRAT", "BRINY")
plot_line(ax, pirat_three, "BRINY", "ARGGG")

plot_line(ax, risti_one, "ORRCA", "HAIRE")
plot_line(ax, risti_one, "HAIRE", "BYRON")
plot_line(ax, risti_one, "BYRON", "TRACY")
plot_line(ax, risti_one, "TRACY", "MOVDD")
plot_line(ax, risti_one, "TIPRE", "OOWEN")
plot_line(ax, risti_one, "OOWEN", "MOVDD")
plot_line(ax, risti_one, "MOVDD", "RISTI")
plot_line(ax, risti_one, "RISTI", "CEDES")

plot_line(ax, serfr_four, "SERFR", "NRRLI")
plot_line(ax, serfr_four, "NRRLI", "WWAVS")
plot_line(ax, serfr_four, "WWAVS", "EPICK")
plot_line(ax, serfr_four, "EPICK", "FOLET")
plot_line(ax, serfr_four, "FOLET", "EDDYY")

plot_line(ax, stlr_four, "LOZIT", "STLER")
plot_line(ax, stlr_four, "STLER", "PDROW")
plot_line(ax, stlr_four, "STLER", "WESLA")
plot_line(ax, stlr_four, "WESLA", "MVRKK")

plot_line(ax, wwavs_two, "WWAVS", "WPOUT")
plot_line(ax, wwavs_two, "WPOUT", "PLLAR")
plot_line(ax, wwavs_two, "WPOUT", "THEEZ")
plot_line(ax, wwavs_two, "THEEZ", "WESLA")

plot_line(ax, yosem_three, "YOSEM", "SNORA")
plot_line(ax, yosem_three, "SNORA", "ZOMER")
plot_line(ax, yosem_three, "ZOMER", "FRIGG")
plot_line(ax, yosem_three, "FRIGG", "SOOIE")
plot_line(ax, yosem_three, "SOOIE", "FAITH")
#----------------------------------------------------------------
# OUTPUT
plt.show()
# ---------------------------------------------------------------