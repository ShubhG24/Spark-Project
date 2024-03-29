import pandas as pd

# Read the Excel file
df = pd.read_csv('mortality_age.csv')

# Extract distinct country codes
distinct_country_codes = df['Country Code'].unique()

# Print the distinct country codes
for code in distinct_country_codes:
    print(f"<option value=\"{code}\">{code}</option>")