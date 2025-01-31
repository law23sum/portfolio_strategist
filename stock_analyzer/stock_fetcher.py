from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


class StockFetcher:
    def __init__(self):
        self.base_quote_url = "https://finance.yahoo.com/quote"
        self.base_statistics_url = "https://finance.yahoo.com/quote/{}/key-statistics"
        self.driver = self._setup_driver()

    def _setup_driver(self):
        """Set up the Selenium WebDriver."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # # Path to your ChromeDriver executable
        # service = Service(executable_path = "/Users/chrisdixon/MATLAB/Projects/financia/stock_analyzer/chromedriver")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service = service, options = chrome_options)

        return driver

    def fetch_stock_details(self, stock_symbol):
        """
        Fetches detailed stock metrics from Yahoo Finance and Key Statistics page.
        :param stock_symbol: The stock symbol to fetch data for.
        :return: A dictionary with detailed stock metrics.
        """
        try:
            # Fetch main quote data
            quote_data = self._fetch_quote_page(stock_symbol)

            # Fetch key statistics data
            statistics_data = self._fetch_statistics_page(stock_symbol)

            # Combine and return both datasets
            return {**quote_data, **statistics_data}

        except Exception as e:
            raise Exception(f"Error fetching stock details for {stock_symbol}: {e}")

    def _fetch_quote_page(self, stock_symbol):
        """
        Fetches data from the main quote page using Selenium.
        """
        url = f"{self.base_quote_url}/{stock_symbol}"
        self.driver.get(url)
        time.sleep(2)  # Wait for the page to load

        # Get the page source and parse it with BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Save prettified HTML for debugging
        # file_name = f"{stock_symbol}_quote.html"
        # with open(file_name, "w", encoding = "utf-8") as file:
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
            except AttributeError:
                continue  # Skip elements that do not match the expected structure

        return data

    def _fetch_statistics_page(self, stock_symbol):
        """
        Fetches data from the key statistics page using Selenium.
        """
        url = self.base_statistics_url.format(stock_symbol)
        self.driver.get(url)
        time.sleep(2)  # Wait for the page to load

        # Get the page source and parse it with BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Save prettified HTML for debugging
        # file_name = f"{stock_symbol}_statistics.html"
        # with open(file_name, "w", encoding = "utf-8") as file:
        #     file.write(soup.prettify())
        # print(f"Prettified statistics page HTML saved to {file_name}")

        # Parse key statistics
        data = {}
        tables = soup.find_all('table')  # All tables on the page

        for table in tables:
            rows = table.find_all('tr')  # All rows in the table
            for row in rows:
                try:
                    metric_name = row.find('td').text.strip()
                    metric_values = [td.text.strip() for td in row.find_all('td')[1:]]

                    # Flatten the list into a string (comma-separated values)
                    data[metric_name] = ", ".join(metric_values)
                except AttributeError:
                    continue  # Skip rows that do not match the expected structure

        return data

    def close(self):
        """Close the WebDriver."""
        self.driver.quit()