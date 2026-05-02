import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pydeck as pdk

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Earthquake Dashboard", layout="wide")

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Earthquake_clean.csv")
    return df

df = load_data()

# -----------------------------
# DATA PREPROCESSING
# -----------------------------
df.columns = df.columns.str.strip()

df['fromdate'] = pd.to_datetime(df['fromdate'], errors='coerce')

df.rename(columns={
    'Earthquake Magnitude (M)': 'magnitude',
    'Depth (km)': 'depth'
}, inplace=True)

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.markdown("## 🎛️ Dashboard Filters")
st.sidebar.markdown("---")

min_date = df['fromdate'].min()
max_date = df['fromdate'].max()

date_range = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date]
)

min_mag = float(df['magnitude'].min())
max_mag = float(df['magnitude'].max())

mag_range = st.sidebar.slider(
    "Magnitude Range",
    min_mag,
    max_mag,
    (min_mag, max_mag)
)

# -----------------------------
# FILTER DATA
# -----------------------------
if len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])
else:
    start_date = min_date
    end_date = max_date

filtered_df = df[
    (df['fromdate'] >= start_date) &
    (df['fromdate'] <= end_date) &
    (df['magnitude'] >= mag_range[0]) &
    (df['magnitude'] <= mag_range[1])
]

# -----------------------------
# TITLE
# -----------------------------
st.markdown("""
    <h1 style='text-align: center; color: #1f77b4;'>
    🌍 Earthquake Analytics Dashboard
    </h1>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------
# KPI CARDS
# -----------------------------
k1, k2, k3, k4, k5 = st.columns(5)

def kpi_card(title, value):
    return f"""
        <div style="
            background-color:#262730;
            padding:15px;
            border-radius:10px;
            text-align:center;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        ">
            <h4 style='color:gray'>{title}</h4>
            <h2 style='color:#1f77b4'>{value}</h2>
        </div>
    """

k1.markdown(kpi_card("Total Earthquakes", len(filtered_df)), unsafe_allow_html=True)
k2.markdown(kpi_card("Max Magnitude", round(filtered_df['magnitude'].max(), 2)), unsafe_allow_html=True)
k3.markdown(kpi_card("Avg Magnitude", round(filtered_df['magnitude'].mean(), 2)), unsafe_allow_html=True)
k4.markdown(kpi_card("Min Depth", round(filtered_df['depth'].min(), 2)), unsafe_allow_html=True)
k5.markdown(kpi_card("Max Depth", round(filtered_df['depth'].max(), 2)), unsafe_allow_html=True)

st.markdown("---")

# -----------------------------
# MAP (TOP PRIORITY VISUAL)
# -----------------------------
st.markdown("## 🌍 Global Earthquake Map")

map_df = filtered_df.dropna(subset=['latitude', 'longitude'])

layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_df,
    get_position='[longitude, latitude]',
    get_radius='magnitude * 10000',
    get_fill_color='[magnitude * 40, 50, 150]',
    pickable=True
)

view_state = pdk.ViewState(
    latitude=map_df['latitude'].mean() if not map_df.empty else 0,
    longitude=map_df['longitude'].mean() if not map_df.empty else 0,
    zoom=2,
    pitch=0
)

st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={"text": "Magnitude: {magnitude}\nDepth: {depth}"}
))

st.markdown("---")

# -----------------------------
# CHARTS (GRID LAYOUT)
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Magnitude Distribution")
    fig1, ax1 = plt.subplots()
    sns.histplot(filtered_df['magnitude'], kde=True, ax=ax1)
    st.pyplot(fig1)

with col2:
    st.subheader("Depth vs Magnitude")
    fig2, ax2 = plt.subplots()
    sns.scatterplot(data=filtered_df, x='depth', y='magnitude', ax=ax2)
    st.pyplot(fig2)

col3, col4 = st.columns(2)

with col3:
    st.subheader("Earthquakes Over Time")
    time_series = filtered_df.groupby(filtered_df['fromdate'].dt.date).size()
    st.line_chart(time_series)

with col4:
    st.subheader("Top Countries")
    top_loc = filtered_df['country'].value_counts().head(10)
    st.bar_chart(top_loc)

# -----------------------------
# HEATMAP
# -----------------------------
st.subheader("Correlation Heatmap")
numeric_df = filtered_df.select_dtypes(include='number')

fig3, ax3 = plt.subplots(figsize=(10, 5))
sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", ax=ax3)
st.pyplot(fig3)

# -----------------------------
# RAW DATA
# -----------------------------
st.subheader("Raw Data")
st.dataframe(filtered_df)

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.markdown(
    "<center>Built with Streamlit | Earthquake Analytics Dashboard</center>",
    unsafe_allow_html=True
)