# INGRO – Simplifying Groundwater Intelligence from INGRES

## Overview

INGRO is a data-driven groundwater intelligence system that simplifies access to official groundwater data provided by the **India Groundwater Resource Estimation System (INGRES)**.

The system bridges the gap between complex groundwater datasets and real-world decision-making by enabling users to interact using **natural language queries**. It retrieves, interprets, and presents groundwater information in a clear and actionable format.

INGRO integrates multiple datasets — recharge, extraction, rainfall, and aquifer characteristics — and converts raw numerical values into meaningful advisories using a **rule-based interpretation engine** aligned with CGWB standards.

---

## Problem Overview

Groundwater data in India is available but not easily usable. Existing platforms like INGRES have several limitations:

- Require structured API inputs instead of simple queries
- Use technical identifiers (UUIDs) instead of familiar location names
- Provide raw numerical outputs without explanation
- Depend on GIS-based interfaces difficult for non-experts
- Lack user-friendly interpretation for real-world decisions

**Practical questions users struggle to answer:**
- Is groundwater available in my area?
- Is it safe to drill a borewell?
- How has groundwater changed over time?

---

## Our Solution

INGRO builds an intelligent, layered system on top of INGRES that:

- Accepts natural language queries
- Maps user input to official administrative regions
- Retrieves relevant groundwater data from authoritative sources
- Interprets values using CGWB-based rules
- Presents results as explanations, charts, and reports

---

## How It Works (Pipeline)

| Step | Description |
|------|-------------|
| **Step 1** – User Query | User asks a question (text/voice) |
| **Step 2** – Query Processing | Extracts intent and location using NLP |
| **Step 3** – Location Mapping | Maps place name to district/taluka used in INGRES |
| **Step 4** – Data Retrieval | Fetches recharge, draft, rainfall, aquifer data |
| **Step 5** – Data Processing | Cleans and normalizes API responses |
| **Step 6** – Interpretation Engine | Applies CGWB rules to classify groundwater status |
| **Step 7** – Output Generation | Generates explanation, charts, and advisories |
| **Step 8** – Report Export | Creates downloadable structured reports |

---

## System Architecture

INGRO follows a modular architecture:

### 1. User Interaction Layer
- Natural language interface
- Multilingual query support
- Report viewing and download

### 2. Query Processing Layer
- Intent detection
- Location extraction
- Query classification

### 3. Data Retrieval Layer
- INGRES API integration
- Rainfall and aquifer datasets
- Data normalization

### 4. Interpretation Layer
- Rule-based advisory system
- CGWB classification logic
- Feasibility analysis

### 5. Visualization & Reporting Layer
- Charts and trend graphs
- Structured reports
- Downloadable outputs

---

## Core Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Natural Language Query System** | Ask questions in plain language — no technical knowledge required |
| 2 | **Common Query Support** | Handles groundwater availability, borewell feasibility, recharge status |
| 3 | **Document Interaction (PDF Querying)** | Upload groundwater PDFs and query them using OCR-based extraction |
| 4 | **Report Generation with Trends** | Rainfall, recharge, extraction graphs and status summaries |
| 5 | **Multilingual Support** | Supports multiple languages for rural and non-English users |
| 6 | **Borewell Depth Estimation** | Approximate depth ranges based on regional conditions |
| 7 | **Data Security (AES Encryption)** | Encrypts stored and processed sensitive data |
| 8 | **Rule-Based Advisory Engine** | Classifies status as Safe, Semi-Critical, or Over-Exploited |

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React.js |
| Backend | Python, FastAPI |
| NLP | Python NLP libraries |
| Data Sources | INGRES, CGWB, India-WRIS, IMD |
| OCR | Tesseract / OCR libraries |
| Visualization | Charting libraries |
| Security | AES Encryption |

---

## Key Innovations / USP

- Converts complex groundwater data into simple insights
- Uses **rule-based interpretation** instead of black-box models
- Integrates multiple official datasets into one system
- Supports **natural language queries** instead of raw APIs
- Provides real-time visualization and downloadable reports
- Includes **document-based interaction** with OCR
- Designed specifically for **non-technical users**

---

## What Makes This Different

- Focuses on **interpretability** over prediction
- Uses **official datasets only** (no synthetic assumptions)
- Bridges technical data → real-world usability
- Works as a **decision-support system**, not just a data viewer
- Designed specifically for **Indian groundwater systems**

---

## Applications

| User | Use Case |
|------|----------|
| 🌾 Farmers | Borewell feasibility and water planning |
| 🔬 Researchers | Trend analysis and comparisons |
| 🏛️ Government Officials | Quick access to reports |
| 👤 General Users | Awareness and understanding |

---

## Limitations

- Depends on availability of official datasets
- No real-time groundwater monitoring
- Borewell depth is indicative, not exact

---

## Future Work

- [ ] Aquifer-based feasibility modeling
- [ ] Integration of real-time sensor data
- [ ] Groundwater quality indicators (fluoride, salinity)
- [ ] Population and demand-based forecasting
- [ ] Improved OCR accuracy
- [ ] CRON-based secure data synchronization

---

## Potential Impact

INGRO improves accessibility of groundwater data and supports better decision-making. It can contribute to **sustainable water usage**, especially in regions where groundwater is the primary resource.

---

## Team

- Anisha Shankar
- Tejas Gadge
- Ganesh Shelar

---

## Acknowledgment

We would like to thank **Rohini Ma'am**, **Dr. Parveen Kaur**, and **CGWB** for their guidance and support throughout this project.
