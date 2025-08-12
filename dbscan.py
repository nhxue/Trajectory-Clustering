import pandas as pd
import numpy as np
from traffic.core import Traffic
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import matplotlib.gridspec as gridspec
from trajectories import sfo_lat, sfo_lon, dyamd_five

#--------------------------------------------------
# get coordinates from Traffic objects
def extract_coords(trajectory, n_points=800):
    traj_df = trajectory.data.dropna(subset=["latitude", "longitude"])

    traj_df = traj_df.sort_values("timestamp")
    latitudes = np.interp(np.linspace(0, len(traj_df)-1, n_points), np.arange(len(traj_df)), traj_df["latitude"].values)
    longitudes = np.interp(np.linspace(0, len(traj_df)-1, n_points), np.arange(len(traj_df)), traj_df["longitude"].values)
    
    return np.hstack([latitudes, longitudes])
#--------------------------------------------------
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
#--------------------------------------------------

# read csv
print("Reading CSV...")
df = pd.read_csv("DYAMD_ARCHI.csv", parse_dates=["timestamp"])
flights = Traffic(df)

# define relevant columns
cols = ["timestamp", "latitude", "longitude"]

flight_objects = []

# split into individual trajectories
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

# DBSCAN Clustering
# -------------------------------------------------------------
# build feature matrix
features = []
valid_flights = []

print("Extracting coordinates...")
for flight in flight_objects:
    feat = extract_coords(flight)
    if feat is not None:
        features.append(feat)
        valid_flights.append(flight)

X = np.vstack(features)

print("Running DBSCAN...")
db = DBSCAN(eps=1, min_samples=3).fit(X)
labels = db.labels_

# assign label to each trajectory
for flight, label in zip(valid_flights, labels):
    flight.cluster_label = label

# get list of unique labels and determine number of clusters used
unique_labels = sorted([label for label in set(labels) if label != -1])
n_clusters = len(unique_labels)

# -------------------------------------------------------------
# Plotting (2 rows, 3 on top row and 2 on bottom row, assuming 5 clusters)
print("Plotting...")
fig = plt.figure(figsize=(15, 10), facecolor="black")
gs = gridspec.GridSpec(2, 3, height_ratios=[1,1])
fig.subplots_adjust(hspace=0.1, wspace=0.1)  # hspace = vertical space, wspace = horizontal space

axes = []

# manually add subplots
for i in range(3):
    axes.append(fig.add_subplot(gs[0, i], projection=ccrs.PlateCarree()))
for i in range(2):
    axes.append(fig.add_subplot(gs[1, i], projection=ccrs.PlateCarree()))

# plot trajectory in appropriate subplot
for i, cluster_id in enumerate(unique_labels):
    if i >= len(axes):
        print("Warning: More clusters than subplots")
        break
    
    cluster_flights = [flight for flight in valid_flights if flight.cluster_label == cluster_id]
    ax = axes[i]
    ax.set_title(f"Cluster {cluster_id+1} ({len(cluster_flights)} Trajectories)", color="white")
    ax.set_facecolor("black")
    ax.set_extent([-122.5, -120, 37.2, 38])
    ax.coastlines(linewidth=0.5, color="white", alpha=0.7)
    gl = ax.gridlines(draw_labels=True, color="white", alpha=0.3)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"color": "white"}
    gl.ylabel_style = {"color": "white"}

    for flight in cluster_flights:
        flight.plot(ax=ax, color=f"C{i}", alpha=0.7)

    # plot fixes
    for coords in dyamd_five.values():
        ax.plot(coords[1], coords[0], marker="o", color="white", alpha=0.6, markersize=3, transform=ccrs.Geodetic())

    # plot lines between fixes
    plot_line(ax, dyamd_five, "DYAMD", "LAANE")
    plot_line(ax, dyamd_five, "LAANE", "ALWYS")
    plot_line(ax, dyamd_five, "ALWYS", "FLOWZ")
    plot_line(ax, dyamd_five, "FLOWZ", "CEDES")
    plot_line(ax, dyamd_five, "CEDES", "FRELY")
    plot_line(ax, dyamd_five, "FRELY", "ARCHI")

    # plot SFO
    ax.plot(sfo_lon, sfo_lat, marker="*", color="red", transform=ccrs.PlateCarree())
    ax.text(sfo_lon, sfo_lat+0.05, "SFO", color="red", fontsize=12)
    
plt.tight_layout()
plt.show()

# plotting all trajectories on one plot
'''
fig, ax = plt.subplots(figsize=(12, 10), facecolor="black",
                       subplot_kw={'projection': ccrs.PlateCarree()})

ax.set_facecolor("black")
ax.set_extent([-122.5, -120, 37.2, 38])
ax.coastlines(linewidth=0.5, color="white", alpha=0.7)
gl = ax.gridlines(draw_labels=True, color="white", alpha=0.4)
gl.top_labels = False
gl.right_labels = False
gl.xlabel_style = {"color": "white"}
gl.ylabel_style = {"color": "white"}

for flight in valid_flights:
    label = getattr(flight, 'cluster_label', -1)
    color = "gray" if label == -1 else f"C{label%10}"
    flight.plot(ax=ax, color=color, alpha=0.5, linewidth=1)

# plot fixes
for coords in dyamd_five.values():
    ax.plot(coords[1], coords[0], marker="o", color="white", alpha=0.6, markersize=3, transform=ccrs.Geodetic())

# plot lines between fixes
plot_line(ax, dyamd_five, "DYAMD", "LAANE")
plot_line(ax, dyamd_five, "LAANE", "ALWYS")
plot_line(ax, dyamd_five, "ALWYS", "FLOWZ")
plot_line(ax, dyamd_five, "FLOWZ", "CEDES")
plot_line(ax, dyamd_five, "CEDES", "FRELY")
plot_line(ax, dyamd_five, "FRELY", "ARCHI")

# plot SFO
ax.plot(sfo_lon, sfo_lat, marker="*", color="red", transform=ccrs.PlateCarree())
ax.text(sfo_lon, sfo_lat+0.05, "SFO", color="red", fontsize=12)

plt.show()
'''

