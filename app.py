import streamlit as st
import pandas as pd

st.set_page_config(page_title="📘 Data Request Dictionary", layout="wide")
st.title("📘 Column Finder for Data Requests")

@st.cache_data
def load_data():
    # Replace with your file name if different
    xls = pd.ExcelFile("data_dictionary.xlsx")
    
    # Load and clean all sheets
    table_df = xls.parse("(Updated)tables_with_columns").rename(columns=lambda x: str(x).strip().upper())
    view_df = xls.parse("view_fields_audit").rename(columns=lambda x: str(x).strip().upper())
    mapping_df = xls.parse("Data Mapping").rename(columns=lambda x: str(x).strip().upper())
    
    # Clean and label
    table_df["SOURCE"] = "TABLE"
    view_df["SOURCE"] = "VIEW"
    
    table_df = table_df.rename(columns={
        "TABLE_SCHEMA": "SCHEMA",
        "TABLE_NAME": "TABLE",
        "COLUMN_NAME": "COLUMN",
        "DATA_TYPE": "DATA_TYPE",
        "DESCRIPTIONS": "DESCRIPTION"
    })

    view_df = view_df.rename(columns={
        "TABLE_SCHEMA": "SCHEMA",
        "TABLE_NAME": "TABLE",
        "COLUMN_NAME": "COLUMN",
        "DATA_TYPE": "DATA_TYPE"
    })
    view_df["DESCRIPTION"] = ""
    
    mapping_df = mapping_df.rename(columns={
        "FIELD NAME - FR": "COLUMN",
        "TABLE NAME - FR": "TABLE",
        "DESCRIPTION": "BUSINESS_DESCRIPTION",
        "CATEGORY": "CATEGORY"
    })

    combined = pd.concat([
        table_df[["SCHEMA", "TABLE", "COLUMN", "DATA_TYPE", "DESCRIPTION", "SOURCE"]],
        view_df[["SCHEMA", "TABLE", "COLUMN", "DATA_TYPE", "DESCRIPTION", "SOURCE"]]
    ], ignore_index=True)

    final_df = combined.merge(mapping_df[["COLUMN", "TABLE", "BUSINESS_DESCRIPTION", "CATEGORY"]],
                              on=["COLUMN", "TABLE"], how="left")

    return final_df

df = load_data()

# Sidebar Filters
st.sidebar.header("🔍 Filter Options")
col_filter = st.sidebar.text_input("Search Column Name")
table_filter = st.sidebar.text_input("Search Table Name")
schema_filter = st.sidebar.multiselect("Select Schema", df['SCHEMA'].dropna().unique())
source_type = st.sidebar.radio("Source Type", ["Both", "TABLE", "VIEW"])

# Apply filters
filtered = df.copy()
if col_filter:
    filtered = filtered[filtered["COLUMN"].str.contains(col_filter, case=False, na=False)]
if table_filter:
    filtered = filtered[filtered["TABLE"].str.contains(table_filter, case=False, na=False)]
if schema_filter:
    filtered = filtered[filtered["SCHEMA"].isin(schema_filter)]
if source_type != "Both":
    filtered = filtered[filtered["SOURCE"] == source_type]

st.write(f"🔎 Showing **{len(filtered)}** results for your query")
st.dataframe(filtered, use_container_width=True)

# Optional download
st.download_button(
    "📥 Download Filtered Results",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_data_dictionary.csv",
    mime="text/csv"
)
