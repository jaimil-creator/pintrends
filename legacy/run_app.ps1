# Startup script for PinTrends
$env:PYTHONPATH = "C:\Users\My-PC\Desktop\pintrends"
$env:PYTHONUNBUFFERED = "1"

# Start API in background
Start-Process -FilePath ".venv\Scripts\uvicorn" -ArgumentList "api.main:app --port 8000 --reload" -WindowStyle Normal

# Wait for API
Start-Sleep -Seconds 5

# Start Streamlit
.venv\Scripts\streamlit run ui/app.py
