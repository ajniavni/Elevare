import json
import urllib.request
import re
from datetime import datetime, date

# Comprehensive list of Indian States and UTs for automatic tagging
STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", 
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", 
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", 
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", 
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", 
    "Delhi", "Jammu and Kashmir", "Ladakh"
]

# Major Public Sector Undertakings (PSUs) and Government Enterprises
PSUS = [
    "ONGC", "NTPC", "SAIL", "BHEL", "IOCL", "GAIL", "POWERGRID", "Coal India", 
    "CIL", "HAL", "BPCL", "HPCL", "NLC", "NMDC", "BEL", "BEML", "REC", "PFC", 
    "SCI", "CONCOR", "RITES", "IRCON", "RVNL", "MRPL", "ISRO", "DRDO", "BARC"
]

def parse_date(text):
    """Extracts date in DD-MM-YYYY or DD/MM/YYYY format and returns a date object"""
    match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})', text)
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if year < 100:
            year += 2000
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None

def classify_job(title):
    """Classifies job into PSU, State Govt, or Central Govt, and detects qualifications including 8th Pass"""
    title_upper = title.upper()
    
    # 1. Check for Public Sector Undertakings (PSUs)
    department = "Central Government"
    for psu in PSUS:
        if psu in title_upper:
            department = f"Public Sector Undertaking (PSU) - {psu}"
            break
    
    # 2. Check for State Government mentions if not already matched as a PSU
    if department == "Central Government":
        for state in STATES:
            if state.upper() in title_upper:
                department = f"State Government - {state}"
                break
        else:
            if any(kw in title_upper for kw in ['UPSC', 'SSC', 'RRB', 'BANK', 'IBPS', 'DEFENCE', 'ARMY', 'NAVY', 'AIRFORCE', 'CENTRAL']):
                department = "Central Government (All India)"
            else:
                department = "Government of India / Central Sector"

    # 3. Detect Qualification including 8th Pass
    if any(kw in title_upper for kw in ['8TH', 'VIII', 'CLASS 8', 'DRIVER', 'MALI', 'PEON', 'ATTENDANT', 'SWEEPER', 'HELPER']):
        qualification = "8th Pass"
    elif any(kw in title_upper for kw in ['10TH', 'SSC', 'MATRIC', 'ITI']):
        qualification = "10th Pass"
    elif any(kw in title_upper for kw in ['12TH', 'INTER', 'HSC']):
        qualification = "12th Pass"
    else:
        qualification = "Graduate / Any Degree"

    return department, qualification

def fetch_live_listings():
    jobs = []
    url = "https://www.freejobalert.com/"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            pattern = r'<a[^>]+href="(https://www\.freejobalert\.com/[^"]+)"[^>]*>([^<]+(?:Online Form|Recruitment|Notification|Walk[- ]in)[^<]*)</a>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            today = date.today()
            seen_links = set()
            
            for link, title in matches:
                clean_title = title.strip()
                if link not in seen_links and len(clean_title) > 10:
                    seen_links.add(link)
                    
                    parsed_date = parse_date(clean_title)
                    
                    # AUTOMATIC EXPIRY CHECK: If last date has passed, skip adding this job
                    if parsed_date and parsed_date < today:
                        continue
                        
                    dept, qual = classify_job(clean_title)
                    last_date_str = parsed_date.strftime('%d-%m-%Y') if parsed_date else "Open / Check Notice"
                    
                    jobs.append({
                        "dept": dept,
                        "title": clean_title[:75],
                        "qual": qual,
                        "min": 18,
                        "max": 40,
                        "last_date": last_date_str,
                        "link": link
                    })
    except Exception as e:
        print(f"Scraper error: {e}")
    return jobs

if __name__ == "__main__":
    today = date.today()
    print(f"Syncing jobs for current date: {today}")

    try:
        with open("jobs.json", "r") as f:
            existing_jobs = json.load(f)
    except FileNotFoundError:
        existing_jobs = []

    # CLEAN UP: Remove any previously stored listings whose last date has now passed
    active_jobs = []
    for job in existing_jobs:
        ld = job.get("last_date", "")
        parsed = parse_date(ld)
        if parsed:
            if parsed >= today:
                active_jobs.append(job)
        else:
            active_jobs.append(job) # Keep active if date couldn't be strictly parsed

    # Fetch fresh live listings
    new_listings = fetch_live_listings()
    
    existing_links = {j.get("link") for j in active_jobs if "link" in j}
    for job in new_listings:
        if job["link"] and job["link"] not in existing_links:
            active_jobs.insert(0, job)

    # Save cleaned, active database back to jobs.json
    with open("jobs.json", "w") as f:
        json.dump(active_jobs, f, indent=2)
        
    print(f"Database successfully updated. Total active pending listings: {len(active_jobs)}")
