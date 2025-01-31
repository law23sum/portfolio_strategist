import pandas as pd
import numpy as np


class StockAnalyzer:
    np.set_printoptions(suppress = True)

    def calculate_ratios(self, metrics):
        """Calculates financial ratios based on available stock metrics."""
        ratios = {}

        # Predefined ratios that can be directly fetched from metrics
        predefined_ratios = {
            'Earnings Per Share'  : 'Diluted EPS  (ttm)',
            'P/E Ratio'           : 'PE Ratio (TTM)',
            'Dividend Yield'      : 'Forward Annual Dividend Yield 4',
            'Debt to Equity'      : 'Total Debt/Equity  (mrq)',
            'Current Ratio'       : 'Current Ratio  (mrq)',
            'Operating Margin'    : 'Operating Margin  (ttm)',
            'Net Profit Margin'   : 'Profit Margin',
            'Return on Assets'    : 'Return on Assets  (ttm)',
            'Return on Equity'    : 'Return on Equity  (ttm)',
            'Price-to-Sales'      : 'Price/Sales',
            'Price-to-Book'       : 'Price/Book',
            'EV/EBITDA'           : 'Enterprise Value/EBITDA',
            'Gross Profit'        : 'Gross Profit  (ttm)',
            'Revenue'             : 'Revenue  (ttm)',
            'Revenue Per Share'   : 'Revenue Per Share  (ttm)',
            'Book Value Per Share': 'Book Value Per Share  (mrq)',
            }

        # Fetch predefined ratios directly from metrics if available
        for ratio_name, metric_key in predefined_ratios.items():
            if metric_key in metrics:
                ratios[ratio_name] = self._to_float(metrics[metric_key])
            else:
                ratios[ratio_name] = None

        # Extract metrics for calculated ratios
        MarketCap = self._to_float(metrics.get('Market Cap', "0").split(",")[0])
        Revenue = self._to_float(metrics.get('Revenue  (ttm)', "0"))
        NetIncome = self._to_float(metrics.get('Net Income Avi to Common  (ttm)', "0"))
        TotalDebt = self._to_float(metrics.get('Total Debt  (mrq)', "0"))
        TotalCash = self._to_float(metrics.get('Total Cash  (mrq)', "0"))
        GrossProfit = self._to_float(metrics.get('Gross Profit  (ttm)', "0"))
        OperatingCashFlow = self._to_float(metrics.get('Operating Cash Flow  (ttm)', "0"))
        EBITDA = self._to_float(metrics.get('EBITDA', "0"))
        TotalAssets = self._to_float(metrics.get('Total Assets  (mrq)', "0"))
        CurrentAssets = self._to_float(metrics.get('Current Assets  (mrq)', "0"))
        CurrentLiabilities = self._to_float(metrics.get('Current Liabilities  (mrq)', "0"))
        LeveredFreeCashFlow = self._to_float(metrics.get('Levered Free Cash Flow  (ttm)', "0"))
        SharesOutstanding = self._to_float(metrics.get('Shares Outstanding 5', "0"))
        OperatingIncome = self._to_float(metrics.get('Operating Income  (ttm)', "0"))

        # Derived variables
        TotalEquity = TotalAssets - TotalDebt if TotalAssets and TotalDebt else None

        # Calculate ratios only if not already fetched from metrics
        if 'Revenue Per Share' not in ratios:
            ratios['Revenue Per Share'] = Revenue / SharesOutstanding if Revenue and SharesOutstanding else None
        if 'Gross Margin' not in ratios:
            ratios['Gross Margin'] = GrossProfit / Revenue if Revenue else None
        if 'Operating Margin' not in ratios:
            ratios['Operating Margin'] = OperatingIncome / Revenue if Revenue and OperatingIncome else None
        if 'Net Profit Margin' not in ratios:
            ratios['Net Profit Margin'] = NetIncome / Revenue if Revenue and NetIncome else None
        if 'Current Ratio' not in ratios:
            ratios['Current Ratio'] = CurrentAssets / CurrentLiabilities if CurrentAssets and CurrentLiabilities else None
        if 'Debt to Assets' not in ratios:
            ratios['Debt to Assets'] = TotalDebt / TotalAssets if TotalDebt and TotalAssets else None
        if 'Book Value Per Share' not in ratios:
            ratios['Book Value Per Share'] = TotalEquity / SharesOutstanding if TotalEquity and SharesOutstanding else None
        if 'Free Cash Flow Per Share' not in ratios:
            ratios['Free Cash Flow Per Share'] = LeveredFreeCashFlow / SharesOutstanding if LeveredFreeCashFlow and SharesOutstanding else None
        if 'Cash Flow to Debt' not in ratios:
            ratios['Cash Flow to Debt'] = OperatingCashFlow / TotalDebt if OperatingCashFlow and TotalDebt else None
        if 'Price-to-Sales' not in ratios:
            ratios['Price-to-Sales'] = MarketCap / Revenue if MarketCap and Revenue else None
        if 'Price-to-Book' not in ratios:
            ratios['Price-to-Book'] = MarketCap / TotalEquity if MarketCap and TotalEquity else None
        if 'Return on Assets' not in ratios:
            ratios['Return on Assets'] = NetIncome / TotalAssets if NetIncome and TotalAssets else None
        if 'Return on Equity' not in ratios:
            ratios['Return on Equity'] = NetIncome / TotalEquity if NetIncome and TotalEquity else None
        if 'EV/EBITDA' not in ratios:
            ratios['EV/EBITDA'] = (MarketCap + TotalDebt - TotalCash) / EBITDA if MarketCap and TotalDebt and TotalCash and EBITDA else None
        if 'Free Cash Flow Yield' not in ratios:
            ratios['Free Cash Flow Yield'] = LeveredFreeCashFlow / MarketCap if LeveredFreeCashFlow and MarketCap else None
        return ratios

    # Helper to float-convert typical Yahoo-style metrics like "123.45B" or "0.03%" etc.
    def _to_float(self, val):
        import re

        if not val or val.strip().lower() in ("", "none", "nan"):
            return None

        # If comma-separated (like "27.36, 34.33, 36.58,..."), take the first chunk
        if "," in val:
            val = val.split(",")[0].strip()

        # Remove anything in parentheses, e.g. "10.01B (mrq)" or "0.03%"
        val = re.sub(r"\(.*?\)", "", val).strip()

        # Handle trailing percent sign
        if val.endswith("%"):
            try:
                float_val = float(val[:-1]) / 100.0
                return float_val
            except ValueError:
                return None

        # Handle letter multipliers (K, M, B, T)
        multipliers = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}
        last_char = val[-1].upper()
        if last_char in multipliers:
            try:
                float_val = float(val[:-1]) * multipliers[last_char]
                return float_val
            except ValueError:
                return None

        try:
            float_val = float(val)
            # Format to 6 decimal places, ensuring no scientific notation
            formatted = f"{float_val:.6f}"
            return float(formatted)  # Return as float
        except ValueError:
            return None

    def evaluate_performance(self, ratios):
        """Evaluates performance for each ratio."""
        performance = []
        for name, value in ratios.items():
            if value is None:  # Handle missing or invalid values
                performance.append('N/A')
                continue

            if name == 'P/E Ratio':
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [5.000000000, 10.000000000, 15.000000000, 25.000000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Price-to-Sales':
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [0.750000000, 1.500000000, 2.250000000, 3.000000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Price-to-Book':
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [0.800000000, 2.200000000, 3.600000000, 5.000000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Debt to Equity':
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [0.500000000, 1.000000000, 1.500000000, 2.000000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Dividend Yield':
                # Higher Dividend Yield is better
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [0.020000000, 0.033333333, 0.046666666, 0.060000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Gross Margin':
                # Higher Gross Margin is better
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [0.300000000, 0.500000000, 0.700000000, 0.900000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Net Profit Margin':
                # Higher Net Profit Margin is better
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [0.050000000, 0.100000000, 0.150000000, 0.200000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Operating Margin':
                # Higher Operating Margin is better
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [0.050000000, 0.116666666, 0.183333333, 0.250000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Return on Assets':
                # Higher Return on Assets is better
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [0.025000000, 0.100000000, 0.175000000, 0.250000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Return on Equity':
                # Higher Return on Equity is better
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [0.025000000, 0.100000000, 0.175000000, 0.250000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Current Ratio':
                # Higher Current Ratio is better
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [0.500000000, 1.333333333, 2.166666666, 3.000000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Free Cash Flow Yield':
                # Higher Free Cash Flow Yield is better
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [0.030000000, 0.060000000, 0.090000000, 0.120000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Revenue Per Share':
                # Higher Revenue Per Share is better
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [10.000000000, 40.000000000, 70.000000000, 100.000000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Free Cash Flow Per Share':
                # Higher Free Cash Flow Per Share is better
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [0.000000000, 1.000000000, 2.000000000, 3.000000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'EV/EBITDA':
                # Lower EV/EBITDA is better
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [10.000000000, 15.000000000, 20.000000000, 25.000000000],
                                ['Perfect', 'Excellent', 'Mediocre', 'Poor']
                                )
                        )
            elif name == 'Book Value Per Share':
                # Higher Book Value Per Share is better
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [3.000000000, 2.333333333, 1.666666667, 1.000000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Cash Flow to Debt':
                # Higher Cash Flow to Debt is better
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [0.500000000, 1.000000000, 1.500000000, 2.000000000],
                                ['Poor', 'Mediocre', 'Excellent', 'Perfect']
                                )
                        )
            elif name == 'Debt to Assets':
                # Lower Debt to Assets is better
                performance.append(
                        self._evaluate_range_with_accuracy(
                                value,
                                [0.200000000, 0.400000000, 0.600000000, 0.800000000],
                                ['Perfect', 'Excellent', 'Mediocre', 'Poor']
                                )
                        )
            else:
                performance.append('N/A')
        return performance

    def _evaluate_range_with_accuracy(self, value, thresholds, ratings):
        """
        Categorizes a numerical value into a performance rating based on defined thresholds.

        Assumes higher values are better for metrics where thresholds and ratings are ordered accordingly.
        For metrics where lower values are better, ensure that thresholds are in ascending order
        and ratings are ordered from 'Perfect' to 'Poor'.

        :param value: The numerical value to evaluate.
        :param thresholds: A list of numerical thresholds in ascending order.
        :param ratings: A list of performance labels corresponding to the thresholds.
        :return: The corresponding performance rating or 'N/A' if input is invalid.
        """
        try:
            value = round(float(value), 9)
        except (ValueError, TypeError):
            return 'N/A'

        for i, threshold in enumerate(thresholds):
            if value <= threshold:
                return ratings[i]
        return ratings[-1]

    def build_ratios_table(self, ratios, performance):
        """Builds a Pandas DataFrame for the ratios, their evaluations, and definitions."""
        # Define the desired order of the ratios
        desired_order = [
            'Earnings Per Share',
            'P/E Ratio',
            'Return on Equity',
            'Free Cash Flow Yield',
            'Operating Margin',
            'Net Profit Margin',
            'EV/EBITDA',
            'Return on Assets',
            'Gross Margin',
            'Debt to Equity',
            'Price-to-Sales',
            'Price-to-Book',
            'Revenue Per Share',
            'Book Value Per Share',
            'Free Cash Flow Per Share',
            'Cash Flow to Debt',
            'Debt to Assets',
            'Current Ratio',
            'Dividend Yield',
            ]

        # Reorder the ratios, values, and performance evaluations
        ratio_names = [name for name in desired_order if name in ratios]
        ratio_values = [ratios[name] for name in desired_order if name in ratios]
        ratio_performance = [performance[list(ratios.keys()).index(name)] for name in desired_order if name in ratios]

        return pd.DataFrame(
                {
                    'Ratio Name' : ratio_names,
                    'Ratio Value': ratio_values,
                    'Performance': ratio_performance,
                    })