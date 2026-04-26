from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from ClassA.Class_Classify import QueryClassifier  # Ensure this path is correct
from ClassA.Intent_Classify import IntentClassify
from ClassA.JsonSearch import JsonSearchClass
from ClassA.IngresTalukaDataApi import IngresTalukaDataApi
from ClassA.SummaryResponse import SummaryResponseAgent
from ClassA.ApiShortenScript import ApiShortenScript
import json
import os
import requests
import time
import tempfile
import google.generativeai as genai
import uuid
from dotenv import load_dotenv
import psycopg2
import base64
import threading
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import cloudinary
import cloudinary.uploader
import psycopg2
from psycopg2.extras import RealDictCursor
from os import urandom
import threading
import geopandas as gpd
from shapely.geometry import Point
import rasterio
import numpy as np
from pyproj import Transformer
from datetime import datetime
import math
load_dotenv()
GENAI_API_KEY = os.getenv("GEMINI_API_KEY") 

AES_KEY = base64.b64decode(os.getenv("AES_SECRET_KEY"))

if len(AES_KEY) not in (16, 24, 32):
    raise ValueError("Invalid AES key length")

genai.configure(api_key=GENAI_API_KEY)
REPORTS_DIR = "saved_reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

GEMINI_REQUEST_LIMIT = 3      # allow 3 Gemini calls
GEMINI_WAIT_SECONDS = 60      # then wait 1 minute

gemini_request_count = 0
gemini_last_reset = time.time()
gemini_lock = threading.Lock()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

DATABASE_URL = os.getenv("DATABASE_URL")

db_conn = psycopg2.connect(DATABASE_URL)
db_cursor = db_conn.cursor()

LITHOLOGY_TIF_PATH = "Spatial_data/india_geology_2m.tif"
TALUKA_GEOJSON_PATH = "Spatial_data/India_geojson/india_taluk.geojson"
DISTRICT_GEOJSON_PATH = "Spatial_data/India_geojson/india_district.geojson"

taluka_gdf = gpd.read_file(TALUKA_GEOJSON_PATH).to_crs("EPSG:4326")
district_gdf = gpd.read_file(DISTRICT_GEOJSON_PATH).to_crs("EPSG:4326")

ESA_WORLDCOVER_BASE_URL = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com"
)

ESA_WORLDCOVER_VERSION = "v100"   # use v100 for now
ESA_WORLDCOVER_YEAR = "2021"
ESA_WORLDCOVER_LAYER = "map"

LITHOLOGY_COG = "Spatial_data/india_geology_2m.tif"
LANDCOVER_CLASSES = { 10: "Tree cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland", 50: "Built-up", 60: "Bare / sparse vegetation", 70: "Snow and ice", 80: "Permanent water bodies", 90: "Herbaceous wetland", 95: "Mangroves", 100: "Moss and lichen" }
LITHOLOGY_CLASSES = {
    0: "Unknown / Mixed",
    1: "Alluvium",
    2: "Sandstone / Sedimentary (Gondwana / Vindhyan)",
    3: "Limestone",
    4: "Granite / Gneiss (Archaean hard rock)",
    5: "Basalt (Deccan Trap)"
}


app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

classifier = QueryClassifier()  # Initialize classifier
intent_classifier = IntentClassify()
json_search = JsonSearchClass()
ingres_taluka_api = IngresTalukaDataApi()
summary_response_agent = SummaryResponseAgent()
api_response_script = ApiShortenScript()

@app.route("/process_query", methods=["POST"])
def process_query():
    try:
        data = request.get_json()  # Get JSON data from request
        user_query = data.get("query")

        if not user_query:
            return jsonify({"error": "Missing 'query' field"}), 400

        # Pass query to QueryClassifier class
        classified_class = classifier.classify(user_query)
        
        if classified_class == "ClassA":  # Fixed: Use == for comparison
            intent = intent_classifier.intent_classify(user_query)
            
            json_path = "./India_Ingris_Data_Complete.json"
            with open(json_path, "r", encoding="utf-8") as f:
                locations = json.load(f)
                
            loc_chars = json_search.search_by_location_name(locations, intent, score_cutoff=70)
            
            api_response = ingres_taluka_api.fetch_business_data(loc_chars)
            # result = ingres_taluka_api.fetch_business_data(loc_chars)
            short_api_response = api_response_script.convert_json(api_response)
            # result = api_response_script.convert_json(api_response)
            
            result = summary_response_agent.summary_response(user_query,short_api_response)
            
            
        else:
            result = f"Query classified as {classified_class} - No location extraction needed."  # Handle other classes

        return jsonify({"result": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_visual_report(file_url):
    # --- Step 1: Download the File ---
    print(f"Downloading from: {file_url}")
    response = requests.get(file_url)
    if response.status_code != 200:
        raise Exception("Failed to download file from Cloudinary")

    # FIX 1: Detect extension (PDF vs TXT) so Gemini knows how to read it
    file_extension = ".pdf" if ".pdf" in file_url.lower() else ".txt"

    # FIX 2: Use mode='wb' (Write Binary) to handle PDFs/Images correctly
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix=file_extension) as temp_input:
        # FIX 3: Use response.content (Bytes), NOT response.text
        temp_input.write(response.content)
        temp_input_path = temp_input.name

    try:
        # --- Step 2: Upload to Gemini ---
        print("Uploading to Gemini...")
        
        # The mime_type is automatically inferred from the file extension we set above
        uploaded_file = genai.upload_file(path=temp_input_path, display_name="User File")
        
        # Wait for processing (CRITICAL for PDFs)
        while uploaded_file.state.name == "PROCESSING":
            import time
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)
        
        if uploaded_file.state.name == "FAILED":
            raise Exception("Gemini failed to process the file.")

        # --- Step 3: The Prompt ---
        prompt = """
        You are an expert Data Analyst and Frontend Developer.
        
        **Task:** Analyze the attached document deeply. Extract key insights, trends, and statistics.
        
        **Output Requirement:**
        Generate a SINGLE, self-contained HTML file that summarizes this data.
        
        **Design & Layout Specs (CRITICAL):**
        1.  **Responsive Grid:** Use a responsive grid layout. On mobile, stack elements (1 column). On desktop, show charts side-by-side (2 columns) using Tailwind classes like `grid grid-cols-1 md:grid-cols-2 gap-6`.
        2.  **Compact Charts:** The graphs MUST NOT be too tall. 
            * **Wrap every `<canvas>` inside a parent `<div>` with a fixed relative height**, specifically `class="relative h-64 w-full"` or `h-80`. 
            * **Do NOT allow charts to expand indefinitely.**
        3.  **Styling:** Use Tailwind CSS (via CDN) for a clean, modern, dark-mode dashboard.
        
        **Visualizations (Chart.js):**
        1.  Include at least 3 distinct interactive charts (Bar, Pie, Line).
        2.  **Configuration Rule:** inside the `new Chart()` config, you MUST set:
            `options: { responsive: true, maintainAspectRatio: false, ... }`
            This is required so the chart respects the container height defined in the CSS.
        3.  Extract data from the document and hardcode it into the JavaScript arrays.
        
        **Content:**
        * **Executive Summary:** A concise text section at the top.
        * **Key Action Items:** A bulleted list of takeaways.
        
        **Constraint:** Return ONLY the raw HTML code. Do not use markdown blocks. Start with <!DOCTYPE html>.
        """
        gemini_rate_limit_guard() 
        # --- Step 4: Generate ---
        print("Generating report...")
        # Note: Ensure you are using a valid model name (e.g., gemini-1.5-flash or gemini-1.5-pro)
        model = genai.GenerativeModel("gemini-2.5-flash") 
        result = model.generate_content([uploaded_file, prompt])
        
        return result.text

    finally:
        # Cleanup
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)

@app.route('/get_summary', methods=['POST'])
def get_summary():
    try:
        data = request.get_json()
        file_url = data.get("file_url")

        if not file_url:
            return jsonify({"error": "Missing 'file_url'"}), 400

        # Generate report HTML
        html_content = generate_visual_report(file_url)
        html_content = html_content.replace("```html", "").replace("```", "").strip()

        # Save locally
        session_id = str(uuid.uuid4())
        filename = f"report_{session_id}.html"
        save_path = os.path.join(REPORTS_DIR, filename)

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Upload to Cloudinary
        cloudinary_url = upload_html_to_cloudinary(save_path)
        print(cloudinary_url)
        # Insert DB entry
        insert_uploaded_file(
            session_id=session_id,
            input_file_url=file_url,
            report_url=cloudinary_url
        )
        
        

        # Return file to user (same behavior)
        return jsonify({
            "message": "Report generated successfully",
            "report_url": cloudinary_url
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
def encrypt_aes(plain_text: str) -> str:
    iv = urandom(16)
    cipher = Cipher(
        algorithms.AES(AES_KEY),
        modes.CBC(iv)
    )
    encryptor = cipher.encryptor()

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plain_text.encode()) + padder.finalize()

    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(iv + encrypted).decode()


def decrypt_aes(encrypted_text: str) -> str:
    data = base64.b64decode(encrypted_text.encode())
    iv = data[:16]
    encrypted_data = data[16:]

    cipher = Cipher(
        algorithms.AES(AES_KEY),
        modes.CBC(iv)
    )
    decryptor = cipher.decryptor()

    decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()

    return decrypted.decode()

def upload_html_to_cloudinary(file_path):
    result = cloudinary.uploader.upload(
        file_path,
        resource_type="raw",
        folder="generated_reports"
    )
    return result["secure_url"]

def insert_uploaded_file(session_id, input_file_url, report_url):
    encrypted_input = encrypt_aes(input_file_url)
    encrypted_report = encrypt_aes(report_url)

    query = """
        INSERT INTO uploaded_files (id, session_id, input_file, generated_summary)
        VALUES (%s, %s, %s, %s)
    """

    db_cursor.execute(
        query,
        (
            str(uuid.uuid4()),      # id
            session_id,             # session_id
            encrypted_input,        # encrypted input file
            encrypted_report        # encrypted summary
        )
    )
    db_conn.commit()

import json
import re

def gemini_rate_limit_guard():
    global gemini_request_count, gemini_last_reset

    with gemini_lock:
        now = time.time()

        # Reset counter every minute
        if now - gemini_last_reset >= GEMINI_WAIT_SECONDS:
            gemini_request_count = 0
            gemini_last_reset = now

        gemini_request_count += 1
        print(f"[RATE LIMIT] Gemini request #{gemini_request_count}")

        if gemini_request_count > GEMINI_REQUEST_LIMIT:
            sleep_time = GEMINI_WAIT_SECONDS - (now - gemini_last_reset)
            sleep_time = max(sleep_time, 0)

            print(f"[RATE LIMIT] Limit reached. Sleeping for {int(sleep_time)} seconds...")
            time.sleep(sleep_time)

            # Reset after sleep
            gemini_request_count = 1
            gemini_last_reset = time.time()


def extract_query_metadata(user_query: str) -> dict:
    print("[STEP] Extracting query metadata")

    prompt = f"""
    Extract structured information from the user query.

    Fields required:
    - location: string (place / taluka / district name)
    - data_scope: "single" or "multiple"
    - user_type: "layman" or "professional"

    Rules:
    - If query mentions years, trends, history, comparison → multiple
    - Else → single
    - If technical words (stage, recharge, draft, CGWB) → professional
    - Else → layman

    Return ONLY valid JSON.
    No markdown.
    No explanation.

    JSON format:
    {{
      "location": "",
      "data_scope": "single",
      "user_type": "layman"
    }}

    User query:
    {user_query}
    """
    gemini_rate_limit_guard() 
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    raw = (response.text or "").strip()
    print("[DEBUG] Gemini raw output:", raw)

    # ---- Safety layer ----
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        print("[WARN] Gemini did not return JSON, falling back")
        return fallback_metadata(user_query)

    try:
        metadata = json.loads(match.group())
    except json.JSONDecodeError:
        print("[WARN] JSON parse failed, falling back")
        return fallback_metadata(user_query)

    # ---- Validation & defaults ----
    metadata["location"] = metadata.get("location", "").strip()

    if metadata.get("data_scope") not in ("single", "multiple"):
        metadata["data_scope"] = "single"

    if metadata.get("user_type") not in ("layman", "professional"):
        metadata["user_type"] = "layman"

    print("[INFO] Final metadata:", metadata)
    return metadata



YEAR_JSON_MAP = {
    "2016-17": "./Ingres_Data/Ingres_16-17.json",
    "2019-20": "./Ingres_Data/Ingres_19-20.json",
    "2021-22": "./Ingres_Data/Ingres_21-22.json",
    "2022-23": "./Ingres_Data/Ingres_22-23.json",
    "2023-24": "./Ingres_Data/Ingres_23-24.json",
    "2024-25": "./Ingres_Data/Ingres_24-25.json"
}

def fetch_multi_year_data(location: str):
    print("[STEP] Fetching multi-year data")
    collected_data = []

    for year, path in YEAR_JSON_MAP.items():
        print(f"[DEBUG] Checking year {year}")

        if not os.path.exists(path):
            print(f"[WARN] Missing data for {year}")
            continue

        with open(path, "r", encoding="utf-8") as f:
            year_json = json.load(f)

        match = json_search.search_by_location_name(
            year_json,
            location,
            score_cutoff=70
        )

        if match:
            collected_data.append({
                "year": year,
                "data": match
            })

    return collected_data

def generate_groundwater_html_report(user_query, data, user_type, data_scope):
    print("[STEP] Generating HTML report via Gemini")

    prompt = f"""
    You are an expert groundwater analyst and frontend developer.

USER QUERY:
{user_query}

USER TYPE:
{user_type}

DATA SCOPE:
{data_scope}

DATA:
{json.dumps(data)}

TASKS:
1. Explain groundwater status clearly.
2. If multiple years:
   - Show year-wise trend.
   - Predict next year's groundwater level (approximate).
   - Handle missing years gracefully.
3. Adjust language:
   - Layman → simple explanations.
   - Professional → technical terms.

OUTPUT REQUIREMENT:
Generate a SINGLE, self-contained HTML file.

DESIGN & RESPONSIVENESS (CRITICAL):
1. The report MUST work perfectly on:
   - Mobile phones
   - Tablets
   - Desktop / laptop screens
2. Use Tailwind CSS via CDN.
3. Use a responsive layout:
   - Mobile: single-column stacked layout
   - Desktop: multi-column grid where appropriate
4. Use readable font sizes for mobile (no tiny text).
5. Ensure proper spacing and padding for touch interaction.

CHART REQUIREMENTS (VERY IMPORTANT):
1. Use Chart.js for all charts.
2. Charts MUST NOT exceed screen height.
3. DO NOT allow charts to become 2–4× screen height.
4. Every chart MUST be wrapped inside a fixed-height container:
   - Mobile height: ~280–320px
   - Desktop height: ~320–400px
5. Wrap each <canvas> like this:
   <div class="relative w-full h-72 md:h-80">
       <canvas></canvas>
   </div>
6. In Chart.js configuration, you MUST include:
   options: {
     responsive: true,
     maintainAspectRatio: false
   }
7. Charts should resize automatically with screen size.

CONTENT STRUCTURE:
1. Executive Summary (top section)
2. Key Insights (bulleted list)
3. Groundwater status interpretation
4. Charts section (Recharge, Draft, Trend if applicable)
5. Tabular groundwater balance (if data available)

DARK MODE:
- Use a clean dark theme suitable for dashboards.
- Ensure sufficient contrast for readability.

CONSTRAINTS:
- Return ONLY raw HTML.
- Do NOT use markdown blocks.
- Do NOT include explanations or comments.
- Start output with <!DOCTYPE html>.

    """
    gemini_rate_limit_guard() 
    model = genai.GenerativeModel("gemini-2.5-flash")
    result = model.generate_content(prompt)

    return result.text.replace("```html", "").replace("```", "").strip()


@app.route("/process_groundwater_query", methods=["POST"])
def process_groundwater_query():
    try:
        print("[STEP] Groundwater query API called")

        data = request.get_json()
        user_query = data.get("query")

        if not user_query:
            return jsonify({"error": "Missing query"}), 400

        # 1️⃣ Extract metadata
        metadata = extract_query_metadata(user_query)
        location = metadata["location"]
        data_scope = metadata["data_scope"]
        user_type = metadata["user_type"]

        print(f"[INFO] Location: {location}")
        print(f"[INFO] Data Scope: {data_scope}")
        print(f"[INFO] User Type: {user_type}")

        # 2️⃣ Fetch data
        if data_scope == "single":
            print("[STEP] Single-year data pipeline")

            with open("./India_Ingris_Data_Complete.json", "r", encoding="utf-8") as f:
                locations = json.load(f)

            loc_chars = json_search.search_by_location_name(
                locations,
                location,
                score_cutoff=70
            )

            api_response = ingres_taluka_api.fetch_business_data(loc_chars)
            final_data = api_response_script.convert_json(api_response)

        else:
            print("[STEP] Multi-year data pipeline")
            final_data = fetch_multi_year_data(location)

        if not final_data:
            return jsonify({"error": "No data found for given location"}), 404
        
        print("[RATE LIMIT] Waiting for 1 minute to avoid Gemini quota limits...")
        time.sleep(60)

        # 3️⃣ Generate HTML report
        html_content = generate_groundwater_html_report(
            user_query,
            final_data,
            user_type,
            data_scope
        )

        # 4️⃣ Save locally
        filename = f"groundwater_report_{uuid.uuid4()}.html"
        local_path = os.path.join(REPORTS_DIR, filename)

        with open(local_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print("[STEP] Report saved locally")

        # 5️⃣ Upload to Cloudinary
        cloudinary_url = upload_html_to_cloudinary(local_path)
        print("[STEP] Uploaded to Cloudinary")

        return jsonify({
            "status": "success",
            "location": location,
            "data_scope": data_scope,
            "report_url": cloudinary_url
        })

    except Exception as e:
        print("[ERROR]", str(e))
        return jsonify({"error": str(e)}), 500

def get_admin_from_latlon(lat, lon):
    point = Point(lon, lat)

    taluka_row = taluka_gdf[taluka_gdf.contains(point)]
    district_row = district_gdf[district_gdf.contains(point)]

    return {
        "taluka": taluka_row.iloc[0]["NAME_3"] if not taluka_row.empty else None,
        "district": district_row.iloc[0]["NAME_2"] if not district_row.empty else None
    }

def collect_borewell_context(lat, lon):
    env = analyze_location(lat, lon)  # your function

    admin = get_admin_from_latlon(lat, lon)

    return {
        "location": {
            "latitude": lat,
            "longitude": lon,
            "taluka": admin["taluka"],
            "district": admin["district"]
        },
        "environment": env
    }

def fetch_ingres_with_fallback(taluka, district):
    with open("./India_Ingris_Data_Complete.json", "r", encoding="utf-8") as f:
        ingres_data = json.load(f)

    # 1️⃣ Try taluka
    if taluka:
        match = json_search.search_by_location_name(
            ingres_data, taluka, score_cutoff=70
        )
        if match:
            return match, "taluka"

    # 2️⃣ Fallback to district
    if district:
        match = json_search.search_by_location_name(
            ingres_data, district, score_cutoff=70
        )
        if match:
            return match, "district"

    return None, None

def generate_borewell_prompt(context, ingres_data, level_used):
    return f"""
You are a senior groundwater hydrogeologist and environmental consultant
preparing a professional borewell feasibility report for a non-technical user.

IMPORTANT CONTEXT:
This assessment is based on publicly available regional-scale data
and scientific hydrogeological principles.
While exact borewell yield cannot be guaranteed,
the conclusions must be clear, confident, and decision-oriented.

--------------------------------------------------
LOCATION
--------------------------------------------------
Latitude: {context['location']['latitude']}
Longitude: {context['location']['longitude']}
Taluka: {context['location']['taluka']}
District: {context['location']['district']}

--------------------------------------------------
ENVIRONMENTAL & GEOLOGICAL CONTEXT
--------------------------------------------------
{json.dumps(context['environment'], indent=2)}

--------------------------------------------------
GROUNDWATER STATUS DATA
--------------------------------------------------
The following groundwater status data was obtained at the {level_used} level.
If taluka-level data was unavailable, district-level data was used.

{json.dumps(ingres_data, indent=2)}

--------------------------------------------------
TASKS (CRITICAL INSTRUCTIONS)
--------------------------------------------------

1. Perform a COMBINED analysis by considering ALL factors together:
   - Rainfall
   - Lithology (rock type)
   - Land cover
   - Terrain / slope
   - Groundwater status (INGRES data)
   Do NOT analyze them separately.

2. Provide a CLEAR borewell feasibility decision:
   - YES (recommended)
   - CONDITIONAL (possible with precautions)
   - NO (not recommended)

3. If groundwater is likely:
   - Estimate a reasonable borewell depth range (in meters)
   - Mention that this estimate may vary by ±5%
   - Present the estimate confidently (avoid excessive hedging)

4. If data is partially missing:
   - Infer using nearby regional trends
   - Use geological and environmental logic
   - Clearly state assumptions, but do NOT weaken the conclusion

5. If surrounding regions are Critical or Over-Exploited:
   - Firmly recommend AGAINST new borewells
   - Explain the risk of failure or long-term depletion

6. Suggest practical alternatives where applicable:
   - Rainwater harvesting
   - Recharge pits
   - Controlled extraction
   - Seasonal usage planning

7. LANGUAGE REQUIREMENTS:
   - Use simple, layman-friendly language
   - Avoid technical jargon unless briefly explained
   - Sound like a confident groundwater consultant
   - Avoid phrases like “cannot say”, “insufficient to conclude”, “uncertain outcome”

--------------------------------------------------
OUTPUT REQUIREMENTS
--------------------------------------------------

Generate a SINGLE self-contained HTML report.

DESIGN:
- Use Tailwind CSS via CDN
- Clean, professional dark-mode dashboard
- Responsive for mobile and desktop

REPORT STRUCTURE (MANDATORY):
1. Executive Summary (clear verdict at top)
2. Integrated Environmental & Groundwater Assessment
3. Borewell Feasibility & Expected Depth
4. Risks, Limitations & Assumptions (short, honest, not alarming)
5. Final Recommendation & Precautionary Measures

CHARTS:
- Include charts ONLY if they add clarity
- Keep charts compact and readable

CONSTRAINTS:
- Return ONLY raw HTML
- Do NOT include markdown
- Do NOT include explanations outside the report
- Start output with <!DOCTYPE html>

"""


@app.route("/borewell_analysis", methods=["POST"])
def borewell_analysis():
    print("\n================ BOREWELL ANALYSIS START ================")

    try:
        print("[STEP 0] Reading request JSON")
        data = request.get_json()
        print("[DEBUG] Raw request data:", data)

        lat = data.get("latitude")
        lon = data.get("longitude")

        print(f"[STEP 0.1] Latitude: {lat}, Longitude: {lon}")

        if lat is None or lon is None:
            print("[ERROR] Missing latitude or longitude")
            return jsonify({"error": "latitude and longitude required"}), 400

        # 1️⃣ Collect physical + admin context
        print("\n[STEP 1] Collecting environmental & administrative context")
        context = collect_borewell_context(lat, lon)

        print("[DEBUG] Context keys:", context.keys())
        print("[DEBUG] Location info:", context.get("location"))

        taluka = context["location"].get("taluka")
        district = context["location"].get("district")

        print(f"[STEP 1.1] Taluka identified: {taluka}")
        print(f"[STEP 1.2] District identified: {district}")

        # 2️⃣ Fetch INGRES data with fallback
        print("\n[STEP 2] Searching INGRES groundwater data")
        ingres_match, level_used = fetch_ingres_with_fallback(taluka, district)

        print(f"[STEP 2.1] INGRES search level used: {level_used}")

        if ingres_match:
            print("[STEP 2.2] INGRES match found, calling INGRES API")
            api_response = ingres_taluka_api.fetch_business_data(ingres_match)

            print("[STEP 2.3] Shortening INGRES API response")
            shortened = api_response_script.convert_json(api_response)

            print("[DEBUG] Shortened data keys:", 
                  shortened.keys() if isinstance(shortened, dict) else type(shortened))
        else:
            print("[WARN] No INGRES data found at taluka or district level")
            shortened = {"note": "No direct groundwater data found"}

        # 3️⃣ Gemini report generation
        print("\n[STEP 3] Preparing Gemini prompt")
        prompt = generate_borewell_prompt(context, shortened, level_used or "none")

        print("[DEBUG] Prompt length:", len(prompt))

        print("[STEP 3.1] Checking Gemini rate limit")
        gemini_rate_limit_guard()

        print("[STEP 3.2] Calling Gemini model")
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        print("[STEP 3.3] Gemini response received")

        html = (response.text or "")
        html = html.replace("```html", "").replace("```", "").strip()

        print("[DEBUG] Generated HTML size:", len(html))

        # 4️⃣ Save + upload
        print("\n[STEP 4] Saving HTML report locally")
        filename = f"borewell_report_{uuid.uuid4()}.html"
        local_path = os.path.join(REPORTS_DIR, filename)

        with open(local_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"[STEP 4.1] Report saved at: {local_path}")

        print("[STEP 4.2] Uploading report to Cloudinary")
        cloudinary_url = upload_html_to_cloudinary(local_path)

        print("[STEP 4.3] Cloudinary URL:", cloudinary_url)

        print("\n================ BOREWELL ANALYSIS SUCCESS ================\n")

        return jsonify({
            "status": "success",
            "taluka": taluka,
            "district": district,
            "data_level_used": level_used,
            "report_url": cloudinary_url
        })

    except Exception as e:
        print("\n================ BOREWELL ANALYSIS FAILED ================\n")
        print("[EXCEPTION]", str(e))
        return jsonify({"error": str(e)}), 500


def get_rainfall(lat, lon):
    print("[RAIN] Rainfall API called")
    return 100
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "PRECTOT",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": "20250601",
        "end": "20251001",
        "format": "JSON"
    }

    r = requests.get(url, params=params, timeout=20)
    print("[RAIN] HTTP status:", r.status_code)

    data = r.json()
    print("[RAIN] Available parameters:",
          data.get("properties", {}).get("parameter", {}).keys())

    params_block = data.get("properties", {}).get("parameter", {})

    # Prefer corrected precipitation
    if "PRECTOTCORR" in params_block:
        rainfall_data = params_block["PRECTOTCORR"]
        source = "PRECTOTCORR"
    elif "PRECTOT" in params_block:
        rainfall_data = params_block["PRECTOT"]
        source = "PRECTOT"
    else:
        print("[WARN] No precipitation data available")
        return None

    # Remove fill values (-999)
    valid_values = [
        v for v in rainfall_data.values()
        if isinstance(v, (int, float)) and v >= 0
    ]

    total_rainfall = round(sum(valid_values), 2)

    print(f"[RAIN] Using {source}, Total rainfall = {total_rainfall} mm")

    return total_rainfall


def get_slope(lat, lon):
    """
    Terrain slope (degrees)
    """
    print("[SLOPE] Slope API called")
    url = "https://api.opentopodata.org/v1/srtm90m"
    r = requests.get(url, params={"locations": f"{lat},{lon}"}, timeout=10)
    print("data:", r.json())
    return r.json()["results"][0]["elevation"]

import math

def get_esa_worldcover_tile_url(lat, lon):
    """
    Returns the correct ESA WorldCover tile URL
    for a given latitude and longitude.
    """

    lat_deg = math.floor(lat)
    lon_deg = math.floor(lon)

    lat_prefix = "N" if lat_deg >= 0 else "S"
    lon_prefix = "E" if lon_deg >= 0 else "W"

    tile_name = (
        f"ESA_WorldCover_10m_{ESA_WORLDCOVER_YEAR}_{ESA_WORLDCOVER_VERSION}_"
        f"{lat_prefix}{abs(lat_deg):02d}"
        f"{lon_prefix}{abs(lon_deg):03d}_Map.tif"
    )

    tile_url = (
        f"{ESA_WORLDCOVER_BASE_URL}/"
        f"{ESA_WORLDCOVER_VERSION}/{ESA_WORLDCOVER_YEAR}/"
        f"{ESA_WORLDCOVER_LAYER}/{tile_name}"
    )

    return tile_url


def sample_landcover(lat, lon):
    """
    Samples ESA WorldCover land-cover class
    for the given latitude & longitude.
    """

    tile_url = get_esa_worldcover_tile_url(lat, lon)
    print("[LANDCOVER] Using tile:", tile_url)

    try:
        with rasterio.open(tile_url) as ds:
            transformer = Transformer.from_crs(
                "EPSG:4326", ds.crs, always_xy=True
            )

            x, y = transformer.transform(lon, lat)
            row, col = ds.index(x, y)

            value = ds.read(1)[row, col]
            return int(value)

    except Exception as e:
        print("[LANDCOVER ERROR]", str(e))
        return None

def sample_raster(raster_path, lat, lon):
    """
    Sample a single pixel value from a raster (local or COG).
    """
    with rasterio.open(raster_path) as ds:
        transformer = Transformer.from_crs(
            "EPSG:4326", ds.crs, always_xy=True
        )
        x, y = transformer.transform(lon, lat)
        row, col = ds.index(x, y)
        return int(ds.read(1)[row, col])


def get_elevation(lat, lon):
    """
    Elevation above mean sea level (meters)
    """
    print("[ELEV] Elevation API called")
    url = "https://api.open-elevation.com/api/v1/lookup"
    r = requests.get(url, params={"locations": f"{lat},{lon}"}, timeout=10)
    print("status:", r.status_code)
    print("res:",r.json())
    return r.json()["results"][0]["elevation"]

def sample_raster(raster_path, lat, lon):
    """
    Sample a single pixel value from a raster (local or COG).
    """
    with rasterio.open(raster_path) as ds:
        transformer = Transformer.from_crs(
            "EPSG:4326", ds.crs, always_xy=True
        )
        x, y = transformer.transform(lon, lat)
        row, col = ds.index(x, y)
        return int(ds.read(1)[row, col])

def analyze_location(lat, lon):
    """
    Collects environmental + lithological context
    for borewell suitability (regional scale).
    """

    print("\n---------- ANALYZE LOCATION START ----------")

    print("[A1] Raw inputs received")
    print(f"[A1] Latitude: {lat}, Longitude: {lon}")

    lat = round(float(lat), 6)
    lon = round(float(lon), 6)

    print("[A2] Rounded coordinates")
    print(f"[A2] Latitude: {lat}, Longitude: {lon}")

    result = {
        "metadata": {
            "latitude": lat,
            "longitude": lon,
            "analysis_time": datetime.utcnow().isoformat() + "Z"
        }
    }

    # ---- Climate & Terrain ----
    print("\n[A3] Collecting climate & terrain data")

    print("[A3.1] Calling rainfall API")
    rainfall = get_rainfall(lat, lon)
    print(f"[A3.1] Rainfall result: {rainfall}")

    print("[A3.2] Calling elevation API")
    elevation = get_elevation(lat, lon)
    print(f"[A3.2] Elevation result: {elevation}")

    print("[A3.3] Calling slope API (temporary elevation)")
    slope = get_slope(lat, lon)
    print(f"[A3.3] Slope/Elevation result: {slope}")

    result["climate"] = {
        "rainfall_mm": rainfall if rainfall is not None else "Unavailable",
        "elevation_m": elevation if elevation is not None else "Unavailable",
        "slope_deg": slope if slope is not None else "Not calculated"
    }

    # ---- Land Cover ----
    print("\n[A4] Sampling land cover raster")

    lc_code = sample_landcover(lat, lon)
    print(f"[A4] Land cover code: {lc_code}")

    recharge_impact = (
        "Low" if lc_code == 50 else
        "Moderate" if lc_code in (30, 40, 60) else
        "High"
    )

    result["land_cover"] = {
        "code": lc_code,
        "type": LANDCOVER_CLASSES.get(lc_code, "Unknown"),
        "recharge_impact": recharge_impact
    }

    print(f"[A4] Land cover type: {result['land_cover']['type']}")
    print(f"[A4] Recharge impact: {recharge_impact}")

    # ---- Lithology ----
    print("\n[A5] Sampling lithology raster (Geology 2M)")

    litho_code = sample_raster(LITHOLOGY_COG, lat, lon)
    print(f"[A5] Lithology code: {litho_code}")

    groundwater_behavior = {
        1: "Very good groundwater potential (porous alluvium)",
        2: "Moderate groundwater potential (sedimentary formations)",
        3: "Moderate to good groundwater potential (solution cavities)",
        4: "Poor groundwater potential unless fractured",
        5: "Moderate groundwater potential in fractured zones"
    }.get(litho_code, "Uncertain groundwater behavior")

    result["lithology"] = {
        "code": litho_code,
        "type": LITHOLOGY_CLASSES.get(litho_code, "Unknown / Mixed"),
        "groundwater_behavior": groundwater_behavior,
        "data_note": (
            "Lithology derived from GSI Geology 2M map. "
            "This represents regional conditions (~5–10 km scale), "
            "not site-specific borewell guarantees."
        )
    }

    print(f"[A5] Lithology type: {result['lithology']['type']}")
    print(f"[A5] Groundwater behavior: {groundwater_behavior}")

    # ---- Save for traceability ----
    print("\n[A6] Saving analysis result to JSON")

    file_path = f"{DATA_DIR}/location_{lat}_{lon}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    print(f"[A6] File saved at: {file_path}")

    print("---------- ANALYZE LOCATION END ----------\n")

    return result


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

# VISUALIZATION
@app.route('/get_visualization_data', methods=['POST'])
def get_visualization_data():
    try:
        data = request.json
        query = data.get('query', '')
        context = data.get('context', '')
        
        # Extract or generate visualization data based on your groundwater database
        visualization_data = {
            'timeSeries': generate_time_series_data(query),
            'depthData': generate_depth_data(query),
            'qualityDistribution': generate_quality_data(query),
            'seasonalData': generate_seasonal_data(query),
            'statistics': generate_statistics(query),
            'alerts': generate_alerts(query)
        }
        
        return jsonify(visualization_data), 200
    except Exception as e:
        print(f"Error in visualization endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_time_series_data(query):
    # Fetch from your database
    # Return format: [{'month': 'Jan', 'groundwater': 15.5, 'rainfall': 120, 'recharge': 25}, ...]
    return []

def generate_depth_data(query):
    # Return format: [{'depth': '0-10m', 'wells': 45, 'percentage': 30}, ...]
    return []

def generate_quality_data(query):
    # Return format: [{'category': 'Excellent', 'value': 35, 'color': '#10b981'}, ...]
    return []

def generate_seasonal_data(query):
    # Return format: [{'season': 'Pre-Monsoon', 'level': 18.5, 'demand': 75}, ...]
    return []

def generate_statistics(query):
    # Return format: {'avgDepth': '18.5m', 'totalWells': 151, 'rechargeRate': '65%', ...}
    return {}

def generate_alerts(query):
    # Return format: [{'type': 'warning', 'message': '...'}, ...]
    return []

if __name__ == "__main__":
    app.run(debug=True)  # Enable debug mode for development