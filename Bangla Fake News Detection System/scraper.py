import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import re

# === Target News Sites (Updated) ===
NEWS_SITES = {
    "Prothom Alo": "https://www.prothomalo.com/",
    "Jamuna TV": "https://jamuna.tv/",
    "BBC Bangla": "https://www.bbc.com/bengali",
    "NTV BD": "https://www.ntvbd.com/"
}

# === Clean/Normalize URL ===
def normalize_url(url):
    return re.sub(r'\?.*$', '', url.strip())

# === Scrape headlines & links ===
def scrape_homepage_links(base_url):
    try:
        res = requests.get(base_url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')

        links_and_headlines = []
        for article in soup.find_all('a', href=True):
            href = article['href']
            full_url = urljoin(base_url, href)
            headline = article.get_text(strip=True)

            # Keep only valid news links
            if any(kw in full_url for kw in ["/news", "/article", "/story", "/bangladesh", "/international", "/sports", "/entertainment", "/politics", "/crime", "/world", "/business", "/economy"]):
                if headline:
                    links_and_headlines.append((normalize_url(full_url), headline))

            if len(links_and_headlines) >= 50:
                break

        return links_and_headlines
    except Exception as e:
        print(f"⚠ Error scraping {base_url}: {e}")
        return []

# === Main Scraper Function ===
def run_scraper():
    all_data = []

    for site_name, site_url in NEWS_SITES.items():
        print(f"🔍 Scraping: {site_name}")
        links_and_headlines = scrape_homepage_links(site_url)

        for link, headline in links_and_headlines[:50]:  # Ensure 50 entries max
            all_data.append({
                "source": site_name,
                "news_link": link,
                "text": headline.lower(),  # Storing headlines
                "label": "real"
            })

    df = pd.DataFrame(all_data)
    df.drop_duplicates(subset="news_link", inplace=True)
    df.to_csv("data/data.csv", index=False)
    print("✅ Done! Saved to data/data.csv")

if __name__ == "__main__":
    run_scraper()