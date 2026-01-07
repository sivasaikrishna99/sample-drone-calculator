import streamlit as st

# Page setup
st.set_page_config(page_title="Simple Drone Endurance Calculator")

st.title("Simple Drone Endurance Calculator")
st.write("Sample app to test shared link & inputs")

# Inputs
weight = st.number_input("Drone Weight (kg)", value=10.0)
battery_ah = st.number_input("Battery Capacity (Ah)", value=20.0)
current_a = st.number_input("Average Current Draw (A)", value=25.0)

# Calculation
if st.button("Calculate Endurance"):
    endurance_min = (battery_ah * 60) / current_a

    st.subheader("Result")
    st.write(f"**Estimated Endurance:** {endurance_min:.2f} minutes")