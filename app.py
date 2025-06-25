import streamlit as st
import pandas as pd

st.set_page_config(page_title="📘 Data Dictionary Assistant", layout="wide")
st.title("📘 Data Dictionary Assistant")

@st.cache_data
def load_data():
    xls = pd.ExcelFile("data_dictionary.xlsx")

    # Table columns
    df = xls.parse("(Updated)tables_with_columns")
    df = df.rename(columns={
        "TABLE_SCHEMA": "SCHEMA", "TABLE_NAME": "TABLE", "COLUMN_NAME": "COLUMN",
        "DATA_TYPE": "DATA_TYPE", "DESCRIPTIONS": "DESCRIPTION", "DESCRIPTIONS.1": "LONG_DESC"
    })
    df["SOURCE"] = "TABLE"

    # Views
    views = xls.parse("view_fields_audit")
    views = views.rename(columns={
        "TABLE_SCHEMA": "SCHEMA", "TABLE_NAME": "TABLE", "COLUMN_NAME": "COLUMN",
        "DATA_TYPE": "DATA_TYPE"
    })
    views["DESCRIPTION"] = ""
    views["LONG_DESC"] = ""
    views["SOURCE"] = "VIEW"

    # Combine both
    combined = pd.concat([
        df[["SCHEMA", "TABLE", "COLUMN", "DATA_TYPE", "DESCRIPTION", "LONG_DESC", "SOURCE"]],
        views[["SCHEMA", "TABLE", "COLUMN", "DATA_TYPE", "DESCRIPTION", "LONG_DESC", "SOURCE"]]
    ], ignore_index=True)

    # Use Case Mapping
    mapping = xls.parse("Data Mapping")
    mapping = mapping.rename(columns={
        "Fields Needed": "USE_CASE", "Description": "USE_DESC", "Category": "CATEGORY",
        "Table Name - FR": "TABLE", "Field Name - FR": "COLUMN"
    })

    # Table-level metadata (clean headers)
    raw_meta = xls.parse("(Updated)tables", skiprows=2)
    raw_meta.columns = raw_meta.iloc[0]
    raw_meta = raw_meta.drop(index=raw_meta.index[0])
    raw_meta.columns = raw_meta.columns.str.strip().str.upper()

    return combined, mapping, raw_meta

df, use_cases, table_meta = load_data()

# -------------- Sidebar Filters --------------
st.sidebar.header("🎛️ Filter Columns")
with st.sidebar.form("filters"):
    col_filter = st.text_input("🔍 Column name contains:")
    schema = st.selectbox("📂 Schema", ["All"] + sorted(df["SCHEMA"].dropna().unique()))
    
    table_list = sorted(df[df["SCHEMA"] == schema]["TABLE"].dropna().unique()) if schema != "All" else sorted(df["TABLE"].dropna().unique())
    table = st.selectbox("📁 Table", ["All"] + table_list)

    dtype_sel = st.multiselect("📊 Data Types", sorted(df["DATA_TYPE"].dropna().unique()))
    source_sel = st.radio("📌 Source", ["All", "TABLE", "VIEW"])

    submitted = st.form_submit_button("✅ Apply")
    if st.form_submit_button("🔄 Clear"):
        st.experimental_rerun()

# -------------- Filter Logic --------------
filtered = df.copy()
if col_filter:
    filtered = filtered[filtered["COLUMN"].str.contains(col_filter, case=False, na=False)]
if schema != "All":
    filtered = filtered[filtered["SCHEMA"] == schema]
if table != "All":
    filtered = filtered[filtered["TABLE"] == table]
if dtype_sel:
    filtered = filtered[filtered["DATA_TYPE"].isin(dtype_sel)]
if source_sel != "All":
    filtered = filtered[filtered["SOURCE"] == source_sel]

# -------------- Tabs --------------
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Column Search", "🎯 Use Case Explorer", "📁 Schema Viewer", "💬 Ask Assistant"])

# -------- Tab 1: Column Search --------
with tab1:
    st.subheader("🔍 Filtered Column Results")
    st.caption(f"Showing **{len(filtered)}** result(s)")
    for _, row in filtered.iterrows():
        with st.expander(f"📌 `{row['COLUMN']}` in `{row['SCHEMA']}.{row['TABLE']}` ({row['SOURCE']})"):
            st.markdown(f"- **Data Type:** `{row['DATA_TYPE']}`")
            st.markdown(f"- **Short Description:** {row['DESCRIPTION'] or '—'}")
            st.markdown(f"- **Long Description:** {row['LONG_DESC'] or '—'}")

    st.download_button(
        label="📥 Download Filtered Data",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_columns.csv"
    )

# -------- Tab 2: Use Case Explorer --------
with tab2:
    st.subheader("🎯 Business Use Case Mapping")
    use_case = st.selectbox("Select a Use Case", sorted(use_cases["USE_CASE"].dropna().unique()))
    use_rows = use_cases[use_cases["USE_CASE"] == use_case]

    for _, row in use_rows.iterrows():
        st.markdown(f"### 🔹 `{row['USE_CASE']}`")
        st.markdown(f"- **Category**: `{row['CATEGORY']}`")
        st.markdown(f"- **Description**: {row['USE_DESC']}")
        st.markdown(f"- **Table**: `{row['TABLE']}`")
        st.markdown(f"- **Column**: `{row['COLUMN']}`")
        st.markdown("---")

# -------- Tab 3: Schema Viewer --------
with tab3:
    st.subheader("📁 Browse Tables by Schema")
    schema_sel = st.selectbox("Select Schema", sorted(df["SCHEMA"].dropna().unique()), key="schema_tab3")
    table_sel = st.selectbox("Select Table", sorted(df[df["SCHEMA"] == schema_sel]["TABLE"].dropna().unique()), key="table_tab3")

    view = df[(df["SCHEMA"] == schema_sel) & (df["TABLE"] == table_sel)]
    st.markdown(f"### Columns in `{schema_sel}.{table_sel}`")
    st.dataframe(view[["COLUMN", "DATA_TYPE", "DESCRIPTION", "SOURCE"]], use_container_width=True)

    if "TABLE" in table_meta.columns:
        meta = table_meta[table_meta["TABLE"] == table_sel]
        if not meta.empty:
            st.markdown("#### 📘 Table Description")
            st.markdown(f"- **Business Purpose**: {meta.iloc[0].get('BUSINESS: WHAT IT DOES', '—')}")
            st.markdown(f"- **Technical Details**: {meta.iloc[0].get('TECHNICAL: HOW IT WORKS', '—')}")
    else:
        st.warning("⚠️ 'TABLE' column not found in table metadata.")

# -------- Tab 4: Ask Assistant --------
with tab4:
    st.subheader("💬 Ask Assistant")
    st.caption("Type something like: *which fields show subscription data?*")
    query = st.text_input("Your Question:")
    if query:
        result = df[
            df["DESCRIPTION"].str.contains(query, case=False, na=False) |
            df["LONG_DESC"].str.contains(query, case=False, na=False)
        ]
        if not result.empty:
            st.success(f"Found {len(result)} matching fields")
            for _, r in result.head(10).iterrows():
                with st.expander(f"📍 {r['COLUMN']} in {r['SCHEMA']}.{r['TABLE']}"):
                    st.markdown(f"- **Data Type:** `{r['DATA_TYPE']}`")
                    st.markdown(f"- **Description:** {r['DESCRIPTION'] or r['LONG_DESC'] or '—'}")
        else:
            st.warning("❗ No matching fields found. Try rewording your query.")
