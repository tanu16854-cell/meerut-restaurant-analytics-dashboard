
# Meerut Restaurant Analytics Dashboard

An interactive data analytics dashboard built with Python, Streamlit, Pandas and Plotly to explore restaurant and food-place data mapped in Meerut, Uttar Pradesh, India.

## Features

- KPI cards for mapped places, place types, coordinates and phone numbers
- Light and dark theme-compatible styling
- Sidebar filters for location, cuisine, place type and restaurant name
- Interactive Plotly charts for restaurant types, cuisines and locations
- Location diversity analysis
- Map of available geographic coordinates
- Searchable restaurant directory
- CSV export of filtered records
- Data-quality summaries

## Data Source

The dashboard uses a GeoJSON dataset sourced from OpenStreetMap.

**Important:** OpenStreetMap records may be incomplete or outdated. This dataset should not be treated as a verified, exhaustive list of all restaurants in Meerut. Ratings, reviews and prices are not included unless they are explicitly available in the source data.

© OpenStreetMap contributors. Data is available under the Open Database License (ODbL).

## Tech Stack

- Python
- Streamlit
- Pandas
- Plotly
- GeoJSON
- OpenStreetMap

## Project Structure

```text
restaurant_analytics_dashboard/
├── app.py
├── app_backup.py
├── requirements.txt
├── README.md
└── data/
    └── meerut_restaurants.geojson
```

## Run on Windows

### 1. Clone the repository

```powershell
git clone https://github.com/tanu16854-cell/meerut-restaurant-analytics-dashboard.git
cd meerut-restaurant-analytics-dashboard
```

### 2. Create a virtual environment

```powershell
py -m venv .venv
```

### 3. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Start the dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed in the terminal, usually `http://localhost:8501`.

## Future Improvements

- Enhanced dashboard layout and responsive styling
- Additional analytical charts and comparisons
- Improved map interactions
- Downloadable filtered reports and data-quality checks
