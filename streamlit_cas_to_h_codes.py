import streamlit as st
import requests
from bs4 import BeautifulSoup # Although not explicitly used in the final version, keeping for safety if it was intended elsewhere
import re
import json

def get_cid_from_cas_pubchem(cas_number):
    """
    Fetches the PubChem CID for a given CAS number from PubChem.
    """
    headers = {'User-Agent': 'Mozilla/50 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    cid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cas/{cas_number}/cids/JSON"
    try:
        cid_response = requests.get(cid_url, headers=headers)
        cid_response.raise_for_status() # Raise an exception for HTTP errors
        cid_data = cid_response.json()
        cids = cid_data.get('IdentifierList', {}).get('CID')
        if cids:
            return cids[0]
        return None
    except requests.exceptions.RequestException:
        return None
    except json.JSONDecodeError:
        return None
    except Exception:
        return None

def get_name_from_cid_pubchem(cid):
    """
    Fetches a common chemical name for a given PubChem CID.
    """
    headers = {'User-Agent': 'Mozilla/50 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    name_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/synonyms/JSON"
    try:
        name_response = requests.get(name_url, headers=headers)
        name_response.raise_for_status()
        name_data = name_response.json()
        synonyms = name_data.get('InformationList', {}).get('Information', [{}])[0].get('Synonym', [])
        if synonyms:
            for name in synonyms:
                if name and not re.match(r'^\d{2,7}-\d{2}-\d$', name):
                    return name
            return synonyms[0]
        return None
    except requests.exceptions.RequestException:
        return None
    except json.JSONDecodeError:
        return None
    except Exception:
        return None

def get_h_codes_from_pubchem(chemical_name):
    """
    Fetches information for a given chemical name from PubChem and attempts to identify H-codes.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    cid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{chemical_name}/cids/JSON"
    try:
        cid_response = requests.get(cid_url, headers=headers)
        cid_response.raise_for_status()
        cid_data = cid_response.json()
        cids = cid_data.get('IdentifierList', {}).get('CID')
        if not cids:
            return f"No PubChem CID found for chemical name {chemical_name}."
        cid = cids[0]
    except requests.exceptions.RequestException as e:
        return f"Error fetching CID from PubChem (CID lookup): {e}"
    except json.JSONDecodeError:
        return f"Error decoding JSON for CID lookup for {chemical_name}."

    detail_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON/"
    try:
        detail_response = requests.get(detail_url, headers=headers)
        detail_response.raise_for_status()
        detail_data = detail_response.json()

        hazard_statements_raw = []
        sections = detail_data.get('Record', {}).get('Section', [])
        safety_hazard_section = None

        for section in sections:
            if section.get('TOCHeading') == 'Safety and Hazards':
                safety_hazard_section = section
                break

        if safety_hazard_section:
            hazards_identification_section = None
            for sub_section in safety_hazard_section.get('Section', []):
                if sub_section.get('TOCHeading') == 'Hazards Identification':
                    hazards_identification_section = sub_section
                    break

            if hazards_identification_section:
                ghs_classification_section = None
                for sub_sub_section in hazards_identification_section.get('Section', []):
                    if sub_sub_section.get('TOCHeading') == 'GHS Classification':
                        ghs_classification_section = sub_sub_section
                        break

                if ghs_classification_section:
                    for info_block in ghs_classification_section.get('Information', []):
                        if info_block.get('Name') == 'GHS Hazard Statements' and 'Value' in info_block:
                            for item in info_block['Value'].get('StringWithMarkup', []):
                                if 'String' in item:
                                    if re.search(r'H\d{3}[A-Za-z]*', item['String']):
                                        processed_string = item['String']
                                        processed_string = re.sub(r'\s*\(\d+(?:\.\d+)?%(?:\s*\.\s*\d+)?\)\s*:', '', processed_string)
                                        processed_string = re.sub(r'\s*\[.*?\]', '', processed_string)
                                        hazard_statements_raw.append(processed_string.strip())
                            break

        if hazard_statements_raw:
            return "\n".join(sorted(list(set(hazard_statements_raw))))
        else:
            return f"No GHS Hazard Statements (full strings) found in PubChem data for {chemical_name} (CID: {cid}) in the expected 'GHS Classification' section."

    except requests.exceptions.RequestException as e:
        return f"Error fetching detailed compound information from PubChem: {e}"
    except json.JSONDecodeError:
        return f"Error decoding JSON for detailed data for CID {cid}."
    except Exception as e:
        return f"An unexpected error occurred: {e}"


# Dictionary mapping H-codes to control types
h_code_controls = {
    'H200': 'Specific',
    'H201': 'Specific',
    'H202': 'Specific',
    'H203': 'Specific',
    'H204': 'Specific',
    'H205': 'Specific',
    'H220': 'Enhanced',
    'H221': 'Enhanced',
    'H222': 'Enhanced',
    'H223': 'Enhanced',
    'H224': 'Standard',
    'H225': 'Standard',
    'H226': 'Standard',
    'H227': 'Standard',
    'H228': 'Standard',
    'H240': 'Enhanced',
    'H241': 'Enhanced',
    'H242': 'Enhanced',
    'H250': 'Specific',
    'H251': 'Enhanced',
    'H252': 'Standard',
    'H260': 'Specific',
    'H261': 'Standard',
    'H270': 'Standard',
    'H271': 'Standard',
    'H272': 'Standard',
    'H280': 'Enhanced',
    'H281': 'Enhanced',
    'H290': 'Standard',
    'H300': 'Specific',
    'H301': 'Enhanced',
    'H302': 'Standard',
    'H303': 'Standard',
    'H304': 'Standard',
    'H305': 'Standard',
    'H310': 'Specific',
    'H311': 'Enhanced',
    'H312': 'Standard',
    'H313': 'Standard',
    'H314': 'Enhanced',
    'H315': 'Standard',
    'H316': 'Standard',
    'H317': 'Enhanced',
    'H318': 'Standard',
    'H319': 'Standard',
    'H320': 'Standard',
    'H330': 'Specific',
    'H331': 'Enhanced',
    'H332': 'Standard',
    'H333': 'Standard',
    'H334': 'Specific',
    'H335': 'Standard',
    'H336': 'Standard',
    'H340': 'Specific',
    'H341': 'Enhanced',
    'H350': 'Specific',
    'H351': 'Enhanced',
    'H360': 'Specific',
    'H361': 'Enhanced',
    'H362': 'Enhanced',
    'H370': 'Enhanced',
    'H371': 'Enhanced',
    'H372': 'Enhanced',
    'H373': 'Enhanced',
    'H400': 'Standard',
    'H401': 'Standard',
    'H402': 'Standard',
    'H410': 'Standard',
    'H411': 'Standard',
    'H412': 'Standard',
    'H413': 'Standard',
    'EUH001': 'Specific',
    'EUH006': 'Standard',
    'EUH014': 'Enhanced',
    'EUH018': 'Standard',
    'EUH019': 'Specific',
    'EUH029': 'Enhanced',
    'EUH031': 'Enhanced',
    'EUH032': 'Enhanced',
    'EUH032': 'Enhanced',
    'EUH044': 'Standard',
    'EUH059': 'Standard',
    'EUH066': 'Standard',
    'EUH070': 'Standard',
    'H350i': 'Specific',
    'H360F': 'Specific',
    'H360D': 'Specific',
    'H360FD': 'Specific',
    'H360Fd': 'Specific',
    'H360Df': 'Specific',
    'H361fd': 'Specific',
    'H420': 'Standard'
}

# @title

# 1. Set up the Title and Description
st.title("CAS to H-Codes Tool")
st.write("Enter CAS numbers below (separated by commas) to get the H-codes and recommended control types.")

# 2. Create the Input (This is your text box)
user_input = st.text_input("Input CAS Numbers", placeholder="e.g., 67-56-1, 57-27-2")

# 3. Process the Input (Your logic goes here)
if user_input:
    st.subheader("Processing Results:")
    cas_numbers_list = []
    for cas_str in user_input.split(','):
        stripped_cas = cas_str.strip()
        if stripped_cas:
            cas_numbers_list.append(stripped_cas)

    if cas_numbers_list:
        for cas_number in cas_numbers_list:
            st.markdown(f"### CAS: {cas_number}")
            h_code_results_string = get_h_codes_from_pubchem(cas_number)

            if h_code_results_string:
                statements = h_code_results_string.split('\n')
                for statement in statements:
                    match = re.match(r'(H\d{3}[A-Za-z]*):?\s*(.*)', statement)
                    if match:
                        h_code = match.group(1)
                        description = match.group(2).strip()
                        control_type = h_code_controls.get(h_code, 'Unknown')
                        if control_type == 'Specific':
                            st.markdown(f"**{h_code}**: {description}. **Specific risk assessment required.**")
                        else:
                            st.write(f"**{h_code}**: {description}. Apply {control_type} controls.")
                    else:
                        st.write(f"  - {statement.strip()}")
            else:
                st.info(f"No H-codes or safety information found for CAS number {cas_number}.")
        st.success("Processing complete for all entered CAS numbers!")
    else:
        st.warning("No valid CAS numbers were entered after parsing.")
else:
    st.info("Waiting for input... Please enter one or more CAS numbers.")
