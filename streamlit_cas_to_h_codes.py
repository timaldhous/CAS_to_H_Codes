import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json

# --- 1. SET UP THE UI ---
st.title("CAS to H-Codes Tool")
st.write("Enter CAS numbers (comma-separated) to fetch GHS Hazard Statements from PubChem.")

# Use Streamlit's input instead of Python's input()
user_input = st.text_input("Please enter CAS numbers (e.g., 67-56-1, 57-27-2):", placeholder="67-56-1...")

# --- 2. YOUR FUNCTIONS (Keep these as they are) ---

def get_h_codes_from_pubchem(chemical_name):
    # ... (Your existing function code here) ...
    # Note: Keep your functions exactly as you wrote them
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    cid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{chemical_name}/cids/JSON"
    try:
        cid_response = requests.get(cid_url, headers=headers)
        cid_response.raise_for_status()
        cid_data = cid_response.json()
        cids = cid_data.get('IdentifierList', {}).get('CID')
        if not cids: return f"No CID found for {chemical_name}."
        cid = cids[0]
        
        detail_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON/"
        detail_response = requests.get(detail_url, headers=headers)
        detail_data = detail_response.json()
        
        hazard_statements_raw = []
        # (This is a simplified version of your parsing logic for brevity)
        # In your real file, paste your FULL function here.
        # [Simplified for example...]
        return "H301: Toxic if swallowed\nH311: Toxic in contact with skin" 
    except Exception as e:
        return f"Error: {e}"

h_code_controls = {
    'H200': 'Specific', 'H300': 'Specific', 'H301': 'Enhanced', 'H302': 'Standard',
    # ... (Keep your full dictionary here) ...
}

# --- 3. THE MAIN EXECUTION (Updated for Streamlit) ---

if user_input:
    cas_numbers = [c.strip() for c in user_input.split(',') if c.strip()]

    if cas_numbers:
        for cas_number in cas_numbers:
            st.markdown(f"### Results for CAS: **{cas_number}**")
            
            # Call your function
            h_code_results_string = get_h_codes_from_pubchem(cas_number)

            if h_code_results_string and "Error" not in h_code_results_string:
                statements = h_code_results_string.split('\n')
                
                for statement in statements:
                    match = re.match(r'(H\d{3}[A-Za-z]*):?\s*(.*)', statement)
                    if match:
                        h_code = match.group(1)
                        description = match.group(2).strip()
                        control_type = h_code_controls.get(h_code, 'Unknown')
                        
                        # Use st.write or st.info instead of print()
                        if control_type == 'Specific':
                            st.error(f"**{h_code}**: {description}. (Specific risk assessment required)")
                        elif control_type == 'Enhanced':
                            st.warning(f"**{h_code}**: {description}. (Apply Enhanced controls)")
                        else:
                            st.info(f"**{h_code}**: {description}. (Apply Standard controls)")
                    else:
                        st.text(statement.strip())
            else:
                st.error(f"Could not find information for {cas_number}.")
    else:
        st.warning("Please enter at least one valid CAS number.")
