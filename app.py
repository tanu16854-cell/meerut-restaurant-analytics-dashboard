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
            "Phone": tags.get("phone", tags.get("contact:phone", "")),
            "Website": tags.get("website", tags.get("contact:website", "")),
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
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.8rem;
        padding-bottom: 3rem;
    }

    h1 {
        font-weight: 750 !important;
        letter-spacing: -0.8px;
    }

    h2, h3 {
        font-weight: 650 !important;
    }

    [data-testid="stMetric"] {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 14px;
        padding: 18px 20px;
        min-height: 112px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] div,
    [data-testid="stMetricDelta"] {
        color: var(--text-color) !important;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.18);
    }

    [data-testid="stTextInput"] input {
        color: var(--text-color);
        border-radius: 9px;
    }

    [data-testid="stPlotlyChart"],
    [data-testid="stDataFrame"] {
        border-radius: 12px;
    }

    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    div.stDownloadButton > button,
    div.stButton > button {
        border-radius: 9px;
        font-weight: 600;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        [data-testid="stMetric"] {
            padding: 12px;
            min-height: 95px;
        }
    }
</style>
""", unsafe_allow_html=True)


# -------------------- Page heading --------------------

st.title("🍽️ Meerut Restaurant Analytics")
st.markdown(
    "Explore mapped places, compare locations, and analyse available details."
)


# -------------------- Load data --------------------

if not DATA_FILE.exists():
    st.error(f"Restaurant data file not found: {DATA_FILE}")
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

st.caption(
    "Source: OpenStreetMap contributors. Records may be incomplete or "
    "outdated and are not a verified complete list of Meerut restaurants."
)


# -------------------- Sidebar filters --------------------

st.sidebar.title("🎛️ Dashboard Filters")
st.sidebar.caption("Choose filters to explore the available records.")

locations = sorted(df["Location"].dropna().unique().tolist())
cuisines = sorted(df["Cuisine"].dropna().unique().tolist())
types = sorted(df["Restaurant Type"].dropna().unique().tolist())

selected_locations = st.sidebar.multiselect(
    "Location",
    locations,
    default=locations,
    key="filter_locations",
)

selected_cuisines = st.sidebar.multiselect(
    "Cuisine",
    cuisines,
    default=cuisines,
    key="filter_cuisines",
)

selected_types = st.sidebar.multiselect(
    "Restaurant type",
    types,
    default=types,
    key="filter_types",
)

search_text = st.sidebar.text_input(
    "Search restaurant name",
    key="search_restaurant",
)

if st.sidebar.button("Reset filters", use_container_width=True):
    for key in (
        "filter_locations",
        "filter_cuisines",
        "filter_types",
        "search_restaurant",
    ):
        st.session_state.pop(key, None)
    st.rerun()

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
            regex=False,
        )
    ]


# -------------------- KPI cards --------------------

total = len(filtered)

with_coordinates = int(
    filtered[["Latitude", "Longitude"]].notna().all(axis=1).sum()
)

with_phone = int(
    filtered["Phone"].fillna("").astype(str).str.strip().ne("").sum()
)

with_cuisine = int(filtered["Cuisine"].ne("Not listed").sum())

with_address = int(
    filtered["Address"].fillna("").astype(str).str.strip().ne("").sum()
)

with_website = int(
    filtered["Website"].fillna("").astype(str).str.strip().ne("").sum()
)

k1, k2, k3, k4 = st.columns(4)

k1.metric("Mapped Places", f"{total:,}")
k2.metric("Restaurant Types", filtered["Restaurant Type"].nunique())
k3.metric(
    "With Coordinates",
    f"{with_coordinates:,}",
    delta=f"{with_coordinates / total:.0%} coverage" if total else None,
)
k4.metric(
    "With Phone Number",
    f"{with_phone:,}",
    delta=f"{with_phone / total:.0%} coverage" if total else None,
)

st.divider()

if filtered.empty:
    st.warning("No places match your filters. Try resetting the filters.")
    st.stop()


# -------------------- Restaurant overview --------------------

st.subheader("📈 Restaurant Overview")
st.caption(
    f"Analysing {total:,} mapped places across "
    f"{filtered['Location'].nunique():,} listed locations."
)

left, right = st.columns(2)

with left:
    type_counts = (
        filtered["Restaurant Type"]
        .value_counts()
        .rename_axis("Restaurant Type")
        .reset_index(name="Places")
    )

    type_counts["Share"] = (
        type_counts["Places"] / type_counts["Places"].sum() * 100
    ).round(1)

    type_counts["Label"] = (
        type_counts["Places"].astype(str)
        + " ("
        + type_counts["Share"].astype(str)
        + "%)"
    )

    fig = px.bar(
        type_counts.sort_values("Places"),
        x="Restaurant Type",
        y="Places",
        title="Mapped Places by Type",
        text="Label",
        color="Restaurant Type",
        hover_data={"Share": ":.1f"},
    )

    fig.update_layout(
        xaxis_title="Place Type",
        yaxis_title="Number of Places",
        showlegend=False,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)

    st.plotly_chart(fig, use_container_width=True)

with right:
    cuisine_counts = (
        filtered["Cuisine"]
        .value_counts()
        .head(12)
        .rename_axis("Cuisine")
        .reset_index(name="Places")
    )

    cuisine_counts["Share"] = (
        cuisine_counts["Places"] / total * 100
    ).round(1)

    fig = px.bar(
        cuisine_counts.sort_values("Places"),
        x="Places",
        y="Cuisine",
        orientation="h",
        title="Most Common Listed Cuisines",
        text="Places",
        hover_data={"Share": ":.1f"},
    )

    fig.update_layout(
        xaxis_title="Number of Places",
        yaxis_title="",
    )
    fig.update_traces(textposition="outside", cliponaxis=False)

    st.plotly_chart(fig, use_container_width=True)


# -------------------- Location analysis --------------------

st.subheader("📊 Location-wise Analysis")

location_summary = (
    filtered.groupby("Location", as_index=False)
    .agg(
        Places=("Restaurant Name", "count"),
        Types=("Restaurant Type", "nunique"),
        Cuisines=("Cuisine", "nunique"),
        WithCoordinates=("Latitude", "count"),
    )
    .sort_values("Places", ascending=False)
)

left, right = st.columns(2)

with left:
    fig = px.bar(
        location_summary.head(20).sort_values("Places"),
        x="Places",
        y="Location",
        orientation="h",
        title="Top 20 Listed Locations",
        text="Places",
        color="Places",
        color_continuous_scale="Blues",
        hover_data=["Types", "Cuisines", "WithCoordinates"],
    )

    fig.update_layout(
        yaxis_title="",
        xaxis_title="Number of Mapped Places",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    fig = px.scatter(
        location_summary,
        x="Types",
        y="Cuisines",
        size="Places",
        hover_name="Location",
        title="Location Diversity",
        labels={
            "Types": "Different Place Types",
            "Cuisines": "Different Cuisine Labels",
            "Places": "Mapped Places",
        },
        hover_data=["Places", "WithCoordinates"],
    )

    st.plotly_chart(fig, use_container_width=True)


# -------------------- Restaurant distribution --------------------

st.subheader("🍴 Restaurant Distribution")

distribution_type = st.selectbox(
    "Analyse distribution by",
    options=["Location", "Restaurant Type", "Cuisine"],
    key="distribution_type",
)

distribution_data = (
    filtered[distribution_type]
    .fillna("Not listed")
    .value_counts()
    .head(15)
    .rename_axis(distribution_type)
    .reset_index(name="Places")
    .sort_values("Places", ascending=True)
)

fig = px.bar(
    distribution_data,
    x="Places",
    y=distribution_type,
    orientation="h",
    text="Places",
    title=f"Top 15 Places by {distribution_type}",
    labels={"Places": "Number of mapped places"},
)

fig.update_layout(
    yaxis_title="",
    xaxis_title="Number of mapped places",
)

st.plotly_chart(fig, use_container_width=True)

# -------------------- Data quality --------------------

st.subheader("🧹 Data Quality")

q1, q2, q3, q4 = st.columns(4)

q1.metric(
    "Coordinates Available",
    f"{with_coordinates:,}",
    delta=f"{with_coordinates / total:.0%}" if total else None,
)
q2.metric(
    "Cuisine Listed",
    f"{with_cuisine:,}",
    delta=f"{with_cuisine / total:.0%}" if total else None,
)
q3.metric(
    "Address Listed",
    f"{with_address:,}",
    delta=f"{with_address / total:.0%}" if total else None,
)
q4.metric(
    "Website Listed",
    f"{with_website:,}",
    delta=f"{with_website / total:.0%}" if total else None,
)

quality_df = pd.DataFrame({
    "Field": ["Coordinates", "Phone", "Cuisine", "Address", "Website"],
    "Available": [
        with_coordinates,
        with_phone,
        with_cuisine,
        with_address,
        with_website,
    ],
})

quality_df["Missing"] = total - quality_df["Available"]
quality_df["Coverage (%)"] = (
    quality_df["Available"] / total * 100
).round(1)

fig = px.bar(
    quality_df,
    x="Field",
    y="Coverage (%)",
    title="Information Coverage by Field",
    text="Coverage (%)",
    range_y=[0, 100],
)

fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Coverage describes the available records, not every restaurant operating "
    "in Meerut."
)


# -------------------- Interactive map --------------------

st.subheader("📍 Restaurant Locations")

map_data = filtered.dropna(
    subset=["Latitude", "Longitude"]
).copy()

map_data = map_data[
    map_data["Latitude"].between(-90, 90)
    & map_data["Longitude"].between(-180, 180)
]

if not map_data.empty:
    st.caption(f"Showing {len(map_data):,} places with valid coordinates.")

    try:
        fig_map = px.scatter_map(
    map_data,
    lat="Latitude",
    lon="Longitude",
    color="Restaurant Type",
    hover_name="Restaurant Name",
    hover_data={
        "Location": True,
        "Cuisine": True,
        "Address": True,
        "Latitude": False,
        "Longitude": False,
    },
    zoom=11,
    center={"lat": 28.9845, "lon": 77.7064},
    height=520,
    map_style="open-street-map",
    title="Restaurant Locations in Meerut",
)
        fig_map.update_layout(
            margin={"r": 0, "t": 50, "l": 0, "b": 0},
            legend_title_text="Place Type",
        )

        st.plotly_chart(
            fig_map,
            use_container_width=True,
            key="restaurant_location_map",
        )

    except (ValueError, TypeError, KeyError, AttributeError) as error:
        st.error(f"Could not render the map: {error}")

    st.markdown("#### View a place's details")

    place_names = sorted(map_data["Restaurant Name"].unique().tolist())

    selected_place = st.selectbox(
        "Choose a mapped place",
        place_names,
        key="selected_place_details",
    )

    place_rows = map_data[
        map_data["Restaurant Name"] == selected_place
    ]

    if not place_rows.empty:
        place = place_rows.iloc[0]

        d1, d2 = st.columns(2)

        with d1:
            st.markdown(f"**{place['Restaurant Name']}**")
            st.write(f"Type: {place['Restaurant Type']}")
            st.write(f"Cuisine: {place['Cuisine']}")
            st.write(f"Location: {place['Location']}")
            st.write(f"Address: {place['Address'] or 'Not listed'}")

        with d2:
            st.write(f"Phone: {place['Phone'] or 'Not listed'}")
            st.write(
                f"Opening hours: {place['Opening Hours'] or 'Not listed'}"
            )

            website = str(place["Website"]).strip()
            if website:
                st.write(f"Website: {website}")
            else:
                st.write("Website: Not listed")
            maps_url = (
                "https://www.google.com/maps/search/?api=1&query="
                f"{place['Latitude']},{place['Longitude']}"
            )

            st.link_button("📍 Open in Google Maps", maps_url)

else:
    st.warning("No valid coordinates found for the selected filters.")
    st.info("Try selecting more locations or resetting the filters.")


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

with st.expander("Directory display options", expanded=False):
    show_osm_id = st.checkbox("Include OpenStreetMap ID in the table")

if show_osm_id:
    display_columns.append("OSM ID")

sort_column = st.selectbox(
    "Sort restaurants by",
    options=[
        "Restaurant Name",
        "Location",
        "Restaurant Type",
        "Cuisine",
    ],
    key="directory_sort_column",
)

sort_order = st.radio(
    "Sort order",
    options=["A to Z", "Z to A"],
    horizontal=True,
    key="directory_sort_order",
)

directory = filtered[display_columns].sort_values(
    by=sort_column,
    ascending=(sort_order == "A to Z"),
    na_position="last",
)

st.dataframe(
    directory,
    use_container_width=True,
    hide_index=True,
)

st.caption(f"Showing {len(filtered):,} mapped records after filtering.")



# -------------------- CSV and JSON exports --------------------

st.subheader("📥 Export Reports")

export_columns = st.multiselect(
    "Choose columns for export",
    options=display_columns,
    default=display_columns,
    key="export_columns",
)

if export_columns:
    export_df = filtered[export_columns].copy()

    csv_data = export_df.to_csv(index=False).encode("utf-8-sig")

    json_data = export_df.to_json(
        orient="records",
        force_ascii=False,
        indent=2,
    ).encode("utf-8")

    export1, export2 = st.columns(2)

    with export1:
        st.download_button(
            label="⬇️ Download CSV Report",
            data=csv_data,
            file_name="meerut_restaurants.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with export2:
        st.download_button(
            label="⬇️ Download JSON Report",
            data=json_data,
            file_name="meerut_restaurants.json",
            mime="application/json",
            use_container_width=True,
        )
else:
    st.info("Please select at least one column to export.")


# -------------------- Footer --------------------

st.divider()

st.caption(
    "Data source: © OpenStreetMap contributors. "
    "OpenStreetMap data is available under the Open Database License (ODbL). "
    "Business details may be incomplete or outdated. Ratings, reviews and "
    "prices are not included in this dataset."
)