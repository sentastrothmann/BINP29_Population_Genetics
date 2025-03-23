# Population Genetics Project
## Senta Strothmann
### GitHub access to the project files:
+ https://github.com/sentastrothmann/BINP29_Population_Genetics

# 6. Visualize ancient IBD connections for individuals and populations on a map

## Original datasets
+ ibd220.ibd.v54.1.pub.tsv
+ AADR Annotation 2025.xlsx

## Versions
+ Python 3.9.21
+ packages within Python: installed using conda with conda-forge
    + branca 0.8.1
    + folium 0.19.5
    + pandas 2.2.3
    + streamlit 1.43.1
    + streamlit-folium 0.24.0

## How to run the app
1. Open the terminal
2. Select the path in which the files + scripts are stored
    + neccessary file: IBD_data.tsv
3. Run the streamlit application
    + `streamlit run IBD_app.py`
    + follow the opening prompt to the webbrowser

## Workflow Steps
### Preparation of input 
#### Filtering of the input AADR.xlsx file
+ manual selections of the columns
    + Genetic ID
    + Lat.
    + Long.
    + Group ID
    + Locality 
    + Political Entity
    + Full Date One of two formats. (Format 1) 95.4% CI calibrated radiocarbon age (Conventional Radiocarbon Age BP, Lab number) e.g. 2624-2350
        + renamed into Full Date
+ creation of a new, shortened LocDat.xlsx file with the selected columns

#### Combining the .tsv file with the .xlsx file: combine_files.py
```python

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
```

#### Filtering the resulting unfiltered_IBD_data.tsv file
```bash
# Change mispelled Germany
sed 's/\bGernamy\b/Germany/' unfiltered_IBD_data.tsv > filter1_IBD_data.tsv

# Change the two occurences of China to just China when looking for unique countries
sed 's/\bChina\s*\b/China/' filter1_IBD_data.tsv > filter2_IBD_data.tsv
sed -E 's/\bChinaChina_[^ \t]*/China/g' filter2_IBD_data.tsv > filter3_IBD_data.tsv

# Remove unneccesary information from the time
sed -E 's/\([^)]*//g' filter3_IBD_data.tsv | sed -E 's/\)//g' > IBD_data.tsv
```

### Create the interactive app using streamlit and folium
```python
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import branca.colormap as cm

# Load the data
ibd_tsv = pd.read_csv("IBD_data.tsv", sep="\t")

# Convert to dictionary grouped by "iid1"
ibd_data = ibd_tsv.groupby("iid1", group_keys=False).apply(lambda x: x.to_dict(orient="records")).to_dict()

# Streamlit App Title
st.title("Ancient IBD Connections Map 🌍")

# Instructions for users
st.markdown(
    """
    ## How to Use This Map 🗺️
    
    1. **Select a Country**: Choose a country from the dropdown menu.  
    2. **Pick an Individual**: Once a country is selected, you can choose an individual from that country.  
    3. **Filter by Population (Optional)**: You can refine the results further by selecting a population.  
    4. **View the Connections**: The map will show connections between individuals based on IBD segments.  
    5. **Explore Details**:  
       - Hover over the lines to see the **IBD segment length**.  
       - Click on the markers to view **detailed information** about each individual.  

    ### Notes:
    - **Red Markers** represent the chosen individual, **Blue Markers** represent their connected matches.  
    - The **color of the connecting lines** represents the IBD segment length (Blue → Yellow → Red).  
    - If no connections appear, try selecting a different individual or population.
    """
)

# Extract list of individuals and countries
individuals = sorted(ibd_data.keys())
countries = sorted(ibd_tsv["political_entity_1"].dropna().unique())

# User selection for country
selected_country = st.selectbox("Select a country:", ["All countries"] + countries)

# Filter individuals by country
if selected_country != "All countries":
    filtered_individuals = sorted(
        set(ibd_tsv[ibd_tsv["political_entity_1"] == selected_country]["iid1"].unique().tolist())
    )
else:
    filtered_individuals = individuals

# User selection for individual based on country filter
selected_individual = st.selectbox("Select an individual:", filtered_individuals)

# User selection for population filter (optional)
populations = sorted(set(ibd_tsv["political_entity_1"].dropna().unique()))
selected_population = st.selectbox("Filter by population:", ["All"] + populations)

# Get connections for the selected individual
filtered_data = ibd_data.get(selected_individual, [])

# Convert to DataFrame for filtering
filtered_df = pd.DataFrame(filtered_data)

# Apply population filter if needed
if selected_population != "All":
    filtered_df = filtered_df[
        (filtered_df["political_entity_1"] == selected_population) |
        (filtered_df["political_entity_2"] == selected_population)
    ]

# Ensure no missing "lengthM" values
filtered_df = filtered_df.dropna(subset=["lengthM"])

# Ensure sorted values for colormap
filtered_df = filtered_df.sort_values(by="lengthM")

# Function to check if a value is a valid float (not NaN or invalid)
def is_valid_float(value):
    try:
        return float(value) if not pd.isna(value) else None
    except (ValueError, TypeError):
        return None

# Track invalid entries
invalid_entries = []

# Define a color scale based on IBD segment length
if not filtered_df.empty:
    min_length = filtered_df["lengthM"].min()
    max_length = filtered_df["lengthM"].max()
    if min_length == max_length:
        min_length = 0
    colormap = cm.LinearColormap(["blue", "yellow", "red"], vmin=min_length, vmax=max_length, caption="IBD Segment Length in Morgan (M)")
else:
    colormap = cm.LinearColormap(["blue", "yellow", "red"], vmin=0, vmax=1, caption="IBD Segment Length")

# Create a Folium map centered on the individual's location
if not filtered_df.empty:
    map_center = [filtered_df["latitude_1"].astype(float).mean(), filtered_df["longitude_1"].astype(float).mean()]
else:
    map_center = [0, 0]

m = folium.Map(location=map_center, zoom_start=4)

# Add markers and connections with both tooltips and popups
for _, row in filtered_df.iterrows():
    lat1, lon1, name1 = row["latitude_1"], row["longitude_1"], row["iid1"]
    lat2, lon2, name2 = row["latitude_2"], row["longitude_2"], row["iid2"]
    segment_length = row["lengthM"]

    # Extract locality and time information
    locality1, time1 = row["locality_1"], row["time_1"]
    locality2, time2 = row["locality_2"], row["time_2"]

    # Validate latitude and longitude values
    lat1, lon1, lat2, lon2 = is_valid_float(lat1), is_valid_float(lon1), is_valid_float(lat2), is_valid_float(lon2)

    # Skip row if any coordinate is invalid
    if None in [lat1, lon1, lat2, lon2]:  
        invalid_entries.append(row[["latitude_1", "longitude_1", "latitude_2", "longitude_2"]].to_dict())
        continue  

    # Determine line color based on segment length
    color = colormap(segment_length)

    # Create popup text for each individual
    popup_text_1 = f"<b>ID:</b> {name1}<br><b>Locality:</b> {locality1}<br><b>Time:</b> {time1}"
    popup_text_2 = f"<b>ID:</b> {name2}<br><b>Locality:</b> {locality2}<br><b>Time:</b> {time2}"

    # Add markers with popups
    folium.Marker([lat2, lon2], popup=folium.Popup(popup_text_2, max_width=300), icon=folium.Icon(color="blue")).add_to(m)
    folium.Marker([lat1, lon1], popup=folium.Popup(popup_text_1, max_width=300), icon=folium.Icon(color="red")).add_to(m)

    # Create a PolyLine and add a tooltip with the IBD segment length
    polyline = folium.PolyLine(
        [(lat1, lon1), (lat2, lon2)],
        color=color,
        weight=2.5,
        opacity=0.8
    ).add_to(m)

    # Add a tooltip that shows the IBD segment length when hovering
    polyline.add_child(folium.Tooltip(f"IBD Segment Length: {segment_length} M"))

# Add legend to the map
m.add_child(colormap)

# Display the map in Streamlit
folium_static(m)

# Display a warning if there are invalid entries
if invalid_entries:
    st.warning(f"Skipping {len(invalid_entries)} invalid entries due to NaN coordinates.")
```
