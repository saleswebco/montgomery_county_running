import pandas as pd

# Input and output file paths
input_file = "cases.xlsx"
output_file = "cases_updated.xlsx"

# Load the data
df = pd.read_excel(input_file)

# Ensure 'Last Filing Date' is datetime
df['Last Filing Date'] = pd.to_datetime(df['Last Filing Date'], errors='coerce').dt.date

# Drop rows where date couldn't be parsed
df = df.dropna(subset=['Last Filing Date'])

# Sort by Last Filing Date
df = df.sort_values(by='Last Filing Date')

# Create a writer object
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Write All Data sheet
    df.to_excel(writer, sheet_name="All Data", index=False)
    
    # Create month-wise sheets
    for (year, month), group in df.groupby([pd.to_datetime(df['Last Filing Date']).dt.year,
                                            pd.to_datetime(df['Last Filing Date']).dt.month]):
        sheet_name = f"{pd.to_datetime(f'{year}-{month:02d}-01').strftime('%b %Y')}"
        group.sort_values(by='Last Filing Date').to_excel(writer, sheet_name=sheet_name, index=False)
    
    # Create summary sheet
    summary = (
        df.groupby([pd.to_datetime(df['Last Filing Date']).dt.year.rename("Year"),
                    pd.to_datetime(df['Last Filing Date']).dt.month.rename("Month")])
          .size()
          .reset_index(name='Count')
    )

    # Convert Year + Month to "Mon YYYY"
    summary['Month_Name'] = summary.apply(
        lambda x: pd.to_datetime(f"{x['Year']}-{x['Month']:02d}-01").strftime('%b %Y'),
        axis=1
    )

    # Keep only Month_Name and Count
    summary = summary[['Month_Name', 'Count']]
    summary.to_excel(writer, sheet_name="Summary", index=False)

print(f"Updated file created: {output_file}")