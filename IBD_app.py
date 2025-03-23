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