
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Meerut Restaurant Analytics",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = Path(__file__).parent / "data" / "meerut_restaurants.geojson"


@st.cache_data
def load_restaurants(file_path, modified_time):
    with open(file_path, encoding="utf-8") as file:
        geojson = json.load(file)

    rows = []

    type_labels = {
        "restaurant": "Restaurant",
        "fast_food": "Fast Food",
        "cafe": "Cafe",
        "food_court": "Food Court",
    }

    def get_coordinates(value):
        points = []

        if isinstance(value, list):
            if (
                len(value) >= 2
                and isinstance(value[0], (int, float))
                and isinstance(value[1], (int, float))
            ):
                points.append((value[0], value[1]))
            else:
                for item in value:
                    points.extend(get_coordinates(item))

        return points

    for feature in geojson.get("features", []):
        tags = feature.get("properties") or {}
        name = str(tags.get("name", "")).strip()

        if not name:
            continue

        amenity = tags.get("amenity", "restaurant")
        geometry = feature.get("geometry") or {}
        points = get_coordinates(geometry.get("coordinates", []))

        latitude = None
        longitude = None

        if points:
            longitude = sum(point[0] for point in points) / len(points)
            latitude = sum(point[1] for point in points) / len(points)

        street = tags.get("addr:street", "")

        area = (
            tags.get("addr:suburb")
            or tags.get("addr:neighbourhood")
            or tags.get("addr:district")
            or street
            or tags.get("addr:city")
            or "Area not listed"
        )

        cuisine = tags.get("cuisine", "")
        cuisine = cuisine.replace(";", ",").replace("_", " ").strip()
        cuisine = cuisine.title() if cuisine else "Not listed"

        address_parts = [
            value
            for value in [street, tags.get("addr:city", "Meerut")]
            if value
        ]

        rows.append({
            "Restaurant Name": name,
            "Location": area,
            "Restaurant Type": type_labels.get(
                amenity,
                amenity.replace("_", " ").title(),
            ),
            "Cuisine": cuisine,
            "Address": ", ".join(address_parts),
            "Latitude": latitude,
            "Longitude": longitude,
            "Phone": tags.get(
                "phone",
                tags.get("contact:phone", ""),
            ),
            "Website": tags.get(
                "website",
                tags.get("contact:website", ""),
            ),
            "Opening Hours": tags.get("opening_hours", "Not listed"),
            "Brand": tags.get("brand", ""),
            "OSM ID": tags.get("@id", ""),
        })

    df = pd.DataFrame(rows)

    if not df.empty:
        df = df.drop_duplicates(
            subset=["Restaurant Name", "Location"]
        ).reset_index(drop=True)

    return df


# -------------------- Theme-aware styling --------------------

st.markdown("""
<style>
    /* Follow the active Streamlit theme */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    /* KPI cards */
    [data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        color: var(--text-color);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid var(--text-color);
        border-opacity: 0.15;
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] div,
    [data-testid="stMetricDelta"] {
        color: var(--text-color) !important;
    }

    /* Keep input controls theme-compatible */
    [data-testid="stTextInput"] input,
    [data-testid="stMultiSelect"] input {
        color: var(--text-color);
    }

    /* Charts and tables keep their default theme styling */
    h1, h2, h3 {
        color: var(--text-color);
    }
</style>
""", unsafe_allow_html=True)


# -------------------- Page heading --------------------

st.title("🍽️ Meerut Restaurant Analytics")

st.markdown(
    "Explore mapped restaurants, locations, cuisines and available details."
)


# -------------------- Load data --------------------

if not DATA_FILE.exists():
    st.error(f"Restaurant data file not found: {DATA_FILE}")
    st.info(
        "Place meerut_restaurants.geojson inside the project's data folder."
    )
    st.stop()

try:
    df = load_restaurants(
        str(DATA_FILE),
        DATA_FILE.stat().st_mtime,
    )
except (json.JSONDecodeError, OSError, ValueError) as error:
    st.error(f"Could not load the restaurant data: {error}")
    st.stop()

if df.empty:
    st.warning("No named places were found in the GeoJSON file.")
    st.stop()

st.info(
    "Source: OpenStreetMap contributors. These mapped records are not "
    "a verified complete list of Meerut restaurants. Ratings, reviews "
    "and prices are not included in this dataset."
)


# -------------------- Sidebar filters --------------------

st.sidebar.title("🎛️ Dashboard Filters")
st.sidebar.caption("Choose filters to explore available records.")

locations = sorted(df["Location"].dropna().unique().tolist())
cuisines = sorted(df["Cuisine"].dropna().unique().tolist())
types = sorted(df["Restaurant Type"].dropna().unique().tolist())

selected_locations = st.sidebar.multiselect(
    "Location",
    locations,
    default=locations,
)

selected_cuisines = st.sidebar.multiselect(
    "Cuisine",
    cuisines,
    default=cuisines,
)

selected_types = st.sidebar.multiselect(
    "Restaurant type",
    types,
    default=types,
)

search_text = st.sidebar.text_input("Search restaurant name")

filtered = df[
    df["Location"].isin(selected_locations)
    & df["Cuisine"].isin(selected_cuisines)
    & df["Restaurant Type"].isin(selected_types)
].copy()

