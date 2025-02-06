# stock_definitions.py

RATIO_DEFINITIONS = {
    'Earnings Per Share'      : {
        'Term'      : 'EPS',
        'Definition': 'The portion of a company\'s profit allocated to each outstanding share of common stock.',
        'Formula'   : 'Net Income / Shares Outstanding'
        },
    'P/E Ratio'               : {
        'Term'      : 'Price-to-Earnings Ratio',
        'Definition': 'Measures the current share price relative to its per-share earnings.',
        'Formula'   : 'Market Value per Share / Earnings per Share'
        },
    'Return on Equity'        : {
        'Term'      : 'ROE',
        'Definition': 'Measures the profitability of a company in relation to shareholders\' equity.',
        'Formula'   : 'Net Income / Shareholders\' Equity'
        },
    'Free Cash Flow Yield'    : {
        'Term'      : 'FCF Yield',
        'Definition': 'Measures the free cash flow relative to the market value of the company.',
        'Formula'   : 'Free Cash Flow / Market Capitalization'
        },
    'Operating Margin'        : {
        'Term'      : 'Operating Profit Margin',
        'Definition': 'Measures the proportion of revenue left after paying for variable costs of production.',
        'Formula'   : 'Operating Income / Revenue'
        },
    'Net Profit Margin'       : {
        'Term'      : 'Net Margin',
        'Definition': 'Measures the percentage of revenue that remains as profit after all expenses.',
        'Formula'   : 'Net Income / Revenue'
        },
    'EV/EBITDA'               : {
        'Term'      : 'Enterprise Value to EBITDA',
        'Definition': 'Measures the value of a company, including debt, relative to its earnings before interest, taxes, depreciation, '
                      'and amortization.',
        'Formula'   : 'Enterprise Value / EBITDA'
        },
    'Return on Assets'        : {
        'Term'      : 'ROA',
        'Definition': 'Measures how efficiently a company uses its assets to generate profit.',
        'Formula'   : 'Net Income / Total Assets'
        },
    'Gross Margin'            : {
        'Term'      : 'Gross Profit Margin',
        'Definition': 'Measures the percentage of revenue that exceeds the cost of goods sold.',
        'Formula'   : 'Gross Profit / Revenue'
        },
    'Debt to Equity'          : {
        'Term'      : 'D/E Ratio',
        'Definition': 'Measures the relative proportion of shareholders\' equity and debt used to finance a company\'s assets.',
        'Formula'   : 'Total Debt / Total Equity'
        },
    'Price-to-Sales'          : {
        'Term'      : 'P/S Ratio',
        'Definition': 'Measures the price of a stock relative to its revenue per share.',
        'Formula'   : 'Market Capitalization / Revenue'
        },
    'Price-to-Book'           : {
        'Term'      : 'P/B Ratio',
        'Definition': 'Measures the market value of a company relative to its book value.',
        'Formula'   : 'Market Price per Share / Book Value per Share'
        },
    'Revenue Per Share'       : {
        'Term'      : 'RPS',
        'Definition': 'Measures the total revenue generated per outstanding share.',
        'Formula'   : 'Revenue / Shares Outstanding'
        },
    'Book Value Per Share'    : {
        'Term'      : 'BVPS',
        'Definition': 'Measures the equity available to common shareholders per share.',
        'Formula'   : 'Total Equity / Shares Outstanding'
        },
    'Free Cash Flow Per Share': {
        'Term'      : 'FCFPS',
        'Definition': 'Measures the free cash flow available per outstanding share.',
        'Formula'   : 'Free Cash Flow / Shares Outstanding'
        },
    'Cash Flow to Debt'       : {
        'Term'      : 'CF/Debt',
        'Definition': 'Measures the ability of a company to cover its debt with its operating cash flow.',
        'Formula'   : 'Operating Cash Flow / Total Debt'
        },
    'Debt to Assets'          : {
        'Term'      : 'D/A Ratio',
        'Definition': 'Measures the proportion of a company\'s assets that are financed by debt.',
        'Formula'   : 'Total Debt / Total Assets'
        },
    'Current Ratio'           : {
        'Term'      : 'Current Ratio',
        'Definition': 'Measures a company\'s ability to pay short-term obligations with its current assets.',
        'Formula'   : 'Current Assets / Current Liabilities'
        },
    'Dividend Yield'          : {
        'Term'      : 'Dividend Yield',
        'Definition': 'Measures the annual dividend payment relative to the stock price.',
        'Formula'   : 'Annual Dividend per Share / Price per Share'
        }
    }

