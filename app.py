import streamlit as st
import numpy as np
from scipy.interpolate import PchipInterpolator

st.set_page_config(page_title="Drone Endurance Calculator", layout="centered")
st.title("Drone Endurance Calculator 🚁")

# --- Drone Type Dropdown ---
drone_type = st.selectbox(
    "Select Drone Type",
    ["Agri Drone (Variable Payload)", "Surveillance Drone (Fixed Payload)"]
)

# --- Basic Inputs ---
st.header("Basic Inputs")
dry_kg = st.number_input("Dry weight (kg)", value=15.8, min_value=1.0, step=0.1)
motors = st.number_input("Number of motors", value=6, min_value=1, step=1)
battery_Ah = st.number_input("Battery Capacity (Ah)", value=24.0, min_value=1.0, step=0.1)
electronics_consumption = st.number_input("Electronics Consumption (A)", value=4.274, min_value=0.0, step=0.01)

# --- Advanced Inputs Expander ---
with st.expander("Advanced Inputs (Optional)"):
    takeoff_time = st.number_input("Takeoff time (min)", value=0.25, min_value=0.0, step=0.01)
    landing_time = st.number_input("Landing time (min)", value=0.25, min_value=0.0, step=0.01)
    flow_rate = st.number_input("Dispense flow rate (L/min)", value=3.333, min_value=0.1, step=0.01)
    tw_ratio_takeoff = st.number_input("Takeoff T/W ratio", value=1.1, step=0.01)
    tw_ratio_hover_dispense = st.number_input("Hover T/W ratio", value=1.05, step=0.01)
    tw_ratio_landing = st.number_input("Landing T/W ratio", value=0.8, step=0.01)

# --- Payload Input ---
if drone_type == "Agri Drone (Variable Payload)":
    water_kg_full = st.number_input("Payload (water) kg", value=8.5, min_value=0.0, step=0.1)
else:
    water_kg_full = 0.0  # Surveillance drone

# --- Motor Thrust vs Current ---
thrust_g = np.array([1499, 2001, 2498, 2997, 3500, 4001, 4998, 5500, 6003,
                     6500, 7005, 7504, 7999, 8999, 9505, 10000, 10503, 10994,
                     11494, 11852])
current_A = np.array([2.4, 3.6, 4.9, 6.3, 8.0, 9.7, 13.5, 15.6, 17.6,
                      19.9, 22.1, 24.9, 27.4, 32.9, 36.1, 38.6, 42.6, 45.5,
                      48.8, 51.8])
current_interp = PchipInterpolator(thrust_g, current_A, extrapolate=True)

# --- Helper function ---
def calculate_phase_ah(weight_kg, tw_ratio, duration_min):
    thrust_per_motor = (weight_kg * 1000 * tw_ratio) / motors
    I_motor = current_interp(thrust_per_motor)
    I_total = (I_motor * motors) + electronics_consumption
    return I_total * duration_min / 60  # Ah

# --- Calculate button ---
if st.button("Calculate"):
    # --- Takeoff ---
    total_kg_start = dry_kg + water_kg_full
    Ah_takeoff = calculate_phase_ah(total_kg_start, tw_ratio_takeoff, takeoff_time)

    # --- Dispense phase ---
    Ah_dispense = 0
    dispense_duration_min = water_kg_full / flow_rate if water_kg_full > 0 else 0
    dispense_duration_sec = round(dispense_duration_min * 60)
    dt = 0.1  # seconds
    for t in np.arange(0, dispense_duration_sec, dt):
        water_left = max(water_kg_full - (flow_rate / 60) * t, 0)
        total_weight = dry_kg + water_left
        thrust_per_motor = (total_weight * 1000 * tw_ratio_hover_dispense) / motors
        I_motor = current_interp(thrust_per_motor)
        I_total = (I_motor * motors) + electronics_consumption
        Ah_dispense += (I_total * dt) / 3600  # convert sec to Ah

    # --- Landing ---
    Ah_landing = calculate_phase_ah(dry_kg, tw_ratio_landing, landing_time)

    # --- Hover after dispense until battery ends ---
    Ah_hover = battery_Ah - Ah_takeoff - Ah_dispense - Ah_landing
    thrust_per_motor_hover = (dry_kg * 1000 * tw_ratio_hover_dispense) / motors
    I_hover = current_interp(thrust_per_motor_hover)
    I_total_hover = (I_hover * motors) + electronics_consumption
    hovering_time = Ah_hover * 60 / I_total_hover if Ah_hover > 0 else 0

    # --- Total cycle and endurance ---
    Ah_per_cycle = Ah_takeoff + Ah_dispense + Ah_landing
    max_cycles = int(battery_Ah // Ah_per_cycle) if Ah_per_cycle > 0 else 0
    total_endurance = max_cycles * (takeoff_time + dispense_duration_min + landing_time)

    # --- Display main output ---
    st.header("Main Output")
    st.metric("Takeoff → Hover until RTL", f"{hovering_time:.2f} minutes")

    # --- Advanced output ---
    with st.expander("Advanced Output"):
        st.write(f"Takeoff Ah: {Ah_takeoff:.2f} Ah")
        st.write(f"Dispense Ah: {Ah_dispense:.2f} Ah")
        st.write(f"Landing Ah: {Ah_landing:.2f} Ah")
        st.write(f"Max mission cycles: {max_cycles}")
        st.write(f"Total endurance: {total_endurance:.2f} min")
