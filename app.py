import streamlit as st
import pandas as pd
import joblib

@st.cache_resource
def load_model():
    model = joblib.load("models/failure_model.pkl")
    columns = joblib.load("models/feature_columns.pkl")
    return model, columns

model, feature_columns = load_model()

st.title("🔧 Predictive Maintenance – Machine Failure Prediction")
st.write("Enter the sensor readings below to check if a machine is at risk of failure.")

with st.form("input_form"):

    col1, col2 = st.columns(2)

    with col1:
        air_temp = st.number_input("Air Temperature (K)", min_value=250.0, max_value=500.0, value=300.0)
        process_temp = st.number_input("Process Temperature (K)", min_value=250.0, max_value=500.0, value=310.0)
        rotational_speed = st.number_input("Rotational Speed (rpm)", min_value=500.0, max_value=3000.0, value=1500.0)

    with col2:
        torque = st.number_input("Torque (Nm)", min_value=0.0, max_value=500.0, value=40.0)
        tool_wear = st.number_input("Tool Wear (min)", min_value=0.0, max_value=300.0, value=10.0)
        mtype = st.selectbox("Machine Type", ["L", "M", "H"])

    submitted = st.form_submit_button("Predict")

if submitted:
    input_data = pd.DataFrame([[
        air_temp,
        process_temp,
        rotational_speed,
        torque,
        tool_wear,
        mtype
    ]], columns=feature_columns)  # Prepare input df

    pred = model.predict(input_data)[0]     # Prediction
    proba = model.predict_proba(input_data)[0][1]  # Probability of failure

    st.subheader("Prediction Result")     # Output
    
    if pred == 1:
        st.error(f"⚠️ Machine is at HIGH RISK of failure\nProbability: **{proba:.2f}**")
    else:
        st.success(f"✅ Machine failure\nProbability: **{proba:.2f}**")


    st.write("Prediction Confidence")     #probability bar chart
    st.progress(int(proba * 100))
