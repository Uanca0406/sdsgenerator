import streamlit as st
import requests
import pandas as pd
import pubchempy as pcp
from PIL import Image
from io import BytesIO

# Set page config
st.set_page_config(
    page_title="Chemical Safety Checker",
    page_icon="⚠️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 24px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .hazard-icon {
        font-size: 24px;
        margin-right: 10px;
    }
    .ppe-icon {
        font-size: 20px;
        margin-right: 5px;
    }
    .warning-box {
        border-left: 4px solid #FFA500;
        padding: 10px;
        background-color: #FFF3CD;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

def get_pubchem_data(chemical_name):
    """Fetch chemical data from PubChem API"""
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    
    # First get CID (Compound ID)
    cid_url = f"{base_url}/compound/name/{chemical_name}/cids/JSON"
    try:
        response = requests.get(cid_url)
        if response.status_code == 200:
            cid = response.json()['IdentifierList']['CID'][0]
            
            # Get compound information
            compound_url = f"{base_url}/compound/cid/{cid}/JSON"
            compound_response = requests.get(compound_url)
            
            if compound_response.status_code == 200:
                compound_data = compound_response.json()
                return {
                    'success': True,
                    'data': compound_data
                }
            else:
                return {
                    'success': False,
                    'error': "Failed to fetch compound details"
                }
        else:
            return {
                'success': False,
                'error': "Chemical not found or error in PubChem API"
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def interpret_hazards(compound_data):
    """Interpret hazard information from PubChem data"""
    hazards = []
    
    try:
        # Check for GHS Hazard Codes
        if 'PC_Compounds' in compound_data:
            compound = compound_data['PC_Compounds'][0]
            
            # Get GHS information if available
            if 'coords' in compound and isinstance(compound['coords'], list):
                for coord in compound['coords']:
                    if 'type' in coord and coord['type'] == 2:  # GHS Hazard Codes
                        hazards.append(coord['aid'])
            
            # Interpret common hazards based on PubChem data
            if 'props' in compound:
                for prop in compound['props']:
                    if 'urn' in prop and 'label' in prop['urn']:
                        if 'Hazard Statements' in prop['urn']['label']:
                            hazard_statements = prop['value']['sval']
                            hazards.extend(hazard_statements.split(';'))
    
    except Exception as e:
        st.warning(f"Error interpreting hazards: {str(e)}")
    
    return hazards

def hazard_to_symbol(hazard_code):
    """Convert hazard code to symbol and description"""
    hazard_map = {
        'H200': {'symbol': '💥', 'name': 'Explosive'},
        'H201': {'symbol': '💥', 'name': 'Explosive: mass explosion hazard'},
        'H202': {'symbol': '💥', 'name': 'Explosive: severe projection hazard'},
        'H220': {'symbol': '🔥', 'name': 'Extremely flammable gas'},
        'H221': {'symbol': '🔥', 'name': 'Flammable gas'},
        'H222': {'symbol': '🔥', 'name': 'Extremely flammable aerosol'},
        'H223': {'symbol': '🔥', 'name': 'Flammable aerosol'},
        'H224': {'symbol': '🔥', 'name': 'Extremely flammable liquid and vapor'},
        'H225': {'symbol': '🔥', 'name': 'Highly flammable liquid and vapor'},
        'H226': {'symbol': '🔥', 'name': 'Flammable liquid and vapor'},
        'H228': {'symbol': '🔥', 'name': 'Flammable solid'},
        'H240': {'symbol': '💥🔥', 'name': 'Heating may cause an explosion'},
        'H241': {'symbol': '💥🔥', 'name': 'Heating may cause a fire or explosion'},
        'H242': {'symbol': '🔥', 'name': 'Heating may cause a fire'},
        'H250': {'symbol': '🔥', 'name': 'Catches fire spontaneously if exposed to air'},
        'H251': {'symbol': '🔥', 'name': 'Self-heating; may catch fire'},
        'H252': {'symbol': '🔥', 'name': 'Self-heating in large quantities; may catch fire'},
        'H260': {'symbol': '💧🔥', 'name': 'In contact with water releases flammable gases which may ignite spontaneously'},
        'H261': {'symbol': '💧🔥', 'name': 'In contact with water releases flammable gas'},
        'H270': {'symbol': '🔥🔄', 'name': 'May cause or intensify fire; oxidizer'},
        'H271': {'symbol': '🔥❗', 'name': 'May cause fire or explosion; strong oxidizer'},
        'H272': {'symbol': '🔥', 'name': 'May intensify fire; oxidizer'},
        'H280': {'symbol': '🏺', 'name': 'Contains gas under pressure; may explode if heated'},
        'H281': {'symbol': '🏺❄️', 'name': 'Contains refrigerated gas; may cause cryogenic burns or injury'},
        'H290': {'symbol': '⚡', 'name': 'May be corrosive to metals'},
        'H300': {'symbol': '☠️', 'name': 'Fatal if swallowed'},
        'H301': {'symbol': '☠️', 'name': 'Toxic if swallowed'},
        'H302': {'symbol': '⚠️', 'name': 'Harmful if swallowed'},
        'H304': {'symbol': '⚠️', 'name': 'May be fatal if swallowed and enters airways'},
        'H310': {'symbol': '☠️', 'name': 'Fatal in contact with skin'},
        'H311': {'symbol': '☠️', 'name': 'Toxic in contact with skin'},
        'H312': {'symbol': '⚠️', 'name': 'Harmful in contact with skin'},
        'H314': {'symbol': '⚠️', 'name': 'Causes severe skin burns and eye damage'},
        'H315': {'symbol': '⚠️', 'name': 'Causes skin irritation'},
        'H317': {'symbol': '⚠️', 'name': 'May cause an allergic skin reaction'},
        'H318': {'symbol': '⚠️👁️', 'name': 'Causes serious eye damage'},
        'H319': {'symbol': '⚠️👁️', 'name': 'Causes serious eye irritation'},
        'H330': {'symbol': '☠️', 'name': 'Fatal if inhaled'},
        'H331': {'symbol': '☠️', 'name': 'Toxic if inhaled'},
        'H332': {'symbol': '⚠️', 'name': 'Harmful if inhaled'},
        'H334': {'symbol': '⚠️', 'name': 'May cause allergy or asthma symptoms or breathing difficulties if inhaled'},
        'H335': {'symbol': '⚠️', 'name': 'May cause respiratory irritation'},
        'H336': {'symbol': '⚠️', 'name': 'May cause drowsiness or dizziness'},
        'H340': {'symbol': '⚠️', 'name': 'May cause genetic defects'},
        'H341': {'symbol': '⚠️', 'name': 'Suspected of causing genetic defects'},
        'H350': {'symbol': '⚠️', 'name': 'May cause cancer'},
        'H351': {'symbol': '⚠️', 'name': 'Suspected of causing cancer'},
        'H360': {'symbol': '⚠️', 'name': 'May damage fertility or the unborn child'},
        'H361': {'symbol': '⚠️', 'name': 'Suspected of damaging fertility or the unborn child'},
        'H362': {'symbol': '⚠️', 'name': 'May cause harm to breast-fed children'},
        'H370': {'symbol': '⚠️🧠', 'name': 'Causes damage to organs'},
        'H371': {'symbol': '⚠️🧠', 'name': 'May cause damage to organs'},
        'H372': {'symbol': '⚠️🧠', 'name': 'Causes damage to organs through prolonged or repeated exposure'},
        'H373': {'symbol': '⚠️🧠', 'name': 'May cause damage to organs through prolonged or repeated exposure'},
        'H400': {'symbol': '🐟', 'name': 'Very toxic to aquatic life'},
        'H401': {'symbol': '🐟', 'name': 'Toxic to aquatic life'},
        'H402': {'symbol': '🐟', 'name': 'Harmful to aquatic life'},
        'H410': {'symbol': '🐟💀', 'name': 'Very toxic to aquatic life with long lasting effects'},
        'H411': {'symbol': '🐟💀', 'name': 'Toxic to aquatic life with long lasting effects'},
        'H412': {'symbol': '🐟💀', 'name': 'Harmful to aquatic life with long lasting effects'},
        'H413': {'symbol': '🐟', 'name': 'May cause long lasting harmful effects to aquatic life'},
    }
    
    return hazard_map.get(hazard_code, {'symbol': '❓', 'name': 'Unknown hazard'})

def get_ppe_recommendations(hazards):
    """Determine recommended PPE based on hazards"""
    ppe_recommendations = []
    
    # Basic PPE that should always be considered
    ppe_recommendations.append({
        'item': 'Safety Glasses',
        'description': 'Basic eye protection'
    })
    
    # Add PPE based on specific hazards
    for hazard in hazards:
        if isinstance(hazard, str):
            hazard_code = hazard.split(':')[0] if ':' in hazard else hazard
            
            if hazard_code in ['H300', 'H301', 'H302', 'H304', 'H310', 'H311', 'H312', 'H330', 'H331', 'H332']:
                ppe_recommendations.append({
                    'item': 'Respirator',
                    'description': 'Protection against inhalation of toxic substances'
                })
                ppe_recommendations.append({
                    'item': 'Gloves',
                    'description': 'Chemical-resistant gloves'
                })
            
            if hazard_code in ['H314', 'H315', 'H318', 'H319']:
                ppe_recommendations.append({
                    'item': 'Face Shield',
                    'description': 'Additional face and eye protection'
                })
                ppe_recommendations.append({
                    'item': 'Chemical Apron',
                    'description': 'Protection against skin contact'
                })
            
            if hazard_code in ['H220', 'H221', 'H222', 'H223', 'H224', 'H225', 'H226']:
                ppe_recommendations.append({
                    'item': 'Flame-Resistant Clothing',
                    'description': 'Protection against fire hazards'
                })
            
            if hazard_code in ['H340', 'H341', 'H350', 'H351']:
                ppe_recommendations.append({
                    'item': 'Full Body Suit',
                    'description': 'Complete protection against carcinogens'
                })
    
    # Remove duplicates
    unique_ppe = []
    seen = set()
    for rec in ppe_recommendations:
        if rec['item'] not in seen:
            seen.add(rec['item'])
            unique_ppe.append(rec)
    
    return unique_ppe

def generate_sds(chemical_name, hazards, ppe_recommendations):
    """Generate a simple safety data sheet"""
    sds_content = f"""
    <div style="border: 1px solid #ddd; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
        <h1>Simple Safety Data Sheet (SDS)</h1>
        <h2>1. Identification</h2>
        <p><strong>Product Name:</strong> {chemical_name}</p>
        
        <h2>2. Hazard Identification</h2>
        <p><strong>Hazard Classification:</strong></p>
        <ul>
    """
    
    for hazard in hazards:
        hazard_info = hazard_to_symbol(hazard)
        sds_content += f"""
            <li>{hazard_info['symbol']} {hazard_info['name']} ({hazard})</li>
        """
    
    sds_content += """
        </ul>
        
        <h2>3. Composition/Information on Ingredients</h2>
        <p>Chemical information not available in this simplified version.</p>
        
        <h2>4. First-Aid Measures</h2>
        <p>If exposed:</p>
        <ul>
            <li>Inhalation: Move to fresh air immediately</li>
            <li>Skin contact: Wash with soap and water</li>
            <li>Eye contact: Flush with water for at least 15 minutes</li>
            <li>Ingestion: Seek medical attention immediately</li>
        </ul>
        
        <h2>5. Fire-Fighting Measures</h2>
        <p>Use appropriate fire extinguishing media for the surrounding fire.</p>
        
        <h2>6. Accidental Release Measures</h2>
        <p>Wear proper PPE, contain spill, and dispose according to regulations.</p>
        
        <h2>7. Handling and Storage</h2>
        <p>Store in a cool, dry, well-ventilated area away from incompatible materials.</p>
        
        <h2>8. Exposure Controls/Personal Protection</h2>
        <p><strong>Recommended PPE:</strong></p>
        <ul>
    """
    
    for ppe in ppe_recommendations:
        sds_content += f"""
            <li>{ppe['item']}: {ppe['description']}</li>
        """
    
    sds_content += """
        </ul>
        
        <h2>9-16. Other Sections</h2>
        <p>For complete SDS, consult official sources.</p>
    </div>
    """
    
    return sds_content

def main():
    st.title("Pengecek Keselamatan Bahan Kimia (SDS Generator)")
    st.markdown("Aplikasi ini membantu memeriksa simbol bahaya dan menghasilkan lembar keselamatan sederhana untuk bahan kimia.")
    
    # Create tabs
    tab1, tab2 = st.tabs(["Chemical Safety Checker", "About"])
    
    with tab1:
        # Chemical input
        chemical_name = st.text_input("Masukkan nama bahan kimia:", placeholder="e.g., Acetone, Ethanol")
        
        if chemical_name:
            st.markdown(f"### Hasil untuk: {chemical_name}")
            
            # Fetch PubChem data
            with st.spinner("Mencari informasi bahan kimia..."):
                pubchem_data = get_pubchem_data(chemical_name)
                
                if pubchem_data['success']:
                    # Extract hazards
                    hazards = interpret_hazards(pubchem_data['data'])
                    
                    if hazards:
                        # Display hazard symbols
                        st.markdown("### Simbol Bahaya:")
                        
                        cols = st.columns(4)
                        unique_hazards = set()
                        for hazard in hazards:
                            if isinstance(hazard, str):
                                hazard_code = hazard.split(':')[0] if ':' in hazard else hazard
                                if hazard_code not in unique_hazards:
                                    unique_hazards.add(hazard_code)
                                    hazard_info = hazard_to_symbol(hazard_code)
                                    
                                    with cols[0]:
                                        st.markdown(f"""
                                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                            <span style="font-size: 24px; margin-right: 10px;">{hazard_info['symbol']}</span>
                                            <span>{hazard_info['name']}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                    
                        # Display PPE recommendations
                        ppe_recommendations = get_ppe_recommendations(hazards)
                        
                        st.markdown("### Alat Pelindung Diri (APD) yang Direkomendasikan:")
                        ppe_html = "<div style='display: flex; flex-wrap: wrap; gap: 20px;'>"
                        for ppe in ppe_recommendations:
                            ppe_html += f"""
                            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; width: 200px;">
                                <div style="font-weight: bold; margin-bottom: 5px;">{ppe['item']}</div>
                                <div style="font-size: 0.9em;">{ppe['description']}</div>
                            </div>
                            """
                        ppe_html += "</div>"
                        st.markdown(ppe_html, unsafe_allow_html=True)
                        
                        # Generate SDS button
                        if st.button("Generate Simple Safety Data Sheet"):
                            sds_content = generate_sds(chemical_name, hazards, ppe_recommendations)
                            st.markdown(sds_content, unsafe_allow_html=True)
                    else:
                        st.warning("Tidak ada informasi bahaya yang ditemukan untuk bahan kimia ini.")
                        st.info("""Beberapa bahan kimia mungkin tidak memiliki informasi bahaya yang terdokumentasi dengan baik.
                        Selalu gunakan tindakan pencegahan umum ketika menangani bahan kimia.""")
                else:
                    st.error(f"Gagal mengambil data: {pubchem_data['error']}")
                    st.info("Pastikan nama bahan kimia yang dimasukkan benar atau coba nama alternatif.")
    
    with tab2:
        st.markdown("""
        ## Tentang Aplikasi Ini
        
        Aplikasi **Pengecek Keselamatan Bahan Kimia (SDS Generator)** membantu pengguna untuk:
        - Memeriksa simbol bahaya bahan kimia
        - Mengetahui alat pelindung diri (APD) yang diperlukan
        - Membuat lembar keselamatan sederhana
        
        ### Integrasi API
        Aplikasi ini menggunakan data dari:
        - [PubChem API](https://pubchem.ncbi.nlm.nih.gov/) - Basis data senyawa kimia dari National Library of Medicine
        
        ### Tindakan Pencegahan
        - Informasi yang diberikan bersifat referensi dan tidak menggantikan SDS resmi
        - Selalu konsultasikan dengan ahli keselamatan sebelum menangani bahan kimia
        - Untuk penggunaan laboratorium atau industri, selalu periksa SDS resmi dari produsen
        
        ### Panduan Penggunaan
        1. Masukkan nama bahan kimia
        2. Sistem akan menampilkan simbol bahaya dan rekomendasi APD
        3. Klik tombol untuk menghasilkan lembar keselamatan sederhana
        4. Simpan atau cetak hasil untuk referensi
        """)

if __name__ == "__main__":
    main()
