import streamlit as st
import cv2
import numpy as np
from PIL import Image
import time
import requests

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="AgroAid Smart Crop Care",
    page_icon="🌿",
    layout="wide"
)

# -----------------------------
# SESSION STATE
# -----------------------------
if "weather_loaded" not in st.session_state:
    st.session_state.weather_loaded = False
    st.session_state.temp = None
    st.session_state.humidity = None
    st.session_state.condition = None

# -----------------------------
# WEATHER API
# -----------------------------
API_KEY = "6bab5bbd95b552cb813e4491df4b71f8"
CITY = "Kochi"

def get_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    if "main" not in data:
        st.error("Weather API not ready yet. Try again later.")
        return None, None, None

    temp = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    condition = data["weather"][0]["main"]

    return temp, humidity, condition

# -----------------------------
# HEADER
# -----------------------------
st.markdown("# 🌿 Intelligent Pesticide Decision System")
st.write("Detect Early. Decide Smart. Spray Right.")

col1, col2 = st.columns([1.2,1])

# -----------------------------
# WEATHER PANEL
# -----------------------------
with col2:
    st.subheader("🌦 Weather Conditions")

    if st.button("Fetch Live Weather"):
        temp, humidity, condition = get_weather()

        if temp is not None:
            st.session_state.weather_loaded = True
            st.session_state.temp = temp
            st.session_state.humidity = humidity
            st.session_state.condition = condition

    if st.session_state.weather_loaded:
        st.success(f"{st.session_state.condition}")
        st.write(f"🌡 Temperature: {st.session_state.temp} °C")
        st.write(f"💧 Humidity: {st.session_state.humidity} %")

# -----------------------------
# IMAGE INPUT
# -----------------------------
with col1:
    st.subheader("📷 Plant Image")
    uploaded_file = st.file_uploader("Drag & Drop Leaf Image", type=["jpg","png","jpeg"])

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True)

# -----------------------------
# SEVERITY CALCULATION
# -----------------------------
def calculate_severity(image):
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_green = np.array([25,40,40])
    upper_green = np.array([90,255,255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)

    lower_inf = np.array([10,100,20])
    upper_inf = np.array([30,255,200])
    inf_mask = cv2.inRange(hsv, lower_inf, upper_inf)

    infected_pixels = np.sum(inf_mask > 0)
    total_pixels = np.sum((green_mask > 0) | (inf_mask > 0))

    if total_pixels == 0:
        return 0, img, inf_mask

    severity = round((infected_pixels / total_pixels) * 100,2)
    return severity, img, inf_mask

# -----------------------------
# INFECTION LABEL
# -----------------------------
def infection_label(severity):
    if severity < 10:
        return "Low"
    elif severity < 30:
        return "Mild"
    elif severity < 60:
        return "Moderate"
    else:
        return "Severe"

# -----------------------------
# DECISION ENGINE
# -----------------------------
def decision(severity, humidity, temp, condition):

    if condition in ["Rain","Thunderstorm","Drizzle"]:
        return "Delay Spray", "Rain will wash pesticide"

    if severity < 10:
        return "No Spray", "Low infection"

    elif severity < 30 and humidity > 75:
        return "Preventive Spray", "High humidity spreads fungus"

    elif severity < 60:
        return "Targeted Spray", "Moderate infection"

    else:
        return "Heavy Spray", "Severe infection"

# -----------------------------
# SPRAY DURATION
# -----------------------------
def spray_duration(severity):
    if severity < 10:
        return 0
    elif severity < 30:
        return 3
    elif severity < 60:
        return 6
    else:
        return 10

# -----------------------------
# ANALYZE BUTTON
# -----------------------------
if uploaded_file and st.button("🔍 Analyze Plant"):

    if not st.session_state.weather_loaded:
        st.error("Please fetch live weather first!")
    else:
        severity, original_img, inf_mask = calculate_severity(image)
        label = infection_label(severity)

        action, reason = decision(
            severity,
            st.session_state.humidity,
            st.session_state.temp,
            st.session_state.condition
        )

        duration = spray_duration(severity)

        # 🌿 HEALTH METER
        health = 100 - severity
        st.subheader("🌿 Plant Health")
        st.progress(int(health))

        if health > 80:
            st.success(f"Healthy ({health}%)")
        elif health > 50:
            st.warning(f"Moderate Condition ({health}%)")
        else:
            st.error(f"Poor Condition ({health}%)")

        st.write(f"**Infection Level:** {label} ({severity}%)")

        # 🧠 DECISION
        st.markdown("## 🧠 System Decision")

        color = "#2ecc71"
        if action == "Preventive Spray":
            color = "#f39c12"
        elif action == "Heavy Spray":
            color = "#e74c3c"
        elif action == "Delay Spray":
            color = "#3498db"

        st.markdown(f"""
        <div style="padding:20px;border-radius:12px;background-color:{color};color:white">
        <h3>{action}</h3>
        <p>{reason}</p>
        </div>
        """, unsafe_allow_html=True)

        # 🔬 INFECTED AREA
        colored = original_img.copy()
        colored[inf_mask > 0] = [0,0,255]
        colored = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)

        st.subheader("🔬 Detected Infection Area")
        st.image(colored, use_column_width=True)

        # ⏱ SPRAY SIMULATION
        if duration == 0 or action == "Delay Spray":
            st.success("No spraying performed ✅")
        else:
            st.warning(f"Applying pesticide for {duration} seconds")

            counter = st.empty()
            progress = st.progress(0)

            for i in range(1, duration+1):
                counter.write(f"Spraying... {i} sec")
                progress.progress(i/duration)
                time.sleep(1)

            st.success("Spraying Completed ✅")
