import json
import os
from adqlm.datalab import DataLabClient

"""
Script to build the local schema documentation database.
Fetches table and column metadata from the TAP service and saves it as a JSON file suitable for RAG ingestion.
"""

def build_schema_db(output_path='schema_docs.json'):
    """
    Connects to Data Lab, retrieves schema metadata, and saves to JSON.
    """
    client = DataLabClient()
    
    print("Fetching table metadata...")
    # Get all tables with descriptions
    tables_query = """
    SELECT schema_name, table_name, description 
    FROM tap_schema.tables 
    WHERE description IS NOT NULL
    """
    tables_df = client.execute_query(tables_query)
    
    print(f"Found {len(tables_df)} tables with descriptions.")
    
    print("Fetching column metadata...")
    # Get all columns with descriptions
    # Note: collecting all columns might be heavy, so we group by table later
    cols_query = """
    SELECT table_name, column_name, description, datatype
    FROM tap_schema.columns 
    WHERE description IS NOT NULL
    """
    cols_df = client.execute_query(cols_query)
    print(f"Found {len(cols_df)} columns with descriptions.")

    documents = []
    
    # Iterate over tables and build structured documents
    for _, row in tables_df.iterrows():
        table_name = row['table_name']
        description = row['description']
        
        # Find columns for this table
        table_cols = cols_df[cols_df['table_name'] == table_name]
        
        col_text = ""
        if not table_cols.empty:
            col_lines = []
            for _, col in table_cols.iterrows():
                col_lines.append(f"- {col['column_name']} ({col['datatype']}): {col['description']}")
            col_text = "\nColumns:\n" + "\n".join(col_lines[:20]) # Limit to top 20 cols to save tokens
            if len(col_lines) > 20:
                col_text += f"\n... ({len(col_lines) - 20} more columns)"
        
        doc_text = f"Table: {table_name}\nDescription: {description}{col_text}"
        
        documents.append({
            'text': doc_text,
            'source': f"tap_schema: {table_name}",
            'table_name': table_name
        })

    print(f"Saving {len(documents)} schema documents to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(documents, f, indent=2)
    print("Done.")

if __name__ == "__main__":
    # Ensure scripts dir exists if we were in a broader structure, but here we run from root usually
    build_schema_db()
