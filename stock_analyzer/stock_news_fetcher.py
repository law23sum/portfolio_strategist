import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class StockNewsFetcher:
    def __init__(self):
        """
        Initialize the fetcher with a base news URL and a Selenium WebDriver.
        """
        self.base_news_url = "https://finance.yahoo.com/quote/{}/news"
        self.driver = self._setup_driver()

    def _setup_driver(self):
        """
        Set up the Selenium WebDriver with headless Chrome.
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service = service, options = chrome_options)
            return driver
        except Exception as e:
            print(f"Failed to set up Selenium WebDriver: {e}")
            raise

    def fetch_stock_news(self, stock_symbol):
        """
        1. Opens the Yahoo Finance news page for a given stock.
        2. Scrolls down for ~13 seconds.
        3. Parses the final loaded page for specific <section> elements.
        4. Within those sections, finds <a> tags containing href.
        5. Visits each unique link (up to 50) and combines all resulting HTML into a single string.

        :param stock_symbol: The stock symbol (e.g., 'NCLH') to fetch news for.
        :return: A single string containing the combined HTML of all pages visited.
        """
        try:
            links_amount = 30
            # Navigate to the page
            news_url = self.base_news_url.format(stock_symbol)
            print(f"Navigating to URL: {news_url}")
            self.driver.get(news_url)

            # Give the page a chance to load
            print("Waiting for the page to load...")
            WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "section[data-testid='storyitem'][role='article']"))
                    )

            # Scroll repeatedly for 30 seconds
            print("Starting to scroll the web page ...")
            start_time = time.time()
            scroll_count = 0
            while time.time() - start_time < 13:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                scroll_count += 1
                # print(f"Performed scroll #{scroll_count}")
                WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "section[data-testid='storyitem'][role='article']"))
                        )
            print("Completed scrolling.")

            # Parse the final page
            print("Parsing the page...")
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # --------------------------------------------------
            # Save prettified HTML for debugging
            # file_name = f"{stock_symbol}_news.html"
            # with open(file_name, "w", encoding = "utf-8") as file:
            #     file.write(soup.prettify())
            # print(f"Prettified news page HTML saved to {file_name}")
            # --------------------------------------------------

            # Collect all <a> tags with an href within specific <section> elements
            print("Extracting <a> tags with href attributes within specific <section> elements...")
            article_sections = soup.find_all(
                    "section",
                    {
                        "data-testid": "storyitem",
                        "role"       : "article"
                        }
                    )
            print(f"Found {len(article_sections)} article sections.")

            article_links = []
            seen_links = set()

            for section in article_sections:
                a_tags = section.find_all("a", href = True)
                for a in a_tags:
                    href = a["href"]
                    # if href.startswith("/"):
                    #     full_link = "https://finance.yahoo.com" + href
                    if href.startswith("http://") or href.startswith("https://"):
                        full_link = href
                    else:
                        # Handle other types of relative links or skip
                        # print(f"Skipping non-HTTP/HTTPS link: {href}")
                        continue
                    if full_link not in seen_links:
                        article_links.append(full_link)
                        seen_links.add(full_link)
                        if len(article_links) >= links_amount:
                            break
                if len(article_links) >= links_amount:
                    break
            print(f"Extracted {len(article_links)} unique article links.")

            # Gather & visit links
            combined_html = ""
            visited_links = 0
            skipped_links = 0

            print("Starting to visit each link and collect HTML...")
            for idx, full_link in enumerate(article_links, 1):
                print(f"Visiting link {idx}: {full_link}")

                try:
                    # Visit each link (may or may not be relevant)
                    self.driver.get(full_link)
                    WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='storyitem']"))
                            )

                    # Parse the article content
                    article_soup = BeautifulSoup(self.driver.page_source, "html.parser")
                    article_content = article_soup.find("div", class_ = "article-wrap no-bb", attrs = {"data-testid": "article-content-wrapper"})
                    if article_content:
                        page_html = article_content.prettify()
                        combined_html += "\n" + page_html
                        visited_links += 1
                        # print(f"Successfully visited and appended HTML from link {idx}")
                    else:
                        # print(f"No specific article content found for link {idx}: {full_link}")
                        skipped_links += 1
                except Exception as e:
                    # If a link fails, skip it
                    print(f"Skipping link {full_link}, error: {e}")
                    skipped_links += 1
                    continue

            print(f"Completed visiting links.") #  Visited: {visited_links}, Skipped: {skipped_links}
            # print("Combined HTML length:", len(combined_html))
            self.close()
            return combined_html

        except Exception as e:
            print(f"Error fetching stock news for {stock_symbol}: {e}")
            raise

    def close(self):
        """
        Close the WebDriver session.
        """
        print("Closing the Selenium WebDriver...")
        self.driver.quit()