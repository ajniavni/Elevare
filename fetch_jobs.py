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
    try:
        req = urllib.request.Request(job_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=6) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            last_date_str = "Check Official Notice"
            parsed_date = None
            
            date_match = re.search(r'(?:last\s*date|closing\s*date|upto|before|by|exams?\s*date)[^<\d]*(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})', html, re.IGNORECASE)
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

            direct_link = job_url
            all_links = re.findall(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE)
            
            for l, anchor_html in all_links:
                anchor = re.sub(r'<[^>]+>', '', anchor_html).strip().lower()
                if not l.startswith('http'):
                    l = "https://www.sarkariresult.com/" + l.lstrip('/')
                
                if 'apply online' in anchor or 'official website' in anchor:
                    if 'sarkariresult.com' not in l or len(l) > 30:
                        direct_link = l
                        break
            else:
                for l, anchor_html in all_links:
                    if not l.startswith('http'):
                        l = "https://www.sarkariresult.com/" + l.lstrip('/')
                    l_lower = l.lower()
                    if ('gov.in' in l_lower or 'nic.in' in l_lower or '.pdf' in l_lower) and 'sarkariresult' not in l_lower:
                        direct_link = l
                        break

            return last_date_str, parsed_date, direct_link
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

    if any(kw in title_upper for kw in ['ITI', 'DIPLOMA', 'POLYTECHNIC', 'NCVT', 'SCVT', 'TECHNICIAN']):
        qualification = "ITI / Diploma"
    elif any(kw in title_upper for kw in ['8TH', 'VIII', 'CLASS 8', 'DRIVER', 'MALI', 'PEON', 'ATTENDANT', 'SWEEPER', 'HELPER', 'CANTEEN']):
        qualification = "8th Pass"
    elif any(kw in title_upper for kw in ['10TH', 'SSC', 'MATRIC', 'CONSTABLE', 'GDS', 'GRAMIN DAK SEVAK', 'MTS', 'GROUP D', 'CHSL']):
        qualification = "10th Pass"
    elif any(kw in title_upper for kw in ['12TH', 'INTER', 'HSC', 'CLERK', 'STENO', 'ASSISTANT']):
        qualification = "12th Pass"
    else:
        qualification = "Graduate / Any Degree"

    return department, qualification

if __name__ == "__main__":
    today = date.today()
    print(f"Syncing jobs for current date: {today}")

    active_jobs = []
    url = "https://www.sarkariresult.com/"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            matches = re.findall(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE)
            
            seen_links = set()
            count = 0
            
            for link, anchor_html in matches:
                clean_title = re.sub(r'<[^>]+>', '', anchor_html).strip()
                
                if not link.startswith('http'):
                    full_link = "https://www.sarkariresult.com/" + link.lstrip('/')
                else:
                    full_link = link
                    
                if full_link not in seen_links and len(clean_title) > 5:
                    title_lower = clean_title.lower()
                    if any(kw in title_lower for kw in ['online form', 'recruitment', 'vacancy', 'notice', 'bharti', 'post', 'officer', 'clerk', 'constable', 'uptet', 'police']):
                        seen_links.add(full_link)
                        
                        if count < 35:
                            last_date_str, parsed_date, direct_link = fetch_job_details(full_link)
                            
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
        
    print(f"Database successfully updated. Total active listings: {len(active_jobs)}")