MACRO_ECONOMIC_INDICATORS = {
    'Interest Rate Tickers': {
        'US10Y'       : {
            'Definition' : '10-Year U.S. Treasury Yield',
            'Purpose'    : 'Serves as a benchmark for long-term interest rates and investor confidence.',
            'When to Use': 'To assess bond market expectations, inflation trends, and economic growth outlook.'
            },
        'US02Y'       : {
            'Definition' : '2-Year U.S. Treasury Yield',
            'Purpose'    : 'Reflects short-term interest rate trends and expectations of Federal Reserve policy.',
            'When to Use': 'To gauge immediate shifts in economic sentiment, monetary policy, and rate hikes/cuts.'
            },
        'US30Y'       : {
            'Definition' : '30-Year U.S. Treasury Yield',
            'Purpose'    : 'Indicates long-term borrowing costs and inflation expectations.',
            'When to Use': 'To evaluate investor sentiment regarding long-term economic stability and fiscal policy.'
            },
        'US05Y'       : {
            'Definition' : '5-Year U.S. Treasury Yield',
            'Purpose'    : 'Represents medium-term economic expectations.',
            'When to Use': 'To assess economic cycles and forecast mid-term inflation trends.'
            },
        'FFR'         : {
            'Definition' : 'Federal Funds Rate',
            'Purpose'    : 'The interest rate at which banks lend excess reserves overnight.',
            'When to Use': 'To analyze central bank policy, liquidity conditions, and borrowing costs in the economy.'
            },
        'PRIME'       : {
            'Definition' : 'U.S. Prime Rate',
            'Purpose'    : 'Determines the interest rate for creditworthy borrowers.',
            'When to Use': 'To evaluate lending conditions and the impact on businesses and consumers.'
            },
        'SOFR'        : {
            'Definition' : 'Secured Overnight Financing Rate',
            'Purpose'    : 'A replacement for LIBOR, reflecting the cost of borrowing cash overnight.',
            'When to Use': 'To track interbank lending rates and overall market liquidity.'
            },
        'LIBOR'       : {
            'Definition' : 'London Interbank Offered Rate (phasing out)',
            'Purpose'    : 'Historically used for interbank lending and setting adjustable interest rates.',
            'When to Use': 'Used before transition to SOFR; still relevant for legacy financial contracts.'
            },
        'MORTGAGE30US': {
            'Definition' : '30-Year Fixed Mortgage Rate',
            'Purpose'    : 'Determines the cost of long-term home loans in the U.S.',
            'When to Use': 'To evaluate housing affordability and consumer borrowing power.'
            },
        'MORTGAGE15US': {
            'Definition' : '15-Year Fixed Mortgage Rate',
            'Purpose'    : 'Indicates the interest rate for shorter-term home loans.',
            'When to Use': 'To compare mortgage cost trends and assess real estate market health.'
            }
        },
    'Volatility Tickers'   : {
        'VIX'   : {
            'Definition' : 'CBOE Volatility Index (Fear Index)',
            'Purpose'    : 'Measures market expectations for future volatility.',
            'When to Use': 'To assess investor sentiment and potential market turbulence.'
            },
        'VVIX'  : {
            'Definition' : 'Volatility of VIX',
            'Purpose'    : 'Tracks expected volatility of VIX itself.',
            'When to Use': 'To predict extreme market uncertainty or major trend reversals.'
            },
        'VXN'   : {
            'Definition' : 'Nasdaq 100 Volatility Index',
            'Purpose'    : 'Measures expected volatility in technology-heavy Nasdaq stocks.',
            'When to Use': 'To analyze risk in high-growth, speculative investments.'
            },
        'RVX'   : {
            'Definition' : 'Russell 2000 Volatility Index',
            'Purpose'    : 'Represents volatility expectations for small-cap stocks.',
            'When to Use': 'To assess risk levels in smaller, high-growth companies.'
            },
        'VXD'   : {
            'Definition' : 'Dow Jones Industrial Average Volatility Index',
            'Purpose'    : 'Measures expected volatility for Dow 30 blue-chip stocks.',
            'When to Use': 'To gauge investor confidence in large, stable companies.'
            },
        'VSTOXX': {
            'Definition' : 'Euro Stoxx 50 Volatility Index',
            'Purpose'    : 'Tracks volatility expectations in European stock markets.',
            'When to Use': 'To evaluate risk in European financial markets and economic uncertainty.'
            }
        },
    'Market Tickers'       : {
        'SPX'  : {
            'Definition' : 'S&P 500 Index',
            'Purpose'    : 'Represents the performance of 500 large-cap U.S. companies.',
            'When to Use': 'To measure the overall health and trends in the U.S. stock market.'
            },
        'DJIA' : {
            'Definition' : 'Dow Jones Industrial Average',
            'Purpose'    : 'Tracks 30 major U.S. industrial companies.',
            'When to Use': 'To assess stability in established, blue-chip stocks.'
            },
        'IXIC' : {
            'Definition' : 'Nasdaq Composite Index',
            'Purpose'    : 'Focuses on technology and growth stocks.',
            'When to Use': 'To analyze the performance of tech-sector investments.'
            },
        'RUT'  : {
            'Definition' : 'Russell 2000 Index',
            'Purpose'    : 'Represents small-cap U.S. stocks.',
            'When to Use': 'To assess trends in emerging and growth companies.'
            },
        'W5000': {
            'Definition' : 'Wilshire 5000 Total Market Index',
            'Purpose'    : 'Tracks all U.S. publicly traded stocks.',
            'When to Use': 'To evaluate the broadest measure of U.S. equity markets.'
            },
        'MSCIW': {
            'Definition' : 'MSCI World Index',
            'Purpose'    : 'Measures global developed market equities.',
            'When to Use': 'To analyze international stock market trends.'
            },
        'FTSE' : {
            'Definition' : 'FTSE 100 Index (UK)',
            'Purpose'    : 'Represents the 100 largest companies on the London Stock Exchange.',
            'When to Use': 'To gauge economic trends in the United Kingdom.'
            },
        'N225' : {
            'Definition' : 'Nikkei 225 Index (Japan)',
            'Purpose'    : 'Measures stock market performance in Japan.',
            'When to Use': 'To evaluate economic trends in the Japanese market.'
            },
        'SSE'  : {
            'Definition' : 'Shanghai Composite Index (China)',
            'Purpose'    : 'Tracks all stocks traded on the Shanghai Stock Exchange.',
            'When to Use': 'To monitor economic and financial conditions in China.'
            },
        'DAX'  : {
            'Definition' : 'German Stock Market Index',
            'Purpose'    : 'Measures the performance of 40 major German companies.',
            'When to Use': 'To assess the economic health of Germany and the Eurozone.'
            }
        }
    }