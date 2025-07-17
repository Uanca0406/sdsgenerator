import streamlit as st
import requests

# Set page config
st.set_page_config(
    page_title="Hazard Symbol Checker",
    page_icon="⚠️",
    layout="wide"
)

# Hazard symbol mapping
hazard_map = {
    'H200': {'symbol': '💥', 'name': 'Explosive'},
    'H220': {'symbol': '🔥', 'name': 'Extremely flammable gas'},
    'H300': {'symbol': '☠️', 'name': 'Fatal if swallowed'},
    'H314': {'symbol': '⚠️', 'name': 'Causes severe skin burns and eye damage'},
    'H400': {'symbol': '🐟', 'name': 'Very toxic to aquatic life'},
    # Add more hazard codes and symbols as needed
}

# Handling instructions mapping
handling_instructions = {
    'H200': "Handle with care. Avoid impact and friction.",
    'H220': "Keep away from heat, sparks, open flames, and hot surfaces.",
    'H300': "If swallowed, seek medical attention immediately.",
    'H314': "Wear protective gloves and eye protection.",
    'H400': "Avoid release to the environment. Collect spillage.",
    # Add more handling instructions as needed
}

def main():
    st.title("Hazard Symbol Checker")
    st.markdown("Enter the hazard code to see the corresponding symbol and handling instructions.")

    # Input for hazard code
    hazard_code = st.text_input("Enter Hazard Code (e.g., H200, H220):", placeholder="H200")

    if hazard_code:
        hazard_info = hazard_map.get(hazard_code)
        if hazard_info:
            st.markdown(f"### Hazard Symbol: {hazard_info['symbol']} - {hazard_info['name']}")
            handling_instruction = handling_instructions.get(hazard_code, "No specific handling instructions available.")
            st.markdown(f"### Handling Instructions: {handling_instruction}")
        else:
            st.warning("Hazard code not found. Please enter a valid code.")

if __name__ == "__main__":
    main()
