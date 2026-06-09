📌 Project Overview
An industrial-grade, highly resilient ETL (Extract, Transform, Load) pipeline designed to securely transfer and synchronize large-scale clinical data (e.g., patient demographics, bed board intervals) into external EHR systems via SOAP/REST APIs.

This pipeline was built to bypass common API gateway limitations (such as payload size caps and network timeouts) and ensures 100% data integrity during transmission.

🛠️ Tech Stack & Key Features
Python (Pandas): In-memory data transformation and vectorization, effectively processing thousands of records without disk I/O bottlenecks.

Security First (Credential Decoupling): Implemented python-dotenv to strictly isolate API keys and endpoint URLs from the source code.

Batching & Chunking Mechanism: Dynamically slices massive datasets into manageable payloads (e.g., 500 rows/batch) to prevent HTTP 413 Payload Too Large errors and memory leaks.

Exponential Backoff with Jitter: Engineered a highly resilient retry mechanism using customized algorithms. When network throttling or server-side HTTP 503 occurs, the pipeline automatically pauses and retries with exponentially increasing delays, eliminating data loss during network storms.

Robust Error Handling: Deep XML/SOAP response parsing to intercept "Fake 200 OK" errors specific to legacy healthcare systems.
