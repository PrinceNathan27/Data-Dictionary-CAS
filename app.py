import streamlit as st
import pandas as pd

st.set_page_config(page_title="📘 Data Dictionary Assistant", layout="wide")
st.title("📘 Data Dictionary Assistant")

@st.cache_data
def load_data():
    xls = pd.ExcelFile("data_dictionary.xlsx")
    df = xls.parse("(Updated)tables_with_columns")
    views = xls.parse("view_fields_audit")
    mapping = xls.parse("Data Mapping")
    meta = xls.parse("(Updated)tables", skiprows=2)

    df = df.rename(columns={
        "TABLE_SCHEMA": "SCHEMA", "TABLE_NAME": "TABLE", "COLUMN_NAME": "COLUMN",
        "DATA_TYPE": "DATA_TYPE", "DESCRIPTIONS": "DESCRIPTION", "DESCRIPTIONS.1": "LONG_DESC"
    })
    df["SOURCE"] = "TABLE"

    views = views.rename(columns={
        "TABLE_SCHEMA": "SCHEMA", "TABLE_NAME": "TABLE", "COLUMN_NAME": "COLUMN",
        "DATA_TYPE": "DATA_TYPE"
    })
    views["DESCRIPTION"] = ""
    views["LONG_DESC"] = ""
    views["SOURCE"] = "VIEW"

    combined = pd.concat([
        df[["SCHEMA", "TABLE", "COLUMN", "DATA_TYPE", "DESCRIPTION", "LONG_DESC", "SOURCE"]],
        views[["SCHEMA", "TABLE", "COLUMN", "DATA_TYPE", "DESCRIPTION", "LONG_DESC", "SOURCE"]]
    ], ignore_index=True)

    mapping = mapping.rename(columns={
        "Fields Needed": "USE_CASE", "Description": "USE_DESC", "Category": "CATEGORY",
        "Table Name - FR": "TABLE", "Field Name - FR": "COLUMN"
    })

    meta.columns = meta.iloc[0]
    meta = meta.drop(index=meta.index[0])
    meta = meta.rename(columns={"TABLE_SCHEMA": "SCHEMA", "TABLE_NAME": "TABLE"})

    return combined, mapping, meta

df, use_cases, table_meta = load_data()

# ---------- Sidebar Filters ----------
st.sidebar.header("🎛️ Filter Columns")
with st.sidebar.form("filter_form"):
    col_search = st.text_input("🔍 Column name contains:")
    schema_sel = st.selectbox("📂 Schema", ["All"] + sorted(df["SCHEMA"].dropna().unique()))
    
    table_list = sorted(df[df["SCHEMA"] == schema_sel]["TABLE"].dropna().unique()) if schema_sel != "All" else sorted(df["TABLE"].dropna().unique())
    table_sel = st.selectbox("📁 Table", ["All"] + table_list)

    dtypes = sorted(df["DATA_TYPE"].dropna().unique())
    dtype_sel = st.multiselect("📊 Data Types", dtypes)

    source_sel = st.radio("📌 Source", ["All", "TABLE", "VIEW"])
    apply = st.form_submit_button("✅ Apply Filters")
    reset = st.form_submit_button("🔄 Clear All Filters")

if reset:
    st.experimental_rerun()

# ---------- Filter Logic ----------
filtered_df = df.copy()
if col_search:
    filtered_df = filtered_df[filtered_df["COLUMN"].str.contains(col_search, case=False, na=False)]
if schema_sel != "All":
    filtered_df = filtered_df[filtered_df["SCHEMA"] == schema_sel]
if table_sel != "All":
    filtered_df = filtered_df[filtered_df["TABLE"] == table_sel]
if dtype_sel:
    filtered_df = filtered_df[filtered_df["DATA_TYPE"].isin(dtype_sel)]
if source_sel != "All":
    filtered_df = filtered_df[filtered_df["SOURCE"] == source_sel]

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Column Search", "🎯 Use Case Explorer", "📁 Schema Viewer", "💬 Ask Assistant"])

# ---------- Tab 1: Column Search ----------
with tab1:
    st.subheader("🔍 Filtered Columns")
    st.caption(f"Showing **{len(filtered_df)}** result(s)")
    for _, row in filtered_df.iterrows():
        with st.expander(f"📌 `{row['COLUMN']}` from `{row['SCHEMA']}.{row['TABLE']}` ({row['SOURCE']})"):
            st.markdown(f"- **Data Type**: `{row['DATA_TYPE']}`")
            st.markdown(f"- **Description**: {row['DESCRIPTION'] or '—'}")
            if pd.notna(row["LONG_DESC"]):
                st.markdown(f"- **Long Description**: {row['LONG_DESC']}")

    st.download_button(
        label="📥 Download Results",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_data_dictionary.csv"
    )

# ---------- Tab 2: Use Case Explorer ----------
with tab2:
    st.subheader("🎯 Explore by Business Use Case")
    use_case = st.selectbox("Choose a Use Case", sorted(use_cases["USE_CASE"].dropna().unique()))
    matched = use_cases[use_cases["USE_CASE"] == use_case]

    for _, row in matched.iterrows():
        st.markdown(f"### 🔹 {row['USE_CASE']}")
        st.markdown(f"- **Category**: `{row['CATEGORY']}`")
        st.markdown(f"- **Description**: {row['USE_DESC']}")
        st.markdown(f"- **Table**: `{row['TABLE']}`")
        st.markdown(f"- **Column(s)**: `{row['COLUMN']}`")
        st.markdown("---")

# ---------- Tab 3: Schema/Table Viewer ----------
with tab3:
    st.subheader("📁 Browse Schema & Table")
    schema = st.selectbox("Select Schema", sorted(df["SCHEMA"].dropna().unique()), key="schema_select")
    tables = sorted(df[df["SCHEMA"] == schema]["TABLE"].dropna().unique())
    table = st.selectbox("Select Table", tables, key="table_select")

    view = df[(df["SCHEMA"] == schema) & (df["TABLE"] == table)]
    st.markdown(f"### 📋 Columns in `{schema}.{table}`")
    st.dataframe(view[["COLUMN", "DATA_TYPE", "DESCRIPTION", "SOURCE"]], use_container_width=True)

    meta = table_meta[table_meta["TABLE"] == table]
    if not meta.empty:
        st.markdown("#### 📘 Table Description")
        st.markdown(f"- **Business**: {meta['BUSINESS: What it does'].values[0]}")
        st.markdown(f"- **Technical**: {meta['TECHNICAL: How it works'].values[0]}")

# ---------- Tab 4: Assistant Chat ----------
with tab4:
    st.subheader("💬 Ask Assistant")
    st.caption("Ask something like: *“Which columns help track donations?”* or *“User engagement fields?”*")
    query = st.text_input("Your question:")
    
    if query:
        suggestion = df[
            df["DESCRIPTION"].str.contains(query, case=False, na=False) |
            df["LONG_DESC"].str.contains(query, case=False, na=False)
        ]

        if not suggestion.empty:
            st.success(f"🔍 Found {len(suggestion)} potential columns:")
            for _, row in suggestion.head(10).iterrows():
                with st.expander(f"{row['COLUMN']} in `{row['SCHEMA']}.{row['TABLE']}`"):
                    st.markdown(f"- **Data Type:** `{row['DATA_TYPE']}`")
                    st.markdown(f"- **Description:** {row['DESCRIPTION'] or row['LONG_DESC']}")
        else:
            st.warning("🤖 I couldn’t find a match. Try rephrasing your question.")