if search_text.strip():
    filtered = filtered[
        filtered["Restaurant Name"].str.contains(
            search_text.strip(),
            case=False,
            na=False,
        )
    ]

if st.sidebar.button("Reset filters", use_container_width=True):
    st.rerun()


# -------------------- KPI cards --------------------

total = len(filtered)

with_coordinates = int(
    filtered[["Latitude", "Longitude"]].notna().all(axis=1).sum()
)

with_phone = int(
    filtered["Phone"].fillna("").astype(str).str.strip().ne("").sum()
)

with_cuisine = int(filtered["Cuisine"].ne("Not listed").sum())

k1, k2, k3, k4 = st.columns(4)

k1.metric("Mapped Places", total)
k2.metric("Restaurant Types", filtered["Restaurant Type"].nunique())
k3.metric("With Coordinates", with_coordinates)
k4.metric("With Phone Number", with_phone)

st.divider()

if filtered.empty:
    st.warning("No places match the selected filters. Try widening your search.")
    st.stop()


# -------------------- Overview charts --------------------

st.subheader("📈 Restaurant Overview")

left, right = st.columns(2)

with left:
    type_counts = (
        filtered["Restaurant Type"]
        .value_counts()
        .rename_axis("Restaurant Type")
        .reset_index(name="Places")
    )

    fig = px.bar(
        type_counts,
        x="Restaurant Type",
        y="Places",
        title="Mapped Places by Type",
        text="Places",
        color="Restaurant Type",
    )

    fig.update_layout(
        xaxis_title="Place Type",
        yaxis_title="Number of Places",
    )

    st.plotly_chart(fig, use_container_width=True)

with right:
    cuisine_counts = (
        filtered["Cuisine"]
        .value_counts()
        .head(12)
        .rename_axis("Cuisine")
        .reset_index(name="Places")
    )

    fig = px.bar(
        cuisine_counts.sort_values("Places"),
        x="Places",
        y="Cuisine",
        orientation="h",
        title="Most Common Listed Cuisines",
        text="Places",
    )

    st.plotly_chart(fig, use_container_width=True)


# -------------------- Location-wise analysis --------------------

st.subheader("📊 Location-wise Analysis")

location_summary = (
    filtered.groupby("Location", as_index=False)
    .agg(
        Restaurants=("Restaurant Name", "count"),
        Types=("Restaurant Type", "nunique"),
        Cuisines=("Cuisine", "nunique"),
    )
    .sort_values("Restaurants", ascending=False)
)

left, right = st.columns(2)

with left:
    fig = px.bar(
        location_summary.sort_values("Restaurants"),
        x="Restaurants",
        y="Location",
        orientation="h",
        title="Mapped Places by Location",
        text="Restaurants",
        color="Restaurants",
        color_continuous_scale="Blues",
    )

    fig.update_layout(
        yaxis_title="",
        xaxis_title="Number of Mapped Places",
    )

    st.plotly_chart(fig, use_container_width=True)

with right:
    fig = px.scatter(
        location_summary,
        x="Types",
        y="Cuisines",
        size="Restaurants",
        hover_name="Location",
        title="Location Diversity",
        labels={
            "Types": "Different Place Types",
            "Cuisines": "Different Cuisine Labels",
        },
    )

    st.plotly_chart(fig, use_container_width=True)


# -------------------- Data quality --------------------

st.subheader("🧹 Data Quality")

q1, q2, q3 = st.columns(3)

q1.metric("Places with Coordinates", with_coordinates)
q2.metric("Places with Cuisine Listed", with_cuisine)

with_address = int(
    filtered["Address"].fillna("").str.strip().ne("").sum()
)

q3.metric("Places with Address Listed", with_address)

st.caption(
    "These figures describe the loaded OpenStreetMap records. "
    "They do not measure every restaurant operating in Meerut."
)


# -------------------- Map --------------------

st.subheader("📍 Restaurant Locations")

map_data = filtered.dropna(
    subset=["Latitude", "Longitude"]
).copy()

if not map_data.empty:
    map_data = map_data.rename(
        columns={
            "Latitude": "latitude",
            "Longitude": "longitude",
        }
    )

    st.map(map_data[["latitude", "longitude"]])
else:
    st.info("No usable coordinates are available for these places.")


# -------------------- Restaurant directory --------------------

st.subheader("🔎 Restaurant Directory")

display_columns = [
    "Restaurant Name",
    "Location",
    "Restaurant Type",
    "Cuisine",
    "Address",
    "Phone",
    "Website",
    "Opening Hours",
    "Brand",
]

st.dataframe(
    filtered[display_columns].sort_values("Restaurant Name"),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    f"Showing {len(filtered)} mapped records after applying filters."
)


# -------------------- CSV download --------------------

csv_data = filtered[display_columns].to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="⬇️ Download Filtered Restaurants (CSV)",
    data=csv_data,
    file_name="meerut_restaurants.csv",
    mime="text/csv",
)

st.divider()

st.caption(
    "Data source: © OpenStreetMap contributors. "
    "OpenStreetMap data is available under the Open Database License (ODbL). "
    "Business details may be incomplete or outdated."
)
