import os
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import numpy as np
import re
import math
from dotenv import load_dotenv

# ==========================================
# 1. Initialization & API Configuration
# ==========================================
print("🔧 Initializing End-to-End EHR Data Pipeline...")
load_dotenv(override=True)

# Fetch sensitive credentials from environment variables (.env)
ENCRYPTED_CONN = os.getenv("EXPORT_API_TOKEN")
# MOCKED FOR PUBLIC REPO: Use actual Report ID in production
EXPORT_ID = os.getenv("REPORT_EXPORT_ID", "9999") 

if not ENCRYPTED_CONN:
    raise ValueError("❌ Missing API_TOKEN in environment variables. Please set it in your .env file.")

URL = "https://reportservices.crediblebh.com/reports/ExportService.asmx"

# Dates are handled dynamically in SQL. We only need the random seed.
dynamic_seed = "2500"

print("📅 Data extraction period: Automatically calculated by SQL (Previous Quarter)")
print(f"🔢 Random seed parameter initialized: {dynamic_seed}")

# ==========================================
# 2. SOAP Payload Construction
# ==========================================
xml_payload = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ExportDataSet xmlns="https://www.crediblebh.com/">
      <connection>{ENCRYPTED_CONN}</connection>
      <export_id>{EXPORT_ID}</export_id>
      <param3>{dynamic_seed}</param3>
    </ExportDataSet>
  </soap:Body>
</soap:Envelope>"""

HEADERS = {
    "Content-Type": "text/xml; charset=utf-8",
    "SOAPAction": '"https://www.crediblebh.com/ExportDataSet"' 
}

# ==========================================
# 3. API Execution & Data Parsing
# ==========================================
print("🎯 Fetching data from EHR SOAP API...")

try:
    response = requests.post(URL, data=xml_payload, headers=HEADERS, timeout=60)
    
    if response.status_code == 200 and "<ErrorDataSet>" not in response.text:
        # Parse XML directly into memory
        root = ET.fromstring(response.text)
        data_rows = []
        
        for elem in root.iter():
            tag_name = elem.tag.split('}')[-1] 
            if tag_name == 'Table' and not any('complexType' in child.tag for child in elem):
                row_dict = {child.tag.split('}')[-1]: child.text for child in elem}
                if row_dict:
                    data_rows.append(row_dict)
        
        if data_rows:
            # Create the initial DataFrame directly from the API response
            df_exported = pd.DataFrame(data_rows)
            print(f"✅ API extraction successful. {len(df_exported)} records loaded into memory.")
            
            # ==========================================
            # 4. Data Cleaning & Type Conversion
            # ==========================================
            print("⚙️ Processing data and applying business logic...")
            
            # Convert XML string values to numeric for math and sorting
            df_exported['billable_count'] = pd.to_numeric(df_exported['billable_count'], errors='coerce').fillna(0)
            df_exported['random'] = pd.to_numeric(df_exported['random'], errors='coerce')
            
            # Exclude test patients and 0 billable counts
            df_exported = df_exported[df_exported['billable_count'] != 0]
            df_exported = df_exported[df_exported['last_name'] != 'Test']
            df_exported['episode_status'] = df_exported['episode_status'].astype(str).str.title()

            # ==========================================
            # 5. Business Logic Functions
            # ==========================================
            def group_programs(prog_name):
                prog_name = str(prog_name)
                # MOCKED FOR PUBLIC REPO: Generalized business categories
                if prog_name.startswith('PROG_A'):
                    return 'Category_A_Group'
                elif 'North' in prog_name:
                    return 'North_Region_Group'
                return prog_name

            def map_status(status):
                s_lower = str(status).strip().lower()
                if s_lower in ['active', 'pending']:
                    return 'Active'
                elif s_lower in ['pending disch', 'inactive', 'closed']:
                    return 'Inactive'
                return 'Inactive'

            # Apply grouping and mapping logic
            df_exported['program_group'] = df_exported['program'].apply(group_programs)
            df_exported['mapped_status'] = df_exported['episode_status'].apply(map_status)

            # ==========================================
            # 6. Excel Generation & Dynamic Formatting
            # ==========================================
            # Use a relative path so the script runs on any machine
            output_dir = os.path.join(os.getcwd(), 'output')
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, 'QRR_Analysis_Results.xlsx')
            
            print(f"📝 Generating Excel report with dynamic sampling...")
            
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                workbook = writer.book
                groups = df_exported['program_group'].unique()
                statuses = df_exported['mapped_status'].unique()
                used_tabs = set()
                
                # Highlight format: Yellow background
                highlight_format = workbook.add_format({'bg_color': '#FFFF00'})

                for group in groups:
                    for status in statuses:
                        subset = df_exported[(df_exported['program_group'] == group) & (df_exported['mapped_status'] == status)].copy()
                        
                        if not subset.empty:
                            # A. Calculate sample size X
                            row_count = len(subset)
                            if row_count < 50:
                                sample_size = min(5, row_count)
                            else:
                                sample_size = math.ceil(row_count / 10)
                            
                            # B. Sort by 'random'
                            subset = subset.sort_values(by='random', ascending=True).reset_index(drop=True)
                            
                            # C. Drop helper columns to keep the export clean
                            cols_to_drop = ['program_group', 'mapped_status']
                            subset = subset.drop(columns=[c for c in cols_to_drop if c in subset.columns])
                            
                            # D. Naming process (handle invalid characters and max length 31)
                            base_name = re.sub(r'[\[\]:*?/\\/]', '_', f"{group}_{status}")
                            tab_name = base_name[:31]
                            
                            counter = 1
                            while tab_name.lower() in used_tabs:
                                suffix = f"_{counter}"
                                tab_name = f"{base_name[:31-len(suffix)]}{suffix}"
                                counter += 1
                            used_tabs.add(tab_name.lower())
                            
                            # E. Write subset to Excel (exclude index)
                            subset.to_excel(writer, sheet_name=tab_name, index=False)
                            
                            # F. Apply conditional formatting (highlight top X rows)
                            worksheet = writer.sheets[tab_name]
                            worksheet.conditional_format(1, 0, sample_size, subset.shape[1]-1, 
                                                        {'type': 'no_blanks', 
                                                         'format': highlight_format})
                            
                            print(f"  -> Sheet '{tab_name}': {row_count} rows in total, highlighted top {sample_size}.")

            print(f"\n🚀 Pipeline complete! Final report successfully saved to: {output_file}")
            
        else:
            print("⚠️ API request succeeded, but no records were found (business vacuum).")
    else:
        print(f"❌ API Request failed. Status code: {response.status_code}")
        if "<ErrorDataSet>" in response.text:
             print("Server returned an internal error dataset. Please check the SQL tool.")

except Exception as e:
    print(f"🚨 Pipeline crashed with an unexpected error: {e}")
