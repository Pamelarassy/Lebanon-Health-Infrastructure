# streamlit_app.py — Lebanon Health Infrastructure (Purpose + 2 charts + insights under Chart 2)
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------- Page ----------------
st.set_page_config(page_title="Lebanon Health Infrastructure", layout="wide")
st.title("Lebanon Health Infrastructure")
st.caption("Hospitals • Clinics • Pharmacies • Medical Centers — by Town (2023)")

# ---------------- Purpose of the study ----------------
st.markdown("""
### Purpose of the study
- **Map and compare** the distribution of health-care resources (Hospitals, Clinics, Pharmacies, Medical Centers) across Lebanese towns in 2023.  
- **Identify disparities** (which towns are resource-dense vs. underserved, and which facility types are lacking where).  
- **Support decisions** for planners, NGOs, and local authorities (e.g., where to prioritize new clinics/hospitals or outreach).
""")

# ---------------- Load ----------------
CSV = Path("data/Health_Resources-Lebanon-2023.csv")
df = pd.read_csv(CSV)  # add sep=';' or encoding='latin-1' if needed
df.columns = df.columns.str.strip().str.replace(r"\s+", " ", regex=True)

# Short names (your mapping)
rename_map = {
    "Existence of nearby care centers - exists": "nearby_exists",
    "Existence of special needs care centers - does not exist": "snc_no",
    "Existence of health resources - exists": "health_exists",
    "Type and size of medical resources - Hospitals": "hospitals",
    "Existence of a first aid center - exists": "first_aid_exists",
    "Total number of care centers": "care_cnt",
    "Type and size of medical resources - Clinics": "clinics",
    "Existence of special needs care centers - exists": "snc_yes",
    "Type and size of medical resources - Pharmacies": "pharmacies",
    "Total number of first aid centers": "first_aid_cnt",
    "Type and size of medical resources - Labs and Radiology": "labs_radiology",
    "Percentage of towns with special needs indiciduals - Without special needs": "pct_no_sn",
    "Percentage of towns with special needs indiciduals - With special needs": "pct_with_sn",
    "Type and size of medical resources - Medical Centers": "medical_centers",
}
df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

# Validate & coerce
need = ["hospitals", "clinics", "pharmacies", "medical_centers"]
if "Town" not in df.columns or any(c not in df.columns for c in need):
    st.error("Missing required columns: 'Town' and the resource columns.")
    st.stop()
for c in need:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

# Aggregate once (per town)
agg = (
    df.groupby("Town", dropna=False)[need]
      .sum(numeric_only=True)
      .reset_index()
)
agg["TOTAL"] = agg[need].sum(axis=1)

pretty = {
    "hospitals": "Hospitals",
    "clinics": "Clinics",
    "pharmacies": "Pharmacies",
    "medical_centers": "Medical Centers",
}

# ---------------- Sidebar controls ----------------
with st.sidebar:
    st.header("Display Options")
    max_n = int(min(60, len(agg)))
    n_towns = st.slider("Heatmap: number of towns", min_value=10, max_value=max_n, value=min(30, max_n), step=5)
    name_filter = st.text_input("Filter towns by name", "")

# Apply optional filter (affects both charts)
agg_filtered = agg.copy()
if name_filter.strip():
    agg_filtered = agg_filtered[agg_filtered["Town"].str.contains(name_filter.strip(), case=False, na=False)]

# ---------------- Chart 1 ----------------
st.markdown("### Distribution of Healthcare Resources by Town in Lebanon")

top_n = min(20, len(agg_filtered))
top20 = agg_filtered.nlargest(top_n, "TOTAL").drop(columns="TOTAL")

long_top20 = top20.melt(id_vars="Town", value_vars=need, var_name="Resource", value_name="count")
long_top20["Resource"] = long_top20["Resource"].map(pretty)

# keep towns ordered by total desc
order = top20.assign(TOTAL=top20[need].sum(axis=1)).sort_values("TOTAL", ascending=False)["Town"].tolist()
long_top20["Town"] = pd.Categorical(long_top20["Town"], categories=order, ordered=True)

fig1 = px.bar(
    long_top20,
    x="Town", y="count", color="Resource",
    barmode="stack",
)
fig1.update_layout(title_text="", xaxis_title="Town", yaxis_title="Count", legend_title="")
fig1.update_xaxes(tickangle=-50)
st.plotly_chart(fig1, use_container_width=True)

# ---------------- Chart 2 ----------------
st.markdown("### Comparative Availability of Healthcare Facilities by Town")

topN = agg_filtered.nlargest(min(n_towns, len(agg_filtered)), "TOTAL").drop(columns="TOTAL")
mat = topN.set_index("Town")[need].rename(columns=pretty)

fig_hm = px.imshow(
    mat,
    aspect="auto",
    labels=dict(x="Resource", y="Town", color="Count"),
    color_continuous_scale="Blues",
    zmin=0,
    zmax=20,  # fixed 0 → 20 for clearer differences across typical towns
)
fig_hm.update_layout(title_text="", coloraxis_colorbar=dict(title="Count"))
fig_hm.update_xaxes(side="top")
st.plotly_chart(fig_hm, use_container_width=True)

# ---- Simple insights under Chart 2 ----
st.markdown("#### Insights:")
st.markdown(
    """
- **Trablous stands out**: it has far more facilities than many towns, mostly pharmacies and clinics.
- **Medical centers are not everywhere**: the pink/medical-centers presence is noticeable only in a few towns 
- **Same mix in most towns**: pharmacies are usually the largest part, clinics come next, and hospitals are the smallest.  
  → This suggests strong outpatient access but limited inpatient capacity at the town level.
"""
)
