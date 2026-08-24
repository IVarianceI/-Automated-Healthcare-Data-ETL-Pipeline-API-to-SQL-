📌 Project Overview
This project is an End-to-End ETL (Extract, Transform, Load) Pipeline designed to automate the extraction of Electronic Health Record (EHR) data, apply complex business logic, and generate highly customized, auditor-ready Excel reports.

Originally developed to streamline the Quarterly Quality Review (QRR) process, this script replaces hours of manual data export, cleaning, and Excel formatting with a single, highly resilient automated workflow.

💼 Business Value
Time Savings: Reduces a multi-hour manual data processing workflow down to seconds.

Audit & Compliance Readiness: Automatically calculates dynamic sample sizes (e.g., top 10% or minimum 5 records) and visually highlights them for quality assurance reviewers.

Error Reduction: Eliminates human error in data formatting and sheet naming by standardizing the extraction and transformation process.

Data Security: Implements .env variable management to ensure zero hardcoding of sensitive API tokens or internal credentials.

🛠️ Technology Stack
Python 3.x (Core scripting)

Pandas (In-memory data manipulation, cleaning, and aggregation)

XlsxWriter (Advanced Excel generation, conditional formatting, dynamic multi-sheet routing)

Requests & XML ElementTree (SOAP API integration and nested XML parsing)

Regex (re) & Math (Data sanitization and dynamic sample size calculations)

⚙️ Architecture & Workflow
1. Extract: SOAP API Integration & XML Parsing
Connects to a legacy/enterprise EHR system using a SOAP API.

Constructs a dynamic XML payload and securely authenticates using environment variables.

Parses nested XML responses directly into memory without writing intermediate files, converting the payload directly into a Pandas DataFrame.

2. Transform: Data Cleaning & Business Logic
Converts string-based XML data into numeric formats for downstream calculations.

Filters out invalid records (e.g., test patients, zero-billable records).

Applies custom business mapping functions to categorize programs and normalize patient episode statuses.

3. Load / Reporting: Dynamic Excel Generation
Dynamic Routing: Splits the master dataset into multiple Excel worksheets based on cross-sections of Program Group and Episode Status.

Edge Case Handling: Automatically sanitizes Excel tab names (stripping illegal characters []:*?/\), enforces the 31-character limit, and resolves duplicate sheet names dynamically.

Automated QA Highlighting: Calculates a dynamic sample size (10% of total rows, or a minimum of 5) and uses XlsxWriter to apply conditional formatting (yellow highlight) to the top X rows for compliance auditing.
