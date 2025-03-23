# Import the modules
import pandas as pd

# Load files
ibd_file = "ibd220.ibd.v54.1.pub.tsv"
loc_file = "LocDat.xlsx"

ibd_data = pd.read_csv(ibd_file, sep="\t")
loc_data = pd.read_excel(loc_file)

# Rename columns in location data for easier merging
loc_data.rename(columns={
    "Genetic ID": "iid",
    "Lat.": "latitude",
    "Long.": "longitude",
    "Political Entity": "political_entity",
    "Group ID": "group_ID",
    "Locality": "locality",
    "Full Date": "time"
}, inplace=True)

# Ensure IDs are strings and clean up whitespace
loc_data["iid"] = loc_data["iid"].astype(str).str.strip()
ibd_data["iid1"] = ibd_data["iid1"].astype(str).str.strip()
ibd_data["iid2"] = ibd_data["iid2"].astype(str).str.strip()

# Remove duplicates so each iid has only one entry
loc_data = loc_data.drop_duplicates(subset="iid", keep="first")

# Convert location data into a dictionary for fast lookup
loc_dict = loc_data.set_index("iid")[["latitude", "longitude", "political_entity", "group_ID", "locality", "time"]].to_dict(orient="index")

# Lists to store extracted location data
latitude_1, longitude_1, political_entity_1, group_ID_1, locality_1, time_1 = [], [], [], [], [], []
latitude_2, longitude_2, political_entity_2, group_ID_2, locality_2, time_2 = [], [], [], [], [], []

# Iterate over the IBD dataset and match location data
for _, row in ibd_data.iterrows():
    iid1, iid2 = row["iid1"], row["iid2"]

    loc1 = loc_dict.get(iid1, {"latitude": None, "longitude": None, "political_entity": None, "group_ID": None, "locality": None, "time": None})
    latitude_1.append(loc1["latitude"])
    longitude_1.append(loc1["longitude"])
    political_entity_1.append(loc1["political_entity"])
    group_ID_1.append(loc1['group_ID'])
    locality_1.append(loc1['locality'])
    time_1.append(loc1["time"])

    loc2 = loc_dict.get(iid2, {"latitude": None, "longitude": None, "political_entity": None, "group_ID": None, "locality": None, "time": None})
    latitude_2.append(loc2["latitude"])
    longitude_2.append(loc2["longitude"])
    political_entity_2.append(loc2["political_entity"])
    group_ID_2.append(loc2['group_ID'])
    locality_2.append(loc2['locality'])
    time_2.append(loc2["time"])

# Add matched data back to the IBD dataframe
ibd_data["latitude_1"] = latitude_1
ibd_data["longitude_1"] = longitude_1
ibd_data["political_entity_1"] = political_entity_1
ibd_data["group_ID_1"] = group_ID_1
ibd_data["locality_1"] = locality_1
ibd_data["time_1"] = time_1
ibd_data["latitude_2"] = latitude_2
ibd_data["longitude_2"] = longitude_2
ibd_data["political_entity_2"] = political_entity_2
ibd_data["group_ID_2"] = group_ID_2
ibd_data["locality_2"] = locality_2
ibd_data["time_2"] = time_2

# Save the new dataset
output_file = "unfiltered_IBD_data.tsv"
ibd_data.to_csv(output_file, sep="\t", index=False)