from adqlm.datalab import DataLabClient

def check_metadata():
    client = DataLabClient()
    # Query to get a sample of tables and their descriptions
    query = """
    SELECT TOP 10 table_name, description 
    FROM tap_schema.tables 
    WHERE description IS NOT NULL
    """
    print("Checking tables...")
    try:
        df = client.execute_query(query)
        print(df.to_string())
    except Exception as e:
        print(f"Error querying tables: {e}")

    # Query to get a sample of columns and their descriptions
    query_cols = """
    SELECT TOP 10 table_name, column_name, description 
    FROM tap_schema.columns 
    WHERE description IS NOT NULL
    """
    print("\nChecking columns...")
    try:
        df = client.execute_query(query_cols)
        print(df.to_string())
    except Exception as e:
        print(f"Error querying columns: {e}")

if __name__ == "__main__":
    check_metadata()
