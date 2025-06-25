import streamlit as st
import pandas as pd

st.set_page_config(page_title="📘 Data Dictionary Portal", layout="wide")
st.title("📘 Data Dictionary Portal")

@st.cache_data
def load_data():
    xls = pd.ExcelFile("data_dictionary.xlsx")
    return {
        "columns": xls.parse("(Updated)tables_with_columns"),
        "views": xls.parse("view_fields_audit"),
        "mapping": xls.parse("Data Mapping"),
        "table_meta": xls.parse("(Updated)tables", skiprows=2)
    }

data = load_data()

# Prepare Tables + Views
tables = data["columns"].rename(columns={
    "TABLE_SCHEMA": "SCHEMA", "TABLE_NAME": "TABLE", "COLUMN_NAME": "COLUMN",
    "DATA_TYPE": "DATA_TYPE", "DESCRIPTIONS": "DESCRIPTION", "DESCRIPTIONS.1": "LONG_DESC"
})
tables["SOURCE"] = "TABLE"

views = data["views"].rename(columns={
    "TABLE_SCHEMA": "SCHEMA", "TABLE_NAME": "TABLE", "COLUMN_NAME": "COLUMN", "DATA_TYPE": "DATA_TYPE"
})
views["DESCRIPTION"] = ""
views["LONG_DESC"] = ""
views["SOURCE"] = "VIEW"

df = pd.concat([tables, views], ignore_index=True)

# Clean mapping and metadata
mapping = data["mapping"].rename(columns={
    "Fields Needed": "USE_CASE", "Description": "USE_DESC", "Category": "CATEGORY",
    "Table Name - FR": "TABLE", "Field Name - FR": "COLUMN"
})
table_meta = data["table_meta"].rename(columns={"TABLE_SCHEMA": "SCHEMA", "TABLE_NAME": "TABLE"})

# --- Sidebar Filters ---
st.sidebar.header("🎛️ Column Filter")
col_filter = st.sidebar.text_input("🔍 Column name contains")
schema_filter = st.sidebar.multiselect("📂 Schema", sorted(df["SCHEMA"].dropna().unique()))
table_filter = st.sidebar.multiselect("📁 Table", sorted(df["TABLE"].dropna().unique()))
source_filter = st.sidebar.radio("📌 Source", ["All", "TABLE", "VIEW"])

# --- Filtered Results ---
filtered = df.copy()
if col_filter:
    filtered = filtered[filtered["COLUMN"].str.contains(col_filter, case=False, na=False)]
if schema_filter:
    filtered = filtered[filtered["SCHEMA"].isin(schema_filter)]
if table_filter:
    filtered = filtered[filtered["TABLE"].isin(table_filter)]
if source_filter != "All":
    filtered = filtered[filtered["SOURCE"] == source_filter]

st.markdown("## 🔍 Filtered Column Results")
st.write(f"Showing **{len(filtered)}** results")

for _, row in filtered.iterrows():
    with st.expander(f"📌 `{row['COLUMN']}` from `{row['SCHEMA']}.{row['TABLE']}` ({row['SOURCE']})"):
        st.markdown(f"**Data Type:** `{row['DATA_TYPE']}`")
        st.markdown(f"**Short Description:** {row['DESCRIPTION'] or '—'}")
        if row['LONG_DESC']:
            st.markdown(f"**Technical Description:** {row['LONG_DESC']}")

st.download_button("📥 Download Filtered Results", data=filtered.to_csv(index=False).encode("utf-8"),
                   file_name="filtered_data_dictionary.csv")

# --- Tabs Section ---
st.markdown("---")
st.markdown("## 🧭 Additional Explorers")

tab1, tab2 = st.tabs(["🎯 Use Case Explorer", "📁 Browse by Table"])

# --- Tab 1: Use Case Explorer ---
with tab1:
    st.subheader("🎯 Business Use Case → Suggested Columns")
    use_case = st.selectbox("Select Use Case", mapping["USE_CASE"].dropna().unique())
    case_rows = mapping[mapping["USE_CASE"] == use_case]

    for _, row in case_rows.iterrows():
        st.markdown(f"### 🔹 {row['USE_CASE']}")
        st.markdown(f"- **Category**: `{row['CATEGORY']}`")
        st.markdown(f"- **Use Description**: {row['USE_DESC']}")
        st.markdown(f"- **Suggested Table**: `{row['TABLE']}`")
        st.markdown(f"- **Suggested Column(s)**:\n```\n{row['COLUMN']}\n```")
        st.markdown("---")

# --- Tab 2: Schema/Table Explorer ---
with tab2:
    st.subheader("📁 Schema + Table Explorer")
    schema_sel = st.selectbox("Select Schema", sorted(df["SCHEMA"].dropna().unique()))
    table_sel = st.selectbox("Select Table", sorted(df[df["SCHEMA"] == schema_sel]["TABLE"].dropna().unique()))

    display_df = df[(df["SCHEMA"] == schema_sel) & (df["TABLE"] == table_sel)]
    st.markdown(f"### 📋 Columns in `{schema_sel}.{table_sel}`")
    st.dataframe(display_df[["COLUMN", "DATA_TYPE", "DESCRIPTION", "SOURCE"]], use_container_width=True)

    # Show table-level metadata
    meta = table_meta[table_meta["TABLE"] == table_sel]
    if not meta.empty:
        st.markdown("#### 🧾 Table Description")
        st.write(f"**Business:** {meta['BUSINESS: What it does'].values[0]}")
        st.write(f"**Technical:** {meta['TECHNICAL: How it works'].values[0]}")
