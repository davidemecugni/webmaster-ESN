import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import concurrent.futures
import queue
import threading
import time
import logging
import os
import re
from parameters import parameters

# Create crawler directory if it doesn't exist
os.makedirs("crawler", exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler/crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("crawler")

class WebCrawler:
    def __init__(self, start_url, max_workers=10, timeout=10, max_retries=3, delay=0.5, use_txt=False):
        """Initialize the web crawler with configurable parameters."""
        self.start_url = start_url
        self.base_domain = urlparse(start_url).netloc
        self.visited = set()
        self.visited_lock = threading.Lock()
        self.queue = queue.Queue()
        self.max_workers = max_workers
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay = delay
        self.use_txt = use_txt
        self.results = {
            "name_changes": [],
            "old_urls": []
        }
        self.results_lock = threading.Lock()
        
        # File locks for thread-safe writing
        self.error_file_lock = threading.Lock()
        self.checked_file_lock = threading.Lock()
        
        # Initialize files or load from existing
        if not self.use_txt or not os.path.exists("crawler/checked.txt"):
            # Initialize new files
            with open("crawler/error.txt", "w") as f:
                f.write("# URLs that failed after max retries\n")
            
            with open("crawler/checked.txt", "w") as f:
                f.write("# Successfully checked URLs\n")
        else:
            # Load previously checked URLs
            logger.info("Loading previously checked URLs from checked.txt")
            try:
                with open("crawler/checked.txt", "r") as f:
                    for line in f:
                        if not line.startswith('#') and line.strip():
                            with self.visited_lock:
                                self.visited.add(line.strip())
                logger.info(f"Loaded {len(self.visited)} previously checked URLs")
            except Exception as e:
                logger.error(f"Error loading checked.txt: {str(e)}")

    def should_ignore_url(self, url):
        """Check if URL should be ignored based on filtering rules."""
        if 'sites' in url:
            return True
        
        if 'facebook' in url:
            return True
        
        if '?q=events/' in url:
            return True
        
        # Use regex to filter out links containing *sites*
        if re.search(r'sites', url):
            return True

            
        # Ignore all links terminating with 3 digits
        if re.search(r'\d{3}$', url):
            return True
            
        return False

    def save_error_url(self, url, error_message):
        """Save a URL that failed to be processed to error.txt."""
        with self.error_file_lock:
            with open("crawler/error.txt", "a") as f:
                f.write(f"{url} - {error_message}\n")
    
    def save_checked_url(self, url):
        """Save a successfully checked URL to checked.txt."""
        with self.checked_file_lock:
            with open("crawler/checked.txt", "a") as f:
                f.write(f"{url}\n")

    def save_old_urls(self, url, findings):
        """Save old URLs found in the page."""
        with self.results_lock:
            with open("crawler/old_urls.txt", "a") as f:
                f.write(f"{url} - {findings}\n")

    def check_name_change(self, text, url):
        """Check if there's a name change in the text."""
        text = text.lower()
        if 'esn modena' in text:
            if any(new_name in text for new_name in ['esn modena and reggio emilia', 'esn modena e reggio emilia', 'esn more']):
                with self.results_lock:
                    self.results["name_changes"].append(url)
                return True
        return False

    def check_correct_url(self, text, soup, current_url):
        """Check if old URLs are present in text or links."""
        old_urls = ["modena.esn.it", "http://modena.esn.it", "https://modena.esn.it", "esnmodena.it", "http://esnmodena.it", "https://esnmodena.it"]
        findings = []
        
        
        # Check in href attributes
        for a_tag in soup.find_all('a', href=True):
            if any(url in a_tag['href'] for url in old_urls) and not self.should_ignore_url(a_tag['href']):
                findings.append(f"Found in link: {a_tag['href']}")
        
        if findings:
            with self.results_lock:
                self.results["old_urls"].append({
                    "url": current_url,
                    "findings": findings
                })
            return findings
        
        return False

    def extract_links(self, current_url, soup):
        """Extract links from the page that belong to the same domain."""
        links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(current_url, href)
            
            # Parse URL to check domain and filter out fragments
            parsed_url = urlparse(full_url)
            
            # Only process URLs from the same domain and ignore fragments
            if parsed_url.netloc == self.base_domain and not parsed_url.fragment:
                # Remove fragments and normalize URL
                clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                if parsed_url.query:
                    clean_url += f"?{parsed_url.query}"
                
                links.add(clean_url)

        
        return links

    def process_url(self, url):
        """Process a single URL: fetch content, analyze, and extract new links."""
        if not url:
            return
        
        # Skip if URL should be ignored
        if self.should_ignore_url(url):
            logger.debug(f"Skipping filtered URL: {url}")
            return
        
        # Skip if URL has already been processed
        with self.visited_lock:
            if url in self.visited:
                return
            self.visited.add(url)
        
        logger.info(f"Processing: {url}")
        
        # Try to fetch the page with retries
        success = False
        error_message = ""
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()  # Raise exception for 4XX/5XX responses
                
                soup = BeautifulSoup(response.content, 'html.parser')
                text = soup.get_text()
                
                # Check for name changes
                self.check_name_change(text, url)
                
                # Check for old URLs
                url_findings = self.check_correct_url(text, soup, url)
                if url_findings:
                    logger.warning(f"Old URL references found at {url}: {url_findings}")
                    self.save_old_urls(url, url_findings)
                
                # Extract new links and add them to the queue
                links = self.extract_links(url, soup)
                for link in links:
                    with self.visited_lock:
                        if link not in self.visited:
                            self.queue.put(link)
                
                # Mark as successful and save to checked.txt
                success = True
                self.save_checked_url(url)
                
                # Add delay to be nice to the server
                time.sleep(self.delay)
                break  # Exit retry loop on success
                
            except requests.exceptions.RequestException as e:
                error_message = str(e)
                logger.error(f"Error fetching {url} (attempt {attempt+1}/{self.max_retries}): {error_message}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to process {url} after {self.max_retries} attempts")
                else:
                    time.sleep(self.delay * (attempt + 1))  # Exponential backoff
        
        # If all retries failed, save to error.txt
        if not success:
            self.save_error_url(url, error_message)
    
    def worker(self):
        """Worker function that processes URLs from the queue."""
        while True:
            try:
                url = self.queue.get(block=False)
                self.process_url(url)
                self.queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Unexpected error in worker: {str(e)}")
                # Save unexpected errors to error file too
                self.save_error_url(url if 'url' in locals() else "unknown_url", f"Unexpected error: {str(e)}")
                self.queue.task_done()
    
    def crawl(self):
        """Start the crawling process with multiple threads."""
        start_time = time.time()
        logger.info(f"Starting crawl from {self.start_url} with {self.max_workers} workers")
        logger.info(f"Using checked.txt for previously visited URLs: {self.use_txt}")
        
        # Add the starting URL to the queue if not already visited
        with self.visited_lock:
            if self.start_url not in self.visited:
                self.queue.put(self.start_url)
        
        # Create and start worker threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Start initial batch of workers
            workers = [executor.submit(self.worker) for _ in range(self.max_workers)]
            
            # Monitor queue and add more workers as needed
            while not self.queue.empty() or any(not worker.done() for worker in workers):
                active_workers = sum(1 for worker in workers if not worker.done())
                if active_workers < self.max_workers:
                    # Add more workers if needed
                    new_workers = [executor.submit(self.worker) 
                                 for _ in range(self.max_workers - active_workers)]
                    workers.extend(new_workers)
                time.sleep(0.5)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Crawl completed in {elapsed_time:.2f} seconds")
        logger.info(f"Visited {len(self.visited)} pages")
        
        # Count successes and failures
        with open("crawler/checked.txt") as f:
            success_count = sum(1 for line in f if not line.startswith('#'))
        
        with open("crawler/error.txt") as f:
            error_count = sum(1 for line in f if not line.startswith('#'))
        
        logger.info(f"Successfully processed: {success_count} pages")
        logger.info(f"Failed to process: {error_count} pages")
        
        # Report findings
        if self.results["name_changes"]:
            logger.info(f"Found {len(self.results['name_changes'])} pages with name changes")
            for url in self.results["name_changes"]:
                logger.info(f"  - {url}")
        
        if self.results["old_urls"]:
            logger.info(f"Found {len(self.results['old_urls'])} pages with old URL references")
            for item in self.results["old_urls"]:
                logger.info(f"  - {item['url']}")
                for finding in item['findings']:
                    logger.info(f"    * {finding}")
        
        return self.results

if __name__ == '__main__':
    # Get settings from parameters file
    start_url = parameters["website"]
    max_workers = parameters.get("max_workers", 10)
    timeout = parameters.get("timeout", 10)
    max_retries = parameters.get("max_retries", 3)
    delay = parameters.get("delay", 0.5)
    use_txt = parameters.get("use_txt", False)  # Option to use checked.txt for already explored sites
    
    # Initialize and run the crawler
    crawler = WebCrawler(
        start_url=start_url,
        max_workers=max_workers,
        timeout=timeout,
        max_retries=max_retries,
        delay=delay,
        use_txt=use_txt
    )
    
    results = crawler.crawl()