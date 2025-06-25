import pandas as pd

# Load your original Excel file
xls = pd.ExcelFile("data_dictionary.xlsx")

# --- Step 1: Clean table column metadata ---
df_tables = xls.parse("(Updated)tables_with_columns")
df_tables = df_tables.rename(columns={
    "TABLE_SCHEMA": "SCHEMA",
    "TABLE_NAME": "TABLE",
    "COLUMN_NAME": "COLUMN",
    "DATA_TYPE": "DATA_TYPE",
    "DESCRIPTIONS": "DESCRIPTION",
    "DESCRIPTIONS.1": "LONG_DESC"
})
df_tables["SOURCE"] = "TABLE"

# --- Step 2: Clean view column metadata ---
df_views = xls.parse("view_fields_audit")
df_views = df_views.rename(columns={
    "TABLE_SCHEMA": "SCHEMA",
    "TABLE_NAME": "TABLE",
    "COLUMN_NAME": "COLUMN",
    "DATA_TYPE": "DATA_TYPE"
})
df_views["DESCRIPTION"] = ""
df_views["LONG_DESC"] = ""
df_views["SOURCE"] = "VIEW"

# --- Step 3: Combine table + view metadata ---
combined_df = pd.concat([
    df_tables[["SCHEMA", "TABLE", "COLUMN", "DATA_TYPE", "DESCRIPTION", "LONG_DESC", "SOURCE"]],
    df_views[["SCHEMA", "TABLE", "COLUMN", "DATA_TYPE", "DESCRIPTION", "LONG_DESC", "SOURCE"]]
], ignore_index=True)

# --- Step 4: Clean use case mappings ---
df_mapping = xls.parse("Data Mapping")
df_mapping = df_mapping.rename(columns={
    "Fields Needed": "USE_CASE",
    "Description": "USE_DESC",
    "Category": "CATEGORY",
    "Table Name - FR": "TABLE",
    "Field Name - FR": "COLUMN"
})

# --- Step 5: Clean table-level metadata ---
df_meta = xls.parse("(Updated)tables", skiprows=2)
df_meta.columns = df_meta.iloc[0]
df_meta = df_meta.drop(index=df_meta.index[0])
df_meta = df_meta.rename(columns={
    "TABLE_SCHEMA": "SCHEMA",
    "TABLE_NAME": "TABLE"
})

# --- Step 6: Save cleaned result ---
with pd.ExcelWriter("streamlit_ready_data_dictionary.xlsx", engine="openpyxl") as writer:
    combined_df.to_excel(writer, sheet_name="combined_data", index=False)
    df_mapping.to_excel(writer, sheet_name="use_cases", index=False)
    df_meta.to_excel(writer, sheet_name="table_meta", index=False)

print("✅ Cleaned Excel saved as: streamlit_ready_data_dictionary.xlsx")
