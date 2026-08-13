import json
import urllib.request
import xml.etree.ElementTree as ET
import re

def fetch_pib_releases():
    """Fetches official government recruitment releases from Press Information Bureau (PIB)"""
    pib_jobs = []
    url = "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            keywords = ['recruitment', 'vacancy', 'posts', 'examination', 'apply', 'upsc', 'ssc', 'rrb', 'post office']
            for item in root.findall('.//item'):
                title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                
                if any(kw in title.lower() for kw in keywords):
                    pib_jobs.append({
                        "dept": "Government of India Notice (PIB)",
                        "title": title[:65] + "..." if len(title) > 65 else title,
                        "qual": "Graduate",
                        "min": 18,
                        "max": 35,
                        "link": link
                    })
    except Exception as e:
        print(f"PIB fetch error: {e}")
    return pib_jobs

def fetch_freejobalert_listings():
    """Fetches and parses job listings safely from FreeJobAlert"""
    fja_jobs = []
    url = "https://www.freejobalert.com/"
    
    try:
        req = urllib.request.Request(
            url, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
            
            # Extract job titles and links using regular expressions
            pattern = r'<a[^>]+href="(https://www\.freejobalert\.com/[^"]+)"[^>]*>([^<]+(?:Online Form|Recruitment|Notification)[^<]*)</a>'
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            
            seen_links = set()
            for link, title in matches:
                if link not in seen_links and len(title.strip()) > 10:
                    seen_links.add(link)
                    fja_jobs.append({
                        "dept": "FreeJobAlert Feed",
                        "title": title.strip()[:65],
                        "qual": "10th Pass",
                        "min": 18,
                        "max": 40,
                        "link": link
                    })
                    if len(fja_jobs) >= 15:  # Cap to top 15 fresh items per sync
                        break
    except Exception as e:
        print(f"FreeJobAlert fetch notice: {e}")
        
    return fja_jobs

if __name__ == "__main__":
    try:
        with open("jobs.json", "r") as f:
            base_jobs = json.load(f)
    except FileNotFoundError:
        base_jobs = []

    # Aggregate listings from multiple sources
    live_notices = fetch_pib_releases() + fetch_freejobalert_listings()
    
    # Merge and avoid duplicate entries by link
    existing_links = {j.get("link") for j in base_jobs if "link" in j}
    for notice in live_notices:
        if notice["link"] and notice["link"] not in existing_links:
            base_jobs.insert(0, notice)

    # Save back to jobs.json
    with open("jobs.json", "w") as f:
        json.dump(base_jobs, f, indent=2)
        
    print(f"Jobs database updated successfully. Total listings: {len(base_jobs)}")
