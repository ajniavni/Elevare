import json
import urllib.request
import xml.etree.ElementTree as ET

def fetch_pib_releases():
    """Fetches official government recruitment releases from Press Information Bureau (PIB)"""
    pib_jobs = []
    # PIB English Recruitment & Press Release RSS Feed
    url = "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
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
                        "qual": "Graduate",  # Default eligibility tier
                        "min": 18,
                        "max": 35,
                        "link": link
                    })
    except Exception as e:
        print(f"Notice fetch error: {e}")
    return pib_jobs

if __name__ == "__main__":
    # Load existing baseline verified database
    try:
        with open("jobs.json", "r") as f:
            base_jobs = json.load(f)
    except FileNotFoundError:
        base_jobs = []

    # Fetch live notices
    live_notices = fetch_pib_releases()
    
    # Merge and avoid duplicates by link
    existing_links = {j.get("link") for j in base_jobs if "link" in j}
    for notice in live_notices:
        if notice["link"] not in existing_links:
            base_jobs.insert(0, notice)

    # Save back to jobs.json
    with open("jobs.json", "w") as f:
        json.dump(base_jobs, f, indent=2)
        
    print(f"Jobs database updated with {len(base_jobs)} total verified listings.")
