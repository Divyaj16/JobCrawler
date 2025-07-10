import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path


class LinkedInJobCrawler:
    def __init__(self, config_file=None):
        """Initialize the LinkedIn job crawler with configuration."""
        # Create base directory path
        base_dir = Path.cwd() / "data" 
        
        # Create directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)
        
        # Set file paths
        if config_file is None:
            config_file = base_dir / "carwler.json"
        
        database_path = base_dir / "database.json"
        
        # Default configuration
        self.config = {
            'job_url': 'https://www.linkedin.com/jobs/search/?f_TPR=r86400&f_E=2%2C3&keywords=data%20engineer&location=United%20States&start=0',
            'keywords': ['python', 'developer', 'engineer', 'data engineer', 'airflow', 'etl', 'aws', 'snowflake', 'databricks'],
            'excluded_keywords': ['5+ years', '4+ years', 'manager', 'director'],
            'database_file': str(database_path),
            'user_agents': [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ],
            'request_delay': {
                'min_seconds': 3,
                'max_seconds': 7
            }
        }
        
        # Convert config_file to string if it's a Path object
        config_file = str(config_file)
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                custom_config = json.load(f)
                # Update config but ensure database_file uses the correct local path
                custom_config['database_file'] = str(database_path)
                self.config.update(custom_config)
        else:
            # Create parent directory if it doesn't exist
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            # Save default configuration
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
                
        # Initialize the webdriver
        self.driver = None
        
        # Load previous jobs
        self.previous_jobs = self.load_previous_jobs()

        
    def setup_driver(self):
        """Set up Selenium WebDriver with enhanced stealth capabilities."""
        if self.driver is not None:
            try:
                self.driver.quit()
            except:
                pass
                
        chrome_options = Options()
        
        # Enhanced stealth options
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--window-size=1366,768")
        chrome_options.add_argument("--disable-gpu")
        
        # Random user agent
        user_agent = random.choice(self.config['user_agents'])
        chrome_options.add_argument(f"--user-agent={user_agent}")
        
        # Additional headers to appear more human-like
        chrome_options.add_argument("--accept-language=en-US,en;q=0.9")
        chrome_options.add_argument("--accept-encoding=gzip, deflate, br")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute stealth script to hide automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": user_agent
            })
            
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            print("Trying with direct ChromeDriver...")
            self.driver = webdriver.Chrome(options=chrome_options)
            
    def human_like_delay(self, min_delay=None, max_delay=None):
        """Add human-like delay between actions."""
        if min_delay is None:
            min_delay = self.config['request_delay']['min_seconds']
        if max_delay is None:
            max_delay = self.config['request_delay']['max_seconds']
        
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        
    def human_like_scroll(self):
        """Implement human-like scrolling behavior to load more jobs."""
        if not self.driver:
            return
            
        print("Starting enhanced scrolling to load all available jobs...")
        scroll_attempts = 0
        max_scroll_attempts = 15  # Increased to load more jobs
        
        while scroll_attempts < max_scroll_attempts:
            # Get current page height
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content to load
            time.sleep(random.uniform(2.0, 4.0))
            
            # Check if "Show more jobs" button exists and click it
            try:
                show_more_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Show more') or contains(text(), 'See more jobs')]")
                if show_more_button.is_displayed() and show_more_button.is_enabled():
                    self.driver.execute_script("arguments[0].click();", show_more_button)
                    print("Clicked 'Show more jobs' button")
                    time.sleep(random.uniform(3.0, 5.0))
            except:
                pass
            
            # Check if page height increased (new content loaded)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == current_height:
                # No new content, try a few more times
                scroll_attempts += 1
                if scroll_attempts >= 3:
                    # Try scrolling up and down to trigger loading
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.8);")
                    time.sleep(1)
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
            else:
                scroll_attempts = 0  # Reset counter if new content loaded
                
            print(f"Scroll attempt {scroll_attempts + 1}/{max_scroll_attempts}, Page height: {new_height}")
        
        print("Finished scrolling to load jobs")
                
    def load_previous_jobs(self):
        """Load previously scraped jobs from database file."""
        if not os.path.exists(self.config['database_file']):
            return []
        try:
            with open(self.config['database_file'], 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading previous jobs: {e}")
            return []
            
    def save_jobs(self, jobs):
        """Save jobs to the database file."""
        try:
            with open(self.config['database_file'], 'w') as f:
                json.dump(jobs, f, indent=4)
            print(f"Jobs saved to {self.config['database_file']}")
        except Exception as e:
            print(f"Error saving jobs: {e}")
            
    def is_new_job(self, job):
        """Check if a job is new by comparing with previous jobs."""
        for prev_job in self.previous_jobs:
            # Compare key fields to determine if it's the same job
            if (job['title'] == prev_job['title'] and 
                job['company'] == prev_job['company'] and
                job['location'] == prev_job['location']):
                return False
        return True
        
    def is_job_relevant(self, job_title):
        """Check if job title contains desired keywords and not excluded keywords."""
        title_lower = job_title.lower()
        
        # Check if any keyword is in the title (less strict for LinkedIn since we already filtered by keyword in URL)
        has_keyword = True
        
        # Check if any excluded keyword is in the title
        has_excluded = any(keyword.lower() in title_lower for keyword in self.config['excluded_keywords'])
        
        return has_keyword and not has_excluded
        
    def extract_job_data_multiple_selectors(self, card):
        """Try multiple selector strategies to extract job data."""
        job_data = {}
        
        # Try multiple title selectors
        title_selectors = [
            'h3.base-search-card__title a',
            'h3.base-search-card__title',
            '.job-search-card__title a',
            '.job-search-card__title',
            'h3 a[data-tracking-control-name="public_jobs_jserp-result_search-card"]',
            '.base-card__full-link',
            'a[data-tracking-control-name="public_jobs_jserp-result_search-card"]',
            '.job-search-card .job-search-card__title',
            'h4.job-search-card__title',
            'h3.job-search-card__title',
            'a.job-search-card__title-link'
        ]
        
        for selector in title_selectors:
            try:
                title_element = card.select_one(selector)
                if title_element and title_element.get_text(strip=True):
                    job_data['title'] = title_element.get_text(strip=True)
                    # Also try to get URL from title link
                    if title_element.get('href'):
                        job_data['url'] = title_element['href']
                    break
            except:
                continue
                
        # Try multiple company selectors
        company_selectors = [
            'h4.base-search-card__subtitle',
            '.job-search-card__subtitle-link',
            '.base-search-card__subtitle a',
            'h4 a[data-tracking-control-name="public_jobs_jserp-result_job-search-card-subtitle"]',
            '.job-search-card__subtitle',
            'h4.job-search-card__subtitle',
            '.base-search-card__subtitle',
            'a[data-tracking-control-name="public_jobs_jserp-result_job-search-card-subtitle"]',
            '.job-search-card .job-search-card__subtitle'
        ]
        
        for selector in company_selectors:
            try:
                company_element = card.select_one(selector)
                if company_element and company_element.get_text(strip=True):
                    job_data['company'] = company_element.get_text(strip=True)
                    break
            except:
                continue
                
        # Try multiple location selectors
        location_selectors = [
            'span.job-search-card__location',
            '.base-search-card__metadata span',
            '.job-search-card__location',
            'span[data-tracking-control-name="public_jobs_jserp-result_job-search-card-location"]'
        ]
        
        for selector in location_selectors:
            try:
                location_element = card.select_one(selector)
                if location_element and location_element.get_text(strip=True):
                    job_data['location'] = location_element.get_text(strip=True)
                    break
            except:
                continue
                
        # Try multiple URL selectors if not already found
        if 'url' not in job_data:
            url_selectors = [
                'a.base-card__full-link',
                '.base-search-card__title a',
                'h3 a',
                'a[data-tracking-control-name="public_jobs_jserp-result_search-card"]',
                'a[href*="/jobs/view/"]',
                '.job-search-card__title a',
                'a.job-search-card__title-link',
                '.job-search-card a[href*="/jobs/view/"]',
                'a[data-entity-urn*="jobPosting"]'
            ]
            
            for selector in url_selectors:
                try:
                    url_element = card.select_one(selector)
                    if url_element and url_element.get('href'):
                        job_data['url'] = url_element['href']
                        break
                except:
                    continue
                    
        # Try multiple date selectors
        date_selectors = [
            'time.job-search-card__listdate',
            'time',
            '.job-search-card__listdate--new',
            'span[data-tracking-control-name="public_jobs_jserp-result_job-search-card-date"]'
        ]
        
        for selector in date_selectors:
            try:
                date_element = card.select_one(selector)
                if date_element and date_element.get_text(strip=True):
                    job_data['date_posted'] = date_element.get_text(strip=True)
                    break
            except:
                continue
                
        return job_data
        
    def scrape_linkedin_jobs(self):
        """Scrape job data from LinkedIn with enhanced techniques."""
        jobs = []
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if self.driver is None:
                    self.setup_driver()
                
                if not self.driver:
                    raise Exception("Failed to initialize WebDriver")
                    
                print(f"Fetching LinkedIn jobs from: {self.config['job_url']}")
                
                # Navigate with human-like behavior
                self.driver.get(self.config['job_url'])
                
                # Wait for initial page load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Add human-like delay
                self.human_like_delay(3, 6)
                
                # Try to accept cookies if present
                try:
                    cookie_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]"))
                    )
                    cookie_button.click()
                    self.human_like_delay(1, 2)
                except:
                    pass
                
                # Human-like scrolling to load more content
                print("Scrolling to load more job listings...")
                self.human_like_scroll()
                
                # Wait for content to load
                self.human_like_delay(2, 4)
                
                # Get the page source after JavaScript execution
                html = self.driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                # Try multiple selectors for job cards with more comprehensive search
                job_card_selectors = [
                    'div.base-card',
                    '.job-search-card',
                    '.base-search-card',
                    'li[data-occludable-job-id]',
                    '.jobs-search__results-list li',
                    'div[data-entity-urn*="jobPosting"]',
                    '.jobs-search-results__list-item',
                    'div.job-search-card',
                    'li.jobs-search-results__list-item'
                ]
                
                job_cards = []
                for selector in job_card_selectors:
                    cards = soup.select(selector)
                    if cards:
                        print(f"Found {len(cards)} job cards using selector: {selector}")
                        job_cards.extend(cards)
                        # Don't break, collect from all working selectors
                
                # Remove duplicates by converting to set and back (based on HTML content)
                unique_cards = []
                seen_urls = set()
                
                for card in job_cards:
                    # Try to find a unique identifier (URL) for deduplication
                    url_elements = card.select('a[href*="/jobs/view/"]')
                    if url_elements:
                        url = url_elements[0].get('href', '')
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            unique_cards.append(card)
                    else:
                        # If no URL found, still include the card
                        unique_cards.append(card)
                
                job_cards = unique_cards
                print(f"Total unique job cards after deduplication: {len(job_cards)}")
                
                if not job_cards:
                    print("No job cards found with any selector")
                    retry_count += 1
                    continue
                
                # Process each job card
                print(f"Processing {len(job_cards)} job cards...")
                processed_count = 0
                skipped_masked = 0
                skipped_missing_data = 0
                skipped_no_url = 0
                
                for i, card in enumerate(job_cards):
                    try:
                        job_data = self.extract_job_data_multiple_selectors(card)
                        
                        # Skip if essential data is missing
                        if not job_data.get('title') or not job_data.get('company'):
                            skipped_missing_data += 1
                            continue
                            
                        title = job_data['title']
                        company = job_data['company']
                        
                        # Skip if data is masked with asterisks
                        if '*' in title or '*' in company:
                            print(f"Skipping masked job data: {title} at {company}")
                            skipped_masked += 1
                            continue
                            
                        if not self.is_job_relevant(title):
                            continue
                            
                        # Build complete job record
                        job = {
                            'title': title,
                            'company': company,
                            'location': job_data.get('location', 'Unknown Location'),
                            'date_posted': job_data.get('date_posted', 'Recent'),
                            'url': job_data.get('url', ''),
                            'source': 'LinkedIn',
                            'scraped_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Only add if we have a valid URL
                        if job['url']:
                            jobs.append(job)
                            processed_count += 1
                            if processed_count <= 5:  # Show first 5 jobs found
                                print(f"Found valid job {processed_count}: {title} at {company}")
                        else:
                            skipped_no_url += 1
                        
                    except Exception as e:
                        print(f"Error extracting job data from card {i}: {e}")
                        continue
                
                print(f"\nExtraction Summary:")
                print(f"  Total cards processed: {len(job_cards)}")
                print(f"  Valid jobs extracted: {processed_count}")
                print(f"  Skipped (masked data): {skipped_masked}")
                print(f"  Skipped (missing data): {skipped_missing_data}")
                print(f"  Skipped (no URL): {skipped_no_url}")
                
                # If we got some valid jobs, break the retry loop
                if jobs:
                    break
                    
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Retry {retry_count}/{max_retries} - No valid jobs found, retrying...")
                    self.human_like_delay(5, 10)
                
            except Exception as e:
                print(f"Error scraping LinkedIn (attempt {retry_count + 1}): {e}")
                retry_count += 1
                
                # Try to restart the driver if it failed
                try:
                    if self.driver:
                        self.driver.quit()
                except:
                    pass
                self.driver = None
                
                if retry_count < max_retries:
                    self.human_like_delay(10, 15)
                    
        return jobs
        
    def run_once(self):
        """Run the LinkedIn job crawler once."""
        print(f"Starting LinkedIn job scraping at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Looking for jobs posted in the last 24 hours matching 'data engineer'")
        
        # Scrape LinkedIn jobs
        current_jobs = self.scrape_linkedin_jobs()
        
        # Identify new jobs
        new_jobs = []
        for job in current_jobs:
            if self.is_new_job(job):
                job['email_sent'] = False
                new_jobs.append(job)
        
        # Keep jobs from the last hour and add new jobs
        one_hour_ago = datetime.now() - timedelta(hours=1)
        filtered_previous_jobs = [
            job for job in self.previous_jobs 
            if datetime.strptime(job['scraped_date'], '%Y-%m-%d %H:%M:%S') >= one_hour_ago
        ]
        all_jobs = filtered_previous_jobs + new_jobs
        self.save_jobs(all_jobs)
        
        print(f"\nFound {len(current_jobs)} total job listings")
        print(f"Identified {len(new_jobs)} new job postings")
        
        return new_jobs
        
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                print("Browser closed successfully")
            except:
                pass
            self.driver = None


# Run the LinkedIn crawler once
if __name__ == "__main__":
    try:
        print("=== LinkedIn Job Crawler - Data Engineer Jobs (Last 24 Hours) ===")
        crawler = LinkedInJobCrawler()
        new_jobs = crawler.run_once()
        
        # Print a summary of results
        if new_jobs:
            print("\n===== NEW JOBS FOUND =====")
            for i, job in enumerate(new_jobs, 1):
                print(f"{i}. {job['title']} at {job['company']}")
                print(f"   Location: {job['location']}")
                print(f"   Posted: {job['date_posted']}")
                print(f"   URL: {job['url']}")
                print()
        else:
            print("\nNo new data engineer jobs found on LinkedIn in the last 24 hours.")
            
    except KeyboardInterrupt:
        print("\nJob crawler stopped by user")
    except Exception as e:
        print(f"\nError in job crawler: {e}")
    finally:
        # Clean up resources
        if 'crawler' in locals():
            crawler.cleanup()


