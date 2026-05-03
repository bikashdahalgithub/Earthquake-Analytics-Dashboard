import streamlit as st
import pandas as pd
#import matplotlib.pyplot as plt
#import seaborn as sns
import plotly.express as px
import pydeck as pdk

st.set_page_config(page_title="Earthquake Dashboard", layout="wide")

# -------------------- LOAD DATA --------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Earthquake_with_continent.csv")
    return df

df = load_data()
df.columns = df.columns.str.strip()

df['fromdate'] = pd.to_datetime(df['fromdate'], errors='coerce')

df.rename(columns={
    'Earthquake Magnitude (M)': 'magnitude',
    'Depth (km)': 'depth'
}, inplace=True)

# -------------------- SIDEBAR --------------------
st.sidebar.markdown("## 🎛️ Filters")
st.sidebar.markdown("---")

min_date = df['fromdate'].min()
max_date = df['fromdate'].max()

date_range = st.sidebar.date_input("Date Range", [min_date, max_date])

mag_range = st.sidebar.slider(
    "Magnitude Range",
    float(df['magnitude'].min()),
    float(df['magnitude'].max()),
    (float(df['magnitude'].min()), float(df['magnitude'].max()))
)

# Continent filter
continents = sorted(df['continent'].dropna().unique())
selected_continents = st.sidebar.multiselect(
    "Select Continents",
    continents,
    default=continents
)

# -------------------- FILTER LOGIC --------------------
start_date = pd.to_datetime(date_range[0])
end_date = pd.to_datetime(date_range[1])

filtered_df = df[
    (df['fromdate'] >= start_date) &
    (df['fromdate'] <= end_date) &
    (df['magnitude'] >= mag_range[0]) &
    (df['magnitude'] <= mag_range[1]) &
    (df['continent'].isin(selected_continents))
]

# -------------------- HEADER --------------------
st.markdown("""
    <div style="
        background: linear-gradient(90deg, #7f0000, #ff4d4d);
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 25px;
        text-align:center;
    ">
        <h1 style="color:white; font-weight:700; margin-bottom:5px;">
            🌍 Earthquake Analytics Dashboard
        </h1>
        <p style="color:#ffe6e6; font-size:15px;">
            Real-time insights into global seismic activity
        </p>
    </div>
""", unsafe_allow_html=True)

# -------------------- KPI CARDS --------------------
k1, k2, k3, k4 = st.columns(4)

def kpi_card(title, value):
    return f"""
    <div style="
        background: linear-gradient(135deg, #ffe5e5, #ffcccc);
        padding:20px;
        border-radius:12px;
        text-align:center;
        height:120px;
        display:flex;
        flex-direction:column;
        justify-content:center;
        align-items:center;
        box-shadow:0px 6px 14px rgba(0,0,0,0.15);
        border-left:6px solid  #cc0000;
    ">
       <div style="
            color:#800000;
            font-size:15px;
            font-weight:600;
            margin-bottom:8px;
            letter-spacing:0.5px;
        ">
            {title}
        </div>
        <div style="
            color:#cc0000;
            font-size:28px;
            font-weight:800;
        ">
            {value}
        </div>
    </div>
    """

total_eq = len(filtered_df)

population = (
    int(filtered_df['population'].sum())
    if 'population' in filtered_df.columns else "N/A"
)

top_country = (
    filtered_df['country'].value_counts().idxmax()
    if not filtered_df.empty else "N/A"
)

max_mag = round(filtered_df['magnitude'].max(), 2) if not filtered_df.empty else 0

k1.markdown(kpi_card("Total Earthquakes", total_eq), unsafe_allow_html=True)
k2.markdown(kpi_card("Total Population Affected", population), unsafe_allow_html=True)
k3.markdown(kpi_card("Top Country Affected", top_country), unsafe_allow_html=True)
k4.markdown(kpi_card("Max Magnitude", max_mag), unsafe_allow_html=True)

st.markdown("---")

# -------------------- MAP --------------------
st.subheader("🌍 Global Earthquake Map")

map_df = filtered_df.dropna(subset=['latitude', 'longitude'])

layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_df,
    get_position='[longitude, latitude]',
    get_radius='magnitude * 10000',
    get_fill_color='[200, 30, 30]',
    pickable=True
)

view_state = pdk.ViewState(
    latitude=map_df['latitude'].mean() if not map_df.empty else 0,
    longitude=map_df['longitude'].mean() if not map_df.empty else 0,
    zoom=2
)

st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={"text": "Magnitude: {magnitude}\nDepth: {depth}"}
))

st.markdown("---")

# -------------------- EDA (2x2 GRID - INTERACTIVE) --------------------

col1, col2 = st.columns(2)

# 1. Magnitude Distribution (Histogram)
with col1:
    st.subheader("Magnitude Distribution")
    fig1 = px.histogram(
        filtered_df,
        x='magnitude',
        nbins=30,
        color_discrete_sequence=['#ff4d4d'],
        opacity=0.85
    )

    fig1.update_traces(
        marker_line_color='black',
        marker_line_width=1.2
    )

    fig1.update_layout(
        xaxis_title="Magnitude",
        yaxis_title="Count",
        bargap=0.05,
        plot_bgcolor="white"
    )

    st.plotly_chart(fig1, use_container_width=True)


# 2. Alert Score Distribution (Pie Chart)
with col2:
    st.subheader("Alert Score Distribution")

    alert_counts = filtered_df['alertscore'].value_counts().reset_index()
    alert_counts.columns = ['alertscore', 'count']

    fig2 = px.pie(
        alert_counts,
        names='alertscore',
        values='count',
        color_discrete_sequence=px.colors.sequential.Reds
    )

    st.plotly_chart(fig2, use_container_width=True)


col3, col4 = st.columns(2)

# 3. Earthquakes Over Time (Cumulative Line)
with col3:
    st.subheader("Earthquakes Over Time (Cumulative)")

    time_series = (
        filtered_df.groupby(filtered_df['fromdate'].dt.date)
        .size()
        .cumsum()
        .reset_index()
    )
    time_series.columns = ['date', 'count']

    fig3 = px.line(
        time_series,
        x='date',
        y='count',
        markers=True
    )

    st.plotly_chart(fig3, use_container_width=True)


# 4. Top Countries (Bar Chart)
with col4:
    st.subheader("Top 10 Countries")

    top_loc = (
        filtered_df['country']
        .value_counts()
        .head(10)
        .sort_values()
        .reset_index()
    )
    top_loc.columns = ['country', 'count']

    fig4 = px.bar(
        top_loc,
        x='count',
        y='country',
        orientation='h',
        color='count',
        color_continuous_scale='Reds'
    )

    st.plotly_chart(fig4, use_container_width=True)
st.markdown("---")
st.markdown(
    "<center>Built using Streamlit | Earthquake Analytic Dashboard By Bikash Dahal</center>",
    unsafe_allow_html=True
)
