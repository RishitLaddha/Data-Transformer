#!/bin/bash

echo "📦 Installing required Python packages..."
pip install --upgrade pip

pip install \
  pandas \
  openpyxl \
  streamlit \
  python-dotenv \
  google-generativeai

echo "✅ All dependencies installed."
