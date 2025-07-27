import streamlit as st
import os
import tempfile
import re
import pandas as pd
import google.generativeai as genai
from agent3_executor import run_agent3_and_save_output
from agent4_code import convert_multi_to_long
import io

# === Load Gemini API Key ===
with open("gemini_key.txt", "r") as f:
    GEMINI_API_KEY = f.read().strip()
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.0-flash")

# === Streamlit UI ===
st.set_page_config(page_title="Excel Format Transformer", layout="centered")
st.title(" Excel↔Format Transformer")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"], key="inputfile")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(uploaded_file.read())
        temp_path = tmp.name
    st.success("✅ Input file uploaded and saved.")

    try:
        df = pd.read_excel(temp_path, header=None)
    except Exception as e:
        st.error(f"❌ Failed to read Excel file: {e}")
        st.stop()

    preview = df.head(10).to_csv(index=False)

    # === Agent 1: Format Detection ===
    with open("agent1_detection_prompt.txt") as f:
        agent1_prompt = f.read()
    detection_prompt = agent1_prompt + f"\n\nHere is a sample of the data:\n\n{preview}"

    response1 = model.generate_content(detection_prompt)
    format_classification = response1.text.strip().upper()

    if format_classification not in {"PIVOTED", "UNPIVOTED", "MULTIHEADER"}:
        st.error(f"❌ Invalid format classification: `{format_classification}`")
        st.stop()

    st.info(f"🔍 Detected Format: `{format_classification}`")

    # === MULTIHEADER → Direct Agent 4 Code
    output_path = "output.xlsx"
    if format_classification == "MULTIHEADER":
        try:
            convert_multi_to_long(temp_path, output_path)
            st.success("✅ Transformation successful using MULTIHEADER logic!")
            with open(output_path, "rb") as f:
                buffer = io.BytesIO(f.read())
            st.download_button(
                label="📥 Download Output Excel",
                data=buffer,
                file_name="pivot_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"❌ Failed MULTIHEADER transformation: {e}")
        st.stop()

    # === For PIVOTED / UNPIVOTED: Use Agent 2 and 3
    with open("agent2_codegen_prompt.txt") as f:
        agent_prompt = f.read()
    generation_prompt = (
        agent_prompt
        + f"\n\nHere is your task:"
        + f"\nInput file path: {temp_path}"
        + f"\nDetected format: {format_classification}"
        + f"\nOutput file path: output.xlsx"
    )

    response2 = model.generate_content(generation_prompt)
    raw_code = response2.text.strip()
    raw_code = re.sub(r"^```(?:python)?", "", raw_code).strip()
    raw_code = re.sub(r"```$", "", raw_code).strip()
    raw_code = re.sub(r'path\s*=\s*["\'].*?["\']', f'path = "{temp_path}"', raw_code)

    raw_code = (
        f'path = "{temp_path}"\n'
        f'format_classification = "{format_classification}"\n\n'
        + raw_code
    )

    # === Agent 3: Execute and Output ===
    st.subheader("🚀 Output Preview")
    try:
        result = run_agent3_and_save_output(raw_code, output_path, temp_path, format_classification)
        if "ERROR" in result:
            st.error(result)
        else:
            st.success("✅ Transformation successful!")
            with open(output_path, "rb") as f:
                buffer = io.BytesIO(f.read())
            st.download_button(
                label="📥 Download Output Excel",
                data=buffer,
                file_name="pivot_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"❌ Execution Failed: {e}")
