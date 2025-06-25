import streamlit as st
import pandas as pd

st.set_page_config(page_title="📘 Data Dictionary", layout="wide")
st.title("📘 Data Dictionary Explorer")

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

# Prepare tables
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

mapping = data["mapping"].rename(columns={
    "Fields Needed": "USE_CASE", "Description": "USE_DESC", "Category": "CATEGORY",
    "Table Name - FR": "TABLE", "Field Name - FR": "COLUMN"
})

table_meta = data["table_meta"].rename(columns={"TABLE_SCHEMA": "SCHEMA", "TABLE_NAME": "TABLE"})

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["🔍 Column Search", "🎯 Use Case", "📁 Browse by Table"])

# --- TAB 1: COLUMN SEARCH ---
with tab1:
    st.subheader("🔍 Search by Column")
    search = st.text_input("Enter column name (partial OK)")
    source_filter = st.radio("Source Type", ["All", "TABLE", "VIEW"], horizontal=True)

    results = df.copy()
    if search:
        results = results[results["COLUMN"].str.contains(search, case=False, na=False)]
    if source_filter != "All":
        results = results[results["SOURCE"] == source_filter]

    st.write(f"🔎 Found **{len(results)}** results")

    for _, row in results.iterrows():
        with st.expander(f"📌 `{row['COLUMN']}` in `{row['SCHEMA']}.{row['TABLE']}`"):
            st.markdown(f"- **Source**: `{row['SOURCE']}`")
            st.markdown(f"- **Data Type**: `{row['DATA_TYPE']}`")
            st.markdown(f"- **Short Description**: {row['DESCRIPTION'] or 'N/A'}")
            if row['LONG_DESC']:
                st.markdown(f"- **Detailed Explanation**: {row['LONG_DESC']}")

    st.download_button("📥 Download Results", data=results.to_csv(index=False).encode("utf-8"),
                       file_name="column_search_results.csv")

# --- TAB 2: USE CASE SEARCH ---
with tab2:
    st.subheader("🎯 Search by Fields Needed / Business Use Case")
    use_case = st.selectbox("Choose a business use case", mapping["USE_CASE"].dropna().unique())
    selected = mapping[mapping["USE_CASE"] == use_case]

    for _, row in selected.iterrows():
        st.markdown(f"### 🔹 {row['USE_CASE']}")
        st.markdown(f"- **Category**: `{row['CATEGORY']}`")
        st.markdown(f"- **Use Description**: {row['USE_DESC']}")
        st.markdown(f"- **Table**: `{row['TABLE']}`")
        st.markdown(f"- **Column(s)**:\n```\n{row['COLUMN']}\n```")
        st.markdown("---")

# --- TAB 3: BROWSE BY SCHEMA/TABLE ---
with tab3:
    st.subheader("📁 Explore by Table")
    schema_choice = st.selectbox("Select Schema", sorted(df["SCHEMA"].dropna().unique()))
    table_choice = st.selectbox("Select Table", sorted(df[df["SCHEMA"] == schema_choice]["TABLE"].unique()))

    filtered = df[(df["SCHEMA"] == schema_choice) & (df["TABLE"] == table_choice)]
    st.markdown(f"### Columns in `{schema_choice}.{table_choice}`")
    st.dataframe(filtered[["COLUMN", "DATA_TYPE", "DESCRIPTION", "SOURCE"]], use_container_width=True)

    meta = table_meta[table_meta["TABLE"] == table_choice]
    if not meta.empty:
        st.markdown("#### 📘 Table Description")
        st.markdown(f"**Business**: {meta['BUSINESS: What it does'].values[0]}")
        st.markdown(f"**Technical**: {meta['TECHNICAL: How it works'].values[0]}")
