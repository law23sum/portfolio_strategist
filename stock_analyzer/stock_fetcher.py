import concurrent
import os
import sys
import zipfile
from sys import platform

import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tenacity import retry, stop_after_attempt, wait_fixed
import yfinance as yf


links_amount = 21


class StockFetcher:
    def __init__(self):
        self.base_quote_url = "https://finance.yahoo.com/quote"
        # self.base_statistics_url = "https://finance.yahoo.com/quote/{}/key-statistics"
        self.base_news_url = "https://finance.yahoo.com/quote/{}/news"
        self.base_history_url = "https://finance.yahoo.com/quote/{}/history/"
        print("Initializing StockFetcher and setting up the driver.")
        self.driver = self._setup_driver()

    def _setup_driver(self):
        """Set up the Selenium WebDriver."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--incognito")

        # def get_latest_chromedriver():
        #     url = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"
        #     latest_version = requests.get(url).text.strip()
        #     driver_url = f"https://chromedriver.storage.googleapis.com/{latest_version}/chromedriver_mac_arm64.zip"
        #
        #     # Determine the extraction path
        #     if getattr(sys, '_MEIPASS', False):  # If running as an executable
        #         extract_path = os.path.join(sys._MEIPASS, "chromedriver")
        #     else:  # Running as a script
        #         extract_path = os.path.abspath("chromedriver")
        #
        #     # Download and extract only if not already present
        #     if not os.path.exists(extract_path):
        #         print(f"Downloading latest ChromeDriver for macOS ARM64 ({latest_version})...")
        #
        #         response = requests.get(driver_url, stream = True)
        #         zip_path = os.path.join(sys._MEIPASS if getattr(sys, '_MEIPASS', False) else ".", "chromedriver.zip")
        #
        #         with open(zip_path, "wb") as file:
        #             file.write(response.content)
        #
        #         with zipfile.ZipFile(zip_path, "r") as zip_ref:
        #             zip_ref.extractall(os.path.dirname(extract_path))  # Extract to the same directory
        #
        #         os.remove(zip_path)  # Clean up the zip file
        #         os.remove('LICENSE.chromedriver')
        #         # Set execute permission for ChromeDriver (macOS/Linux)
        #         os.chmod(extract_path, os.stat.S_IRWXU | os.stat.S_IRWXG)
        #
        #         print(f"ChromeDriver is located at: {extract_path}")
        #
        #     return extract_path
        # service = Service(get_latest_chromedriver())
        # service = Service(executable_path = "/Users/chrisdixon/MATLAB/Projects/financia/stock_analyzer/chromedriver")
        print("Installing and initializing ChromeDriver.")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service = service, options = chrome_options)
        print("ChromeDriver setup complete.")
        return driver

    def _ensure_driver_active(self):
        """Ensure the WebDriver session is active."""
        if not hasattr(self, 'driver') or self.driver is None:
            print("WebDriver session not active. Reinitializing...")
            self.driver = self._setup_driver()
        else:
            print("WebDriver Active.")

    @retry(stop = stop_after_attempt(3), wait = wait_fixed(2))
    def fetch_stock_details(self, stock_symbol, stock_period, stock_interval):
        """
        Fetches detailed stock metrics from Yahoo Finance and Key Statistics page.
        :param stock_symbol: The stock symbol to fetch data for.
        :return: A dictionary with detailed stock metrics.
        """
        print(f"Fetching stock details for {stock_symbol}.")
        try:
            self._ensure_driver_active()
            # Fetch main quote data
            print("Fetching Stock Quote.")
            quote_data = self._fetch_quote_page(stock_symbol)

            # Fetch key statistics data
            print("Fetching Stock Statistics.")
            statistics_data = self._fetch_statistics_page(stock_symbol, stock_period, stock_interval)

            # Combine and return both datasets
            print("Combining Stock Quotes & Statistics.")
            return {**quote_data, **statistics_data}

        except Exception as e:
            raise Exception(f"Error fetching stock details for {stock_symbol}: {e}")

    def _fetch_quote_page(self, stock_symbol):
        """
        Fetches data from the main quote page using Selenium.
        """
        self._ensure_driver_active()
        url = f"{self.base_quote_url}/{stock_symbol}"
        print(f"Navigating to {url}.")
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.yf-gn3zu3"))
                )

        # Get the page source and parse it with BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Save prettified HTML for debugging
        # file_name = f"{stock_symbol}_quote.html"
        # with open(file_name, "w", encoding="utf-8") as file:
        #     file.write(soup.prettify())
        # print(f"Prettified quote page HTML saved to {file_name}")

        # Dictionary to store extracted stock data
        data = {}

        # Find all relevant list items containing stock details
        metrics = soup.find_all('li', {'class': 'yf-gn3zu3'})

        for metric in metrics:
            try:
                # Extract the label (metric name)
                metric_name_element = metric.find('span', {'class': 'label'})
                if not metric_name_element:
                    continue  # Skip if label is missing
                metric_name = metric_name_element.text.strip()

                # Extract the value
                metric_value_element = metric.find('span', {'class': 'value'})
                if metric_value_element:
                    # Check if value is in <fin-streamer> tag (for dynamic values)
                    fin_streamer = metric_value_element.find('fin-streamer')
                    metric_value = fin_streamer.text.strip() if fin_streamer else metric_value_element.text.strip()
                else:
                    metric_value = "N/A"  # Assign "N/A" if value is missing

                # Store in dictionary
                data[metric_name] = metric_value
                # print(f"Extracted metric '{metric_name}': '{metric_value}'.")
            except AttributeError:
                print("Skipping a metric due to unexpected structure.")
                continue  # Skip elements that do not match the expected structure
        return data

    def _fetch_statistics_page(self, stock_symbol, period, interval):
        """
        Fetches data from the key statistics page using Selenium.
        """
        data = yf.download(
                tickers = stock_symbol,
                period = period,
                interval = interval
                )
        print(f"Extracted a total of {len(data)} statistics entries.")
        return data
        # self._ensure_driver_active()
        # url = self.base_statistics_url.format(stock_symbol)
        # print(f"Navigating to {url}.")
        # self.driver.get(url)
        # WebDriverWait(self.driver, 10).until(
        #         EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        #         )
        #
        # # Get the page source and parse it with BeautifulSoup
        # soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        #
        # # Save prettified HTML for debugging
        # # file_name = f"{stock_symbol}_statistics.html"
        # # with open(file_name, "w", encoding="utf-8") as file:
        # #     file.write(soup.prettify())
        # # print(f"Prettified statistics page HTML saved to {file_name}")
        #
        # # Parse key statistics
        # data = {}
        # tables = soup.find_all('table')  # All tables on the page
        # print(f"Found {len(tables)} tables on the statistics page.")
        #
        # for table in tables:
        #     rows = table.find_all('tr')  # All rows in the table
        #     for row in rows:
        #         try:
        #             metric_name = row.find('td').text.strip()
        #             metric_values = [td.text.strip() for td in row.find_all('td')[1:]]
        #             # Flatten the list into a string (comma-separated values)
        #             data[metric_name] = ", ".join(metric_values)
        #             # print(f"Extracted statistic '{metric_name}': '{data[metric_name]}'.")
        #         except AttributeError:
        #             print("Skipping a row due to unexpected structure.")
        #             continue  # Skip rows that do not match the expected structure
        # print(f"Extracted a total of {len(data)} statistics entries.")
        # return data

    @retry(stop = stop_after_attempt(3), wait = wait_fixed(2))
    def fetch_stock_history(self, stock_symbol, scroll_duration = 5):
        """
        Fetch historical stock data from Yahoo Finance.

        Steps:
        1. Open the Yahoo Finance history page for the given stock.
        2. Wait for the historical data table to load and scroll if necessary.
        3. Parse the table to extract rows containing Date, Open, High, Low, Close, Adj Close, and Volume.
           Tooltip text in the headers (like "Close price adjusted for splits.") is skipped.

        :param stock_symbol: Stock symbol (e.g., 'AAPL').
        :param scroll_duration: Seconds to scroll the page (if required).
        :return: A DataFrame containing historical stock data.
        """
        try:
            self._ensure_driver_active()
            history_url = self.base_history_url.format(stock_symbol)
            print(f"Navigating to history URL: {history_url}")
            self.driver.get(history_url)

            # Wait for the historical table to load
            print("Waiting for the history table to load...")
            WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
                    )
            print("History table is now visible.")

            # Optionally scroll a bit if more data loads dynamically
            start_time = time.time()
            while time.time() - start_time < scroll_duration:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
            print("Finished scrolling the history page.")

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            table = soup.find("table")
            if not table:
                raise Exception("Historical data table not found.")
            print("Historical table successfully extracted.")

            # Extract table headers while skipping tooltip text
            headers = []
            header_row = table.find("thead").find("tr")
            for th in header_row.find_all("th"):
                direct_text = th.find(string = True, recursive = False)
                headers.append(direct_text.strip() if direct_text else th.get_text(strip = True))
            # print(f"Found {len(headers)} headers in the history table.")

            # Extract table rows
            data_rows = []
            tbody = table.find("tbody")
            for tr in tbody.find_all("tr"):
                cells = tr.find_all("td")
                if len(cells) < len(headers):  # Skip incomplete rows (e.g., dividend info)
                    continue
                row_data = {header: cell.get_text(strip = True) for header, cell in zip(headers, cells)}
                # print("Current data row retrieved: ", row_data)
                data_rows.append(row_data)
            print(f"Extracted {len(data_rows)} rows of historical data.")

            print("Creating a DataFrame from the historical data...")
            df = pd.DataFrame(data_rows)

            if not df.empty:
                # Ensure the 'Date' column is in datetime format
                df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')
                # Ensure the 'Close' column is numeric
                df['Close'] = df['Close'].str.replace(',', '').astype(float)
                # Sort by date in ascending order
                df = df.sort_values('Date', ascending = True)
                print("DataFrame columns converted and sorted by date.")

            return df

        except Exception as e:
            print(f"Error fetching stock history for {stock_symbol}: {e}")
            return pd.DataFrame()

    @retry(stop = stop_after_attempt(3), wait = wait_fixed(2))
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
            self._ensure_driver_active()
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
                # print(f"Scroll count {scroll_count}")
                WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "section[data-testid='storyitem'][role='article']"))
                        )

            # Parse the final page
            print("Parsing the page...")
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # --------------------------------------------------
            # Save prettified HTML for debugging
            # file_name = f"{stock_symbol}_news.html"
            # with open(file_name, "w", encoding="utf-8") as file:
            #     file.write(soup.prettify())
            # print(f"Prettified news page HTML saved to {file_name}")
            # --------------------------------------------------

            # Collect all <a> tags with an href within specific <section> elements
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
                        # print(f"Captured link: {full_link}")
                        if len(article_links) >= links_amount:
                            break
                if len(article_links) >= links_amount:
                    break
            print(f"Extracted {len(article_links)} unique article links.")

            print("Starting to visit each link and collect HTML...")
            # # Gather & visit links
            combined_html = []
            visited_links = 0
            skipped_links = 0

            print("Starting to visit each link and collect HTML...")
            for idx, full_link in enumerate(article_links[::3], start = 1):
                print(f"Visiting link: {idx}: {full_link}")
                try:
                    # Visit each link
                    self.driver.get(full_link)
                    WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='storyitem']"))
                            )

                    # Parse the article content
                    article_soup = BeautifulSoup(self.driver.page_source, "html.parser")
                    article_content = article_soup.find(
                            "div",
                            class_ = "article-wrap no-bb",
                            attrs = {"data-testid": "article-content-wrapper"}
                            )
                    if article_content:
                        combined_html.append(article_content.prettify())
                        visited_links += 1
                    else:
                        skipped_links += 1
                        print(f"No article content found on link {idx}, skipping.")
                except Exception as e:
                    print(f"Skipping link {full_link}, error: {e}")
                    skipped_links += 1
                    continue
            print("Completed visiting links.")
            print(f"Visited: {visited_links}, Skipped: {skipped_links}")
            combined_html = "\n".join(combined_html)
            return combined_html

        except Exception as e:
            print(f"Error fetching stock news for {stock_symbol}: {e}")
            raise

    def close(self):
        """Close the WebDriver."""
        print("Closing the driver.")
        self.driver.quit()