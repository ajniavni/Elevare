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

def fetch_job_details(job_url):
    """Visits individual job pages to extract exact last dates and direct official/PDF links"""
    try:
        req = urllib.request.Request(job_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            last_date_str = "Check Official Notice"
            parsed_date = None
            
            # Target exact date patterns near closing/last date keywords
            date_match = re.search(r'(?:last\s*date|closing\s*date|upto|before|by)[\s:\-\._<>a-z/]*(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})', html, re.IGNORECASE)
            if not date_match:
                date_match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})', html)
            
            if date_match:
                groups = [g for g in date_match.groups() if g is not None]
                if len(groups) >= 3:
                    try:
                        d, m, y = int(groups[-3]), int(groups[-2]), int(groups[-1])
                        if y < 100: y += 2000
                        parsed_date = date(y, m, d)
                        last_date_str = parsed_date.strftime('%d-%m-%Y')
                    except ValueError:
                        pass

            # Find direct official notification link or PDF instead of redirecting back
            official_link = job_url
            links = re.findall(r'<a[^>]+href="(https?://[^"]+)"[^>]*>([^<]+)</a>', html, re.IGNORECASE)
            for l, anchor in links:
                l_lower = l.lower()
                anchor_lower = anchor.lower()
                if ('gov.in' in l_lower or 'nic.in' in l_lower or 'pdf' in l_lower or 'apply' in anchor_lower or 'notification' in anchor_lower) and 'freejobalert' not in l_lower:
                    official_link = l
                    break

            return last_date_str, parsed_date, official_link
    except Exception:
        return "Check Official Notice", None, job_url

def classify_job(title):
    title_upper = title.upper()
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

if __name__ == "__main__":
    today = date.today()
    print(f"Syncing jobs for current date: {today}")

    # Reset jobs.json to clean out old unparsed entries
    active_jobs = []

    url = "https://www.freejobalert.com/"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            pattern = r'<a[^>]+href="(https://www\.freejobalert\.com/[^"]+)"[^>]*>([^<]+(?:Online Form|Recruitment|Notification|Walk[- ]in)[^<]*)</a>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            
            seen_links = set()
            count = 0
            
            for link, title in matches:
                clean_title = title.strip()
                if link not in seen_links and len(clean_title) > 10:
                    seen_links.add(link)
                    
                    # Deep crawl up to 15 fresh listings to grab exact dates & direct links
                    if count < 15:
                        last_date_str, parsed_date, direct_link = fetch_job_details(link)
                        
                        if parsed_date and parsed_date < today:
                            continue
                            
                        dept, qual = classify_job(clean_title)
                        
                        active_jobs.append({
                            "dept": dept,
                            "title": clean_title[:75],
                            "qual": qual,
                            "min": 18,
                            "max": 40,
                            "last_date": last_date_str,
                            "link": direct_link
                        })
                        count += 1
    except Exception as e:
        print(f"Scraper error: {e}")

    with open("jobs.json", "w") as f:
        json.dump(active_jobs, f, indent=2)
        
    print(f"Database successfully rebuilt. Total active listings: {len(active_jobs)}")
