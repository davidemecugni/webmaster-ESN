import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from parameters import parameters

def check_name_change(text):
    text = text.lower()
    if 'esn modena' in text:
        if any(new_name in text for new_name in ['esn modena and reggio emilia', 'esn modena e reggio emilia', 'esn more']):
            return True
    return False

def extract_links(url, soup):
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(url, href)
        if urlparse(full_url).netloc == urlparse(url).netloc:  # Ensure the link is within the same domain
            links.add(full_url)
    return links

def crawl_website(url, visited=set()):
    if url in visited:
        return
    visited.add(url)
    
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        
        if check_name_change(text):
            print(f"Name change detected on: {url}")
        
        links = extract_links(url, soup)
        for link in links:
            crawl_website(link, visited)

if __name__ == '__main__':
    start_url = parameters["website"]
    crawl_website(start_url)