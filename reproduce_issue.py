import requests
import json

url = "http://127.0.0.1:5000/calculate"

# Test 1: Manual difficulty variation
payload = {
    "difficulty_method": "manual",
    "manual_diff_var_1": "10.0",  # 10% monthly increase for year 1
    "manual_diff_var_2": "0.0",
    "manual_diff_var_3": "0.0",
    "manual_diff_var_4": "0.0",
    "manual_diff_var_5": "0.0",
    "manual_diff_var_6": "0.0",
    "manual_diff_var_7": "0.0",
    "manual_diff_var_8": "0.0",
    "energy_cost_per_mwh": "50",
    "power_source": "Direct Energy",
    "depreciation_years": "3"
}

# We need to make sure the server is running. 
# The user metadata shows: "Python App.py (in d:\dev\BP-8Blocks, running for 1m41s)"
# But it says "App.py" and the file is "app.py". Windows is case-insensitive usually.

try:
    response = requests.post(url, data=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        html = response.text
        # Look for the difficulty value in Year 1
        # In results_partial.html: <td class="text-center align-middle font-monospace">{{ "{:,.0f}".format(year_data.avg_difficulty) }}</td>
        print("Response received. Searching for average difficulty in Year 1...")
        # We can't easily parse HTML without bs4, but we can grep.
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Connection failed: {e}")
