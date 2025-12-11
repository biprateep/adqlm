import json
import requests
import re
from typing import List, Dict, Any

"""
Script to build the local reference documentation database.
Scrapes Q3C documentation from GitHub and provides built-in ADQL reference material.
"""

def fetch_q3c_docs() -> List[Dict[str, str]]:
    """
    Fetches and parses Q3C documentation from the official GitHub README.

    Returns:
        List[Dict]: List of documentation chunks for Q3C functions.
    """
    url = "https://raw.githubusercontent.com/segasai/q3c/refs/heads/master/README.md"
    print(f"Fetching Q3C docs from {url}...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        text = response.text
    except Exception as e:
        print(f"Error fetching Q3C docs: {e}")
        return []

    # Parse the markdown to extract functions
    # The readme format uses bullet points for functions, e.g. "- q3c_func(...) -- description"
    
    docs = []
    lines = text.split('\n')
    current_doc = None
    current_title = None
    
    for line in lines:
        line = line.strip()
        # Check for function definition start
        if line.startswith("- q3c_") and "--" in line:
            # Save previous
            if current_doc and current_title:
                docs.append({
                    "text": current_doc.strip(),
                    "source": "Q3C Documentation",
                    "title": current_title
                })
            
            # Start new
            parts = line.split("--", 1)
            current_title = parts[0].strip("- ").strip()
            current_doc = f"{current_title}\n{parts[1].strip()}\n"
            
        elif line.startswith("- q3c_"): # Case where -- might be missing or different format
             # Save previous
            if current_doc and current_title:
                docs.append({
                    "text": current_doc.strip(),
                    "source": "Q3C Documentation",
                    "title": current_title
                })
            current_title = line.strip("- ").strip()
            current_doc = line + "\n"

        else:
            # Continue current doc if it exists and line isn't a new major header
            if current_doc:
                if line.startswith("#"):
                    # New section, close current doc
                    docs.append({
                        "text": current_doc.strip(),
                        "source": "Q3C Documentation",
                        "title": current_title
                    })
                    current_doc = None
                    current_title = None
                else:
                    current_doc += line + "\n"
                
    # Add last
    if current_doc and current_title:
        docs.append({
            "text": current_doc.strip(),
            "source": "Q3C Documentation",
            "title": current_title
        })

    print(f"Parsed {len(docs)} Q3C functions.")
    return docs

def get_adql_docs() -> List[Dict[str, str]]:
    """
    Returns a list of hardcoded ADQL/SQL reference documentation.

    Returns:
         List[Dict]: List of documentation chunks for ADQL functions/syntax.
    """
    # Hardcoded ADQL specific functions that might be useful for RAG
    # Sourced from generic ADQL knowledge/docs
    
    adql_funcs = [
        {
            "title": "ADQL CIRCLE",
            "text": "CIRCLE(coordsys, ra, dec, radius)\nDescription: Returns a region defined by a circle.\nArguments:\n- coordsys: Coordinate system (e.g., 'ICRS')\n- ra: Right Ascension center (degrees)\n- dec: Declination center (degrees)\n- radius: Radius of the circle (degrees)",
            "source": "ADQL Reference"
        },
        {
            "title": "ADQL BOX",
            "text": "BOX(coordsys, ra, dec, width, height)\nDescription: Returns a region defined by a box.\nArguments:\n- coordsys: Coordinate system\n- ra: Center RA\n- dec: Center Dec\n- width: Width in degrees\n- height: Height in degrees",
            "source": "ADQL Reference"
        },
        {
            "title": "ADQL CONTAINS",
            "text": "CONTAINS(region1, region2)\nDescription: Returns 1 if region1 contains region2, otherwise 0. Often used in WHERE clause like WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 10, 20, 1)) = 1",
            "source": "ADQL Reference"
        },
        {
            "title": "ADQL POINT",
            "text": "POINT(coordsys, ra, dec)\nDescription: Returns a point geometry.\nArguments:\n- coordsys: Coordinate system\n- ra: Right Ascension\n- dec: Declination",
            "source": "ADQL Reference"
        },
        {
            "title": "SQL SELECT",
            "text": "SELECT [TOP n] column1, column2 FROM table_name WHERE condition\nDescription: Standard SQL selection. In ADQL, use TOP n to limit results instead of LIMIT n (though some implementations support LIMIT).",
            "source": "SQL Reference"
        },
         {
            "title": "SQL JOIN",
            "text": "SELECT * FROM table1 JOIN table2 ON table1.id = table2.id\nDescription: Standard SQL join. ADQL supports standard JOIN, LEFT JOIN, RIGHT JOIN.",
            "source": "SQL Reference"
        }
    ]
    return adql_funcs

def build_reference_db(output_path='reference_docs.json'):
    """
    Compiles Q3C and ADQL documentation into a JSON database.
    """
    all_docs = []
    
    # Q3C
    all_docs.extend(fetch_q3c_docs())
    
    # ADQL
    all_docs.extend(get_adql_docs())
    
    print(f"Saving {len(all_docs)} reference documents to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(all_docs, f, indent=2)
    print("Done.")

if __name__ == "__main__":
    build_reference_db()
