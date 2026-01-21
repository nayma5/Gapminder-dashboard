import streamlit as st
import pandas as pd
import plotly.express as px

# ── Page config ──
st.set_page_config(page_title="Gapminder Dashboard", layout="wide")

# ── Force light theme + strong multiselect / dropdown fix ──
st.markdown(
    """
    <style>
    /* Force app background */
    .stApp { 
        background-color: #ffffff !important; 
    }

    /* General text */
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #111111 !important;
    }

    /* Multiselect container (the box itself) */
    [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #cccccc !important;
        color: #111111 !important;
    }

    /* Input / search field inside */
    [data-baseweb="select"] input {
        color: #111111 !important;
        caret-color: #111111 !important;
        background-color: transparent !important;
    }

    [data-baseweb="select"] input::placeholder {
        color: #888888 !important;
    }

    /* Selected tags/chips */
    [data-baseweb="tag"] {
        background-color: #e8e8e8 !important;
        color: #111111 !important;
        border: 1px solid #bbbbbb !important;
    }

    [data-baseweb="tag"] svg {
        fill: #111111 !important;
    }

    /* ── MOST IMPORTANT: Dropdown menu / popover ── */
    /* The floating menu container */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div {
        background-color: #ffffff !important;
        border: 1px solid #cccccc !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }

    /* The actual list (menu) */
    ul[data-baseweb="menu"] {
        background-color: #ffffff !important;
        padding: 8px 0 !important;
    }

    /* Each option/item */
    ul[data-baseweb="menu"] li,
    ul[data-baseweb="menu"] li > div {
        background-color: #ffffff !important;
        color: #111111 !important;
        padding: 8px 12px !important;
    }

    /* Hover / selected / focused state */
    ul[data-baseweb="menu"] li:hover,
    ul[data-baseweb="menu"] li[aria-selected="true"],
    ul[data-baseweb="menu"] li:focus {
        background-color: #f0f8ff !important;   /* light blue highlight */
        color: #111111 !important;
    }

    /* Fallback selectors sometimes used by Streamlit */
    div[role="listbox"],
    div[role="option"] {
        background-color: #ffffff !important;
        color: #111111 !important;
    }

    div[role="option"]:hover,
    div[role="option"][aria-selected="true"] {
        background-color: #f0f8ff !important;
        color: #111111 !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ── Data ──
@st.cache_data
def load_data():
    return pd.read_csv("dataset/gapminder_data_graphs.csv")

df = load_data()

# ── Header ──
st.markdown(
    "<h1 style='font-size:36px; margin-bottom:0;'>Global Development Trends (1998–2018)</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='font-size:18px; margin-top:4px;'>Life expectancy, HDI, GDP, CO₂ consumption, services share</p>",
    unsafe_allow_html=True
)

# ── Filters ──
years = sorted(df["year"].unique())
continents = sorted(df["continent"].unique())

c1, c2 = st.columns([1, 3])
with c1:
    year = st.slider("Year", int(min(years)), int(max(years)), int(max(years)))

with c2:
    cont_sel = st.multiselect(
        "Continent(s) (Oceania = Australia & New Zealand)",
        continents,
        default=continents
    )

f = df[(df["year"] == year) & (df["continent"].isin(cont_sel))].copy()

# ── Plot styling helper ──
def fix_axes(fig):
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#111", size=15),
        legend=dict(font=dict(color="#111", size=14)),
        title=dict(font=dict(color="#111", size=20)),
        margin=dict(l=70, r=40, t=60, b=60),
    )
    fig.update_xaxes(
        showline=True, linecolor="#444", ticks="outside",
        tickfont=dict(color="#111", size=14),
        title_font=dict(color="#111", size=16),
        gridcolor="#e6e6e6", zeroline=False,
    )
    fig.update_yaxes(
        showline=True, linecolor="#444", ticks="outside",
        tickfont=dict(color="#111", size=14),
        title_font=dict(color="#111", size=16),
        gridcolor="#e6e6e6", zeroline=False,
    )
    return fig

# ── Main scatter (with brushing) ──
f_scatter = f.dropna(subset=["gdp"]).copy()
f_scatter = f_scatter[f_scatter["gdp"] > 0]

fig_scatter = px.scatter(
    f_scatter,
    x="gdp", y="life_exp",
    color="continent", size="co2_consump",
    hover_name="country",
    title=f"GDP vs Life Expectancy ({year}) — box/lasso select to link",
    labels={"gdp": "GDP per capita (log scale)", "life_exp": "Life expectancy", "co2_consump": "CO₂ consumption"},
)
fig_scatter.update_xaxes(type="log")
fix_axes(fig_scatter)

selected = st.plotly_chart(
    fig_scatter,
    use_container_width=True,
    key="scatter",
    on_select="rerun",
    selection_mode=("box", "lasso"),
)

selected_countries = []
if selected and "selection" in selected and selected["selection"].get("points"):
    selected_countries = [p.get("hovertext") for p in selected["selection"]["points"] if p.get("hovertext")]

if selected_countries:
    f_linked = f[f["country"].isin(selected_countries)].copy()
    st.success(f"Linked selection: {len(selected_countries)} countries")
else:
    f_linked = f.copy()
    st.caption("Select points to explore linked views")

# ── Line chart ──
line = (
    df[df["continent"].isin(cont_sel)]
    .groupby(["year", "continent"], as_index=False)["life_exp"]
    .mean()
)
fig_line = px.line(
    line, x="year", y="life_exp", color="continent",
    title="Average Life Expectancy Over Time (by continent)",
    labels={"life_exp": "Life expectancy"},
)
fix_axes(fig_line)

# ── Bar chart ──
bar = (
    f_linked.groupby("continent", as_index=False)["life_exp"]
    .mean()
    .sort_values("life_exp", ascending=False)
)
fig_bar = px.bar(
    bar, x="continent", y="life_exp", color="continent",
    title=f"Avg Life Expectancy by Continent ({year})",
    labels={"life_exp": "Life expectancy"},
)
fix_axes(fig_bar)

# ── Heatmap ──
h = f_linked.dropna(subset=["hdi_index"]).copy()
fig_heat = px.density_heatmap(
    h, x="hdi_index", y="life_exp",
    nbinsx=20, nbinsy=20,
    title="HDI vs Life Expectancy (density)",
    labels={"hdi_index": "HDI", "life_exp": "Life expectancy"},
)
fix_axes(fig_heat)

# ── Layout ──
top = st.columns(2)
with top[0]:
    st.plotly_chart(fig_line, use_container_width=True)
with top[1]:
    st.plotly_chart(fig_bar, use_container_width=True)

bottom = st.columns(2)
with bottom[0]:
    st.plotly_chart(fig_heat, use_container_width=True)
with bottom[1]:
    st.markdown("<h3 style='font-size:22px;'>Selected Countries (Linked)</h3>", unsafe_allow_html=True)
    cols = ["country", "continent", "life_exp", "hdi_index", "gdp", "co2_consump", "services"]
    table = f_linked[cols].sort_values("life_exp", ascending=False)
    if not selected_countries:
        table = table.head(15)
    st.dataframe(table, use_container_width=True)