import streamlit as st
import pandas as pd

st.set_page_config(page_title="📘 Data Dictionary Assistant", layout="wide")
st.title("📘 Data Dictionary Explorer")

@st.cache_data
def load_data():
    xls = pd.ExcelFile("streamlit_ready_data_dictionary.xlsx")  # <-- OR use "data_dictionary.xlsx"
    df = xls.parse("combined_data")
    mapping = xls.parse("use_cases")
    meta = xls.parse("table_meta")
    return df, mapping, meta

df, use_cases, table_meta = load_data()

# Sidebar filters
st.sidebar.header("🎛️ Filter Columns")
with st.sidebar.form("filters"):
    col_search = st.text_input("🔍 Column name contains:")
    schema = st.selectbox("📂 Schema", ["All"] + sorted(df["SCHEMA"].dropna().unique()))
    
    table_options = sorted(df[df["SCHEMA"] == schema]["TABLE"].unique()) if schema != "All" else sorted(df["TABLE"].dropna().unique())
    table = st.selectbox("📁 Table", ["All"] + table_options)
    
    dtypes = sorted(df["DATA_TYPE"].dropna().unique())
    dtype = st.multiselect("📊 Data Types", dtypes)

    source = st.radio("📌 Source", ["All", "TABLE", "VIEW"])
    go = st.form_submit_button("Apply")
    clear = st.form_submit_button("Clear Filters")

if clear:
    st.experimental_rerun()

# Apply filters
filtered = df.copy()
if col_search:
    filtered = filtered[filtered["COLUMN"].str.contains(col_search, case=False, na=False)]
if schema != "All":
    filtered = filtered[filtered["SCHEMA"] == schema]
if table != "All":
    filtered = filtered[filtered["TABLE"] == table]
if dtype:
    filtered = filtered[filtered["DATA_TYPE"].isin(dtype)]
if source != "All":
    filtered = filtered[filtered["SOURCE"] == source]

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Column Search", "🎯 Use Case Explorer", "📁 Table Viewer", "💬 Assistant"])

with tab1:
    st.subheader("📑 Filtered Columns")
    st.caption(f"Showing **{len(filtered)}** result(s)")
    for _, row in filtered.iterrows():
        with st.expander(f"📌 `{row['COLUMN']}` in `{row['SCHEMA']}.{row['TABLE']}` ({row['SOURCE']})"):
            st.markdown(f"- **Data Type**: `{row['DATA_TYPE']}`")
            st.markdown(f"- **Description**: {row['DESCRIPTION'] or '—'}")
            st.markdown(f"- **Long Description**: {row['LONG_DESC'] or '—'}")
    
    st.download_button("📥 Download Results", data=filtered.to_csv(index=False), file_name="filtered_columns.csv")

with tab2:
    st.subheader("🎯 Explore by Use Case")
    selected_case = st.selectbox("Choose a use case", sorted(use_cases["USE_CASE"].dropna().unique()))
    matches = use_cases[use_cases["USE_CASE"] == selected_case]

    for _, row in matches.iterrows():
        st.markdown(f"**🔹 {row['USE_CASE']}**")
        st.markdown(f"- 📁 Table: `{row['TABLE']}`")
        st.markdown(f"- 🔍 Field(s): `{row['COLUMN']}`")
        st.markdown(f"- 📘 Description: {row['USE_DESC']}")
        st.markdown("---")

with tab3:
    st.subheader("📁 Table Browser")
    sel_schema = st.selectbox("Select schema", sorted(df["SCHEMA"].dropna().unique()))
    table_list = sorted(df[df["SCHEMA"] == sel_schema]["TABLE"].dropna().unique())
    sel_table = st.selectbox("Select table", table_list)

    table_view = df[(df["SCHEMA"] == sel_schema) & (df["TABLE"] == sel_table)]
    st.markdown(f"### 📋 Columns in `{sel_schema}.{sel_table}`")
    st.dataframe(table_view[["COLUMN", "DATA_TYPE", "DESCRIPTION", "SOURCE"]])

    table_info = table_meta[table_meta["TABLE"] == sel_table]
    if not table_info.empty:
        st.markdown("### 🧠 Table Info")
        st.markdown(f"- **Business**: {table_info['BUSINESS: What it does'].values[0]}")
        st.markdown(f"- **Technical**: {table_info['TECHNICAL: How it works'].values[0]}")

with tab4:
    st.subheader("💬 Assistant")
    query = st.text_input("Ask (e.g., donations, user sessions, etc.)")
    if query:
        results = df[
            df["DESCRIPTION"].str.contains(query, case=False, na=False) |
            df["LONG_DESC"].str.contains(query, case=False, na=False)
        ]
        if results.empty:
            st.warning("🤖 No matches found. Try another keyword.")
        else:
            st.success(f"Found {len(results)} match(es)")
            for _, row in results.head(10).iterrows():
                with st.expander(f"💡 `{row['COLUMN']}` in `{row['SCHEMA']}.{row['TABLE']}`"):
                    st.markdown(f"- **Data Type**: `{row['DATA_TYPE']}`")
                    st.markdown(f"- **Description**: {row['DESCRIPTION'] or row['LONG_DESC'] or '—'}")
