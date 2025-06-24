import streamlit as st
import pandas as pd

st.set_page_config(page_title="📘 Data Dictionary Explorer", layout="wide")
st.title("📘 Snowflake Data Dictionary Explorer")

@st.cache_data
def load_data():
    df = pd.read_csv("data_dictionary.csv")  # You’ll export this from the notebook
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("🔍 Search & Filter")
column_search = st.sidebar.text_input("Search Column Name")
table_search = st.sidebar.text_input("Search Table Name")
schema_filter = st.sidebar.multiselect("Schema", options=sorted(df['SCHEMA'].dropna().unique()), default=[])
source_filter = st.sidebar.radio("Source Type", ["Both", "TABLE", "VIEW"], index=0)

filtered_df = df.copy()

if column_search:
    filtered_df = filtered_df[filtered_df['COLUMN'].str.contains(column_search, case=False, na=False)]

if table_search:
    filtered_df = filtered_df[filtered_df['TABLE'].str.contains(table_search, case=False, na=False)]

if schema_filter:
    filtered_df = filtered_df[filtered_df['SCHEMA'].isin(schema_filter)]

if source_filter != "Both":
    filtered_df = filtered_df[filtered_df['SOURCE'] == source_filter]

st.write(f"🔎 Showing **{len(filtered_df)}** results")
st.dataframe(filtered_df, use_container_width=True)

# Optional download
st.download_button(
    label="📥 Download filtered results",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_data_dictionary.csv",
    mime="text/csv"
)
