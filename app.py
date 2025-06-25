import streamlit as st
import pandas as pd

st.set_page_config(page_title="📘 Data Dictionary Explorer", layout="wide")
st.title("📘 Data Dictionary Explorer – Column & Use Case Search")

@st.cache_data
def load_sheets():
    file = "data_dictionary.xlsx"  # Upload this in your Heroku repo
    xls = pd.ExcelFile(file)
    sheets = {name: xls.parse(name) for name in xls.sheet_names}
    return sheets

sheets = load_sheets()

# Extract relevant sheets
tables = sheets.get("(Updated)tables_with_columns")
views = sheets.get("view_fields_audit")
mapping = sheets.get("Data Mapping")
table_details = sheets.get("(Updated)tables")

# Normalize and rename columns
tables = tables.rename(columns={
    "TABLE_SCHEMA": "SCHEMA",
    "TABLE_NAME": "TABLE",
    "COLUMN_NAME": "COLUMN",
    "DATA_TYPE": "DATA_TYPE",
    "DESCRIPTIONS": "DESCRIPTION",
    "DESCRIPTIONS.1": "DEEP_DESCRIPTION"
})
views = views.rename(columns={
    "TABLE_SCHEMA": "SCHEMA",
    "TABLE_NAME": "TABLE",
    "COLUMN_NAME": "COLUMN",
    "DATA_TYPE": "DATA_TYPE"
})
mapping = mapping.rename(columns={
    "Fields Needed": "USE_CASE",
    "Field Name - FR": "COLUMN_RAW",
    "Table Name - FR": "TABLE_RAW",
    "Description": "USE_CASE_DESC",
    "Category": "CATEGORY"
})
table_details.columns = table_details.iloc[1]
table_details = table_details.drop(index=[0, 1])
table_details = table_details.rename(columns={"TABLE_SCHEMA": "SCHEMA", "TABLE_NAME": "TABLE"})

# Prepare merged column-level dataset
tables["SOURCE"] = "TABLE"
views["SOURCE"] = "VIEW"
views["DESCRIPTION"] = ""
views["DEEP_DESCRIPTION"] = ""

combined = pd.concat([
    tables[["SCHEMA", "TABLE", "COLUMN", "DATA_TYPE", "DESCRIPTION", "DEEP_DESCRIPTION", "SOURCE"]],
    views[["SCHEMA", "TABLE", "COLUMN", "DATA_TYPE", "DESCRIPTION", "DEEP_DESCRIPTION", "SOURCE"]]
], ignore_index=True)

# 🧠 -- MAIN TABS --
tab1, tab2, tab3 = st.tabs(["🔍 Column Search", "🎯 Use Case Search", "📁 Explore by Schema/Table"])

# -------------------- TAB 1: COLUMN SEARCH --------------------
with tab1:
    st.subheader("🔍 Search Column")
    column_query = st.text_input("Enter column name (partial OK)", "")

    filtered = combined[combined["COLUMN"].str.contains(column_query, case=False, na=False)] if column_query else combined.copy()

    st.write(f"Found **{len(filtered)}** columns matching search:")
    st.dataframe(filtered, use_container_width=True)

    st.download_button("📥 Download Results", data=filtered.to_csv(index=False).encode("utf-8"),
                       file_name="filtered_columns.csv", mime="text/csv")

# -------------------- TAB 2: USE CASE SEARCH --------------------
with tab2:
    st.subheader("🎯 Search by Fields Needed (Use Case)")
    use_case = st.selectbox("Choose a business use case", options=mapping["USE_CASE"].dropna().unique())

    selected = mapping[mapping["USE_CASE"] == use_case]

    for i, row in selected.iterrows():
        st.markdown(f"### 🔹 {row['USE_CASE']}")
        st.write(f"**Category**: {row['CATEGORY']}")
        st.write(f"**Description**: {row['USE_CASE_DESC']}")
        st.write(f"**Suggested Table**: `{row['TABLE_RAW']}`")
        st.write(f"**Suggested Column(s)**:\n```\n{row['COLUMN_RAW']}\n```")
        st.markdown("---")

# -------------------- TAB 3: EXPLORE BY SCHEMA/TABLE --------------------
with tab3:
    st.subheader("📁 Explore by Schema or Table")

    schema = st.selectbox("Select Schema", sorted(combined["SCHEMA"].dropna().unique()))
    tables_in_schema = combined[combined["SCHEMA"] == schema]["TABLE"].unique()
    selected_table = st.selectbox("Select Table", sorted(tables_in_schema))

    df_table = combined[(combined["SCHEMA"] == schema) & (combined["TABLE"] == selected_table)]

    st.write(f"🔹 Showing columns in `{schema}.{selected_table}`:")
    st.dataframe(df_table, use_container_width=True)

    # Extra: table-level details if available
    if not table_details.empty:
        desc_row = table_details[table_details["TABLE"] == selected_table]
        if not desc_row.empty:
            st.markdown("### 📝 Table Description")
            st.write(desc_row["BUSINESS: What it does"].values[0])
            st.write(desc_row["TECHNICAL: How it works"].values[0])
