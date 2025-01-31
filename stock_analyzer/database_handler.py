import sqlite3

class DatabaseHandler:
    def __init__(self, db_name="stocks.db"):
        self.db_name = db_name
        self._initialize_db()

    def _initialize_db(self):
        """Create or update the database schema."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_data (
                symbol TEXT PRIMARY KEY,
                previous_close REAL,
                open REAL,
                bid TEXT,
                ask TEXT,
                day_range TEXT,
                week_range TEXT,
                volume TEXT,
                avg_volume TEXT,
                market_cap TEXT,  -- Store as comma-separated string
                beta REAL,
                pe_ratio REAL,
                eps REAL,
                earnings_date TEXT,
                forward_dividend_yield TEXT,
                ex_dividend_date TEXT,
                target_est REAL,
                revenue_ttm REAL,
                revenue_per_share REAL,
                quarterly_revenue_growth TEXT,
                gross_profit REAL,
                ebitda REAL,
                net_income REAL,
                diluted_eps REAL,
                total_cash REAL,
                total_cash_per_share REAL,
                total_debt REAL,
                total_debt_to_equity TEXT,
                book_value_per_share REAL,
                operating_cash_flow REAL,
                levered_free_cash_flow REAL,
                current_ratio REAL,
                profit_margin REAL,
                operating_margin REAL,
                return_on_assets REAL,
                return_on_equity REAL,
                enterprise_value TEXT,  -- Store as comma-separated string
                trailing_pe TEXT,       -- Store as comma-separated string
                forward_pe TEXT,        -- Store as comma-separated string
                peg_ratio TEXT,         -- Store as comma-separated string
                price_to_sales TEXT,    -- Store as comma-separated string
                price_to_book TEXT,     -- Store as comma-separated string
                ev_to_revenue TEXT,     -- Store as comma-separated string
                ev_to_ebitda TEXT,      -- Store as comma-separated string
                fiscal_year_ends TEXT,
                most_recent_quarter TEXT,
                shares_outstanding REAL,
                float_shares REAL,
                held_by_insiders REAL,
                held_by_institutions REAL,
                shares_short TEXT,
                short_ratio TEXT,
                short_percent_of_float TEXT,
                short_percent_of_shares_outstanding TEXT,
                dividend_rate REAL,
                dividend_yield REAL,
                trailing_annual_dividend_rate REAL,
                trailing_annual_dividend_yield REAL,
                five_year_avg_dividend_yield REAL,
                payout_ratio REAL,
                dividend_date TEXT,
                last_split_factor TEXT,
                last_split_date TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_stock_data(self, stock_symbol, stock_data):
        """Save stock data into the database while ensuring correct column-value mapping."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            # Get all column names from the database dynamically
            cursor.execute("PRAGMA table_info(stock_data);")
            columns = [row[1] for row in cursor.fetchall()]  # Extract column names

            # Filter stock_data to include only fields that exist in the database schema
            filtered_data = {col: stock_data.get(col, None) for col in columns}

            # Convert arrays to comma-separated strings
            for key in filtered_data:
                if isinstance(filtered_data[key], list):
                    filtered_data[key] = ", ".join(map(str, filtered_data[key]))

            # Ensure values align with database columns
            values = [filtered_data[col] for col in columns]

            # Construct dynamic SQL query
            placeholders = ", ".join(["?"] * len(columns))
            query = f"""
                INSERT OR REPLACE INTO stock_data ({', '.join(columns)}) VALUES ({placeholders})
            """

            # Execute the query and commit changes
            cursor.execute(query, values)
            conn.commit()
            print(f"✅ Successfully saved stock data for {stock_symbol}")
        except sqlite3.Error as e:
            print(f"❌ Failed to save stock data for {stock_symbol}: {e}")
        finally:
            if conn:
                conn.close()

    def fetch_stock_data(self, stock_symbol):
        """Fetch stock data for a specific symbol."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, previous_close, open, bid, ask, day_range, week_range,
                   volume, avg_volume, market_cap, beta, pe_ratio, eps,
                   earnings_date, forward_dividend_yield, ex_dividend_date, target_est,
                   revenue_ttm, revenue_per_share, quarterly_revenue_growth, gross_profit,
                   ebitda, net_income, diluted_eps, total_cash, total_cash_per_share,
                   total_debt, total_debt_to_equity, book_value_per_share,
                   operating_cash_flow, levered_free_cash_flow, current_ratio, profit_margin,
                   operating_margin, return_on_assets, return_on_equity, enterprise_value,
                   trailing_pe, forward_pe, peg_ratio, price_to_sales, price_to_book,
                   ev_to_revenue, ev_to_ebitda, fiscal_year_ends, most_recent_quarter,
                   shares_outstanding, float_shares, held_by_insiders, held_by_institutions,
                   shares_short, short_ratio, short_percent_of_float, short_percent_of_shares_outstanding,
                   dividend_rate, dividend_yield, trailing_annual_dividend_rate,
                   trailing_annual_dividend_yield, five_year_avg_dividend_yield,
                   payout_ratio, dividend_date, last_split_factor, last_split_date
            FROM stock_data WHERE symbol = ?
        """, (stock_symbol,))
        result = cursor.fetchone()
        conn.close()

        if result:
            # Convert comma-separated strings back to arrays where applicable
            data = {
                "symbol": result[0],
                "Previous Close": result[1],
                "Open": result[2],
                "Bid": result[3],
                "Ask": result[4],
                "Day's Range": result[5],
                "52 Week Range": result[6],
                "Volume": result[7],
                "Avg. Volume": result[8],
                "Market Cap": result[9].split(", ") if result[9] else [],  # Convert back to list
                "Beta": result[10],
                "PE Ratio (TTM)": result[11],
                "EPS (TTM)": result[12],
                "Earnings Date": result[13],
                "Forward Dividend & Yield": result[14],
                "Ex-Dividend Date": result[15],
                "1y Target Est": result[16],
                "Revenue (TTM)": result[17],
                "Revenue Per Share (TTM)": result[18],
                "Quarterly Revenue Growth (YoY)": result[19],
                "Gross Profit (TTM)": result[20],
                "EBITDA": result[21],
                "Net Income (TTM)": result[22],
                "Diluted EPS (TTM)": result[23],
                "Total Cash (MRQ)": result[24],
                "Total Cash Per Share (MRQ)": result[25],
                "Total Debt (MRQ)": result[26],
                "Total Debt/Equity (MRQ)": result[27],
                "Book Value Per Share (MRQ)": result[28],
                "Operating Cash Flow (TTM)": result[29],
                "Levered Free Cash Flow (TTM)": result[30],
                "Current Ratio": result[31],
                "Profit Margin": result[32],
                "Operating Margin (TTM)": result[33],
                "Return on Assets (TTM)": result[34],
                "Return on Equity (TTM)": result[35],
                "Enterprise Value": result[36].split(", ") if result[36] else [],  # Convert back to list
                "Trailing P/E": result[37].split(", ") if result[37] else [],  # Convert back to list
                "Forward P/E": result[38].split(", ") if result[38] else [],  # Convert back to list
                "PEG Ratio (5yr expected)": result[39].split(", ") if result[39] else [],  # Convert back to list
                "Price/Sales": result[40].split(", ") if result[40] else [],  # Convert back to list
                "Price/Book": result[41].split(", ") if result[41] else [],  # Convert back to list
                "Enterprise Value/Revenue": result[42].split(", ") if result[42] else [],  # Convert back to list
                "Enterprise Value/EBITDA": result[43].split(", ") if result[43] else [],  # Convert back to list
                "Fiscal Year Ends": result[44],
                "Most Recent Quarter (MRQ)": result[45],
                "Shares Outstanding": result[46],
                "Float": result[47],
                "Held by Insiders": result[48],
                "Held by Institutions": result[49],
                "Shares Short": result[50],
                "Short Ratio": result[51],
                "Short % of Float": result[52],
                "Short % of Shares Outstanding": result[53],
                "Forward Annual Dividend Rate": result[54],
                "Forward Annual Dividend Yield": result[55],
                "Trailing Annual Dividend Rate": result[56],
                "Trailing Annual Dividend Yield": result[57],
                "5 Year Average Dividend Yield": result[58],
                "Payout Ratio": result[59],
                "Dividend Date": result[60],
                "Last Split Factor": result[61],
                "Last Split Date": result[62]
            }
            return data
        else:
            return None  # Explicitly return None if no data is found