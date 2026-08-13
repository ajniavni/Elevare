import json
import urllib.request
import re
from datetime import datetime, date

STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", 
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", 
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", 
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", 
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", 
    "Delhi", "Jammu and Kashmir", "Ladakh"
]

PSUS = [
    "ONGC", "NTPC", "SAIL", "BHEL", "IOCL", "GAIL", "POWERGRID", "Coal India", 
    "CIL", "HAL", "BPCL", "HPCL", "NLC", "NMDC", "BEL", "BEML", "REC", "PFC", 
    "SCI", "CONCOR", "RITES", "IRCON", "RVNL", "MRPL", "ISRO", "DRDO", "BARC"
]

def parse_date(text):
    # Search specifically for last date or closing date patterns first
    match = re.search(r'(?:last\s*date|closing\s*date|before|upto|by)[\s:\-\._]*(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})', text, re.IGNORECASE)
    if not match:
        match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})', text)
    
    if match:
        groups = [g for g in match.groups() if g is not None]
        if len(groups) >= 3:
            try:
                day, month, year = int(groups[-3]), int(groups[-2]), int(groups[-1])
                if year < 100:
                    year += 2000
                return date(year, month, day)
            except ValueError:
                return None
    return None

def classify_job(title):
    title_upper = title.upper()
    
    # Assign clean department/board names without feed tags
    department = "Central Government"
    for psu in PSUS:
        if psu in title_upper:
            department = f"PSU - {psu}"
            break
    else:
        for state in STATES:
            if state.upper() in title_upper:
                department = f"State Government - {state}"
                break
        else:
            if "UPSC" in title_upper: department = "UPSC (Central)"
            elif "SSC" in title_upper: department = "SSC (Central)"
            elif "RRB" in title_upper or "RAILWAY" in title_upper: department = "Indian Railways / RRB"
            elif "BANK" in title_upper or "IBPS" in title_upper: department = "Banking / IBPS"
            elif "DEFENCE" in title_upper or "ARMY" in title_upper or "NAVY" in title_upper: department = "Defence Ministry"
            else: department = "Government of India"

    # Assign qualification including ITI / Diploma
    if any(kw in title_upper for kw in ['ITI', 'DIPLOMA', 'POLYTECHNIC', 'NCVT', 'SCVT']):
        qualification = "ITI / Diploma"
    elif any(kw in title_upper for kw in ['8TH', 'VIII', 'CLASS 8', 'DRIVER', 'MALI', 'PEON', 'ATTENDANT', 'SWEEPER', 'HELPER']):
        qualification = "8th Pass"
    elif any(kw in title_upper for kw in ['10TH', 'SSC', 'MATRIC']):
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

    active_jobs = []
    for job in existing_jobs:
        ld = job.get("last_date", "")
        parsed = parse_date(ld)
        if parsed:
            if parsed >= today:
                active_jobs.append(job)
        else:
            active_jobs.append(job)

    new_listings = fetch_live_listings()
    existing_links = {j.get("link") for j in active_jobs if "link" in j}
    for job in new_listings:
        if job["link"] and job["link"] not in existing_links:
            active_jobs.insert(0, job)

    with open("jobs.json", "w") as f:
        json.dump(active_jobs, f, indent=2)
        
    print(f"Database successfully updated. Total active pending listings: {len(active_jobs)}")
