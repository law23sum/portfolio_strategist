% MATLAB Script: Enhanced Stock Ratio Calculator with Ordered Importance
% Clear workspace
clear; clc;

% Prompt user for the CSV file
fileName = '/Users/chrisdixon/Desktop/Everest_Stocks.csv';

% Read the CSV file into a table
stockData = readtable(fileName);

% Extract variables from the dataset
MarketCap = stockData.Value(strcmp(stockData.Metric, 'Market Cap'));
Revenue = stockData.Value(strcmp(stockData.Metric, 'Revenue (ttm)'));
NetIncome = stockData.Value(strcmp(stockData.Metric, 'Net Income (ttm)'));
TotalDebt = stockData.Value(strcmp(stockData.Metric, 'Total Debt (mrq)'));
TotalCash = stockData.Value(strcmp(stockData.Metric, 'Total Cash (mrq)'));
GrossProfit = stockData.Value(strcmp(stockData.Metric, 'Gross Profit (ttm)'));
EPS = stockData.Value(strcmp(stockData.Metric, 'EPS (TTM)'));
PE_Ratio = stockData.Value(strcmp(stockData.Metric, 'PE Ratio (TTM)'));
DividendYield = stockData.Value(strcmp(stockData.Metric, 'Dividend Yield'));
OperatingCashFlow = stockData.Value(strcmp(stockData.Metric, 'Operating Cash Flow'));
DebtToEquity = stockData.Value(strcmp(stockData.Metric, 'Debt-to-Equity Ratio'));
SharesOutstanding = stockData.Value(strcmp(stockData.Metric, 'Shares Outstanding'));
TotalCurrentAssets = stockData.Value(strcmp(stockData.Metric, 'Total Current Assets'));
TotalCurrentLiabilities = stockData.Value(strcmp(stockData.Metric, 'Total Current Liabilities'));

% Check for missing variables and fill them if necessary
if isempty(DividendYield)
    DividendYield = 0; % Placeholder if not available
end

% Calculate derived values and ratios
OperatingMargin = OperatingCashFlow / Revenue; % Operating Margin
EV = MarketCap + TotalDebt - TotalCash; % Enterprise Value (EV)
EV_EBITDA = EV / OperatingCashFlow; % EV/EBITDA
FreeCashFlowPerShare = OperatingCashFlow / SharesOutstanding;
DebtToAssets = TotalDebt / (MarketCap + TotalDebt);
BookValuePerShare = (MarketCap - TotalDebt) / SharesOutstanding;
CashFlowToDebt = OperatingCashFlow / TotalDebt;
CurrentRatio = TotalCurrentAssets / TotalCurrentLiabilities;
RevenuePerShare = Revenue / SharesOutstanding;
PriceToSales = MarketCap / Revenue; % Price-to-Sales Ratio
PriceToBook = MarketCap / (MarketCap - TotalDebt); % Price-to-Book Ratio
GrossMargin = GrossProfit / Revenue; % Gross Margin
NetProfitMargin = NetIncome / Revenue; % Net Profit Margin
ReturnOnAssets = NetIncome / (MarketCap + TotalDebt - TotalCash); % Return on Assets (ROA)
ReturnOnEquity = NetIncome / (MarketCap - TotalDebt); % Return on Equity (ROE)
PriceToFreeCashFlow = MarketCap / OperatingCashFlow; % Price to Free Cash Flow

% Create the ratios table
RatioNames = {
    'Return on Equity'; 'Net Profit Margin'; 'Operating Margin'; 'Gross Margin';
    'EV/EBITDA'; 'Price-to-Sales'; 'Price-to-Book'; 'Free Cash Flow Yield';
    'Free Cash Flow Per Share'; 'Cash Flow to Debt'; 'Debt-to-Equity'; 'Debt-to-Assets'; 'Revenue Per Share'; 'Book Value Per Share';
    'Current Ratio'; 'P/E Ratio';
    'Return on Assets'; 'Dividend Yield'; 'Earnings Per Share'
};

RatioValues = [
    ReturnOnEquity; NetProfitMargin; OperatingMargin; GrossMargin;
    EV_EBITDA; PriceToSales; PriceToBook; FreeCashFlowPerShare;
    FreeCashFlowPerShare; CashFlowToDebt; DebtToEquity; DebtToAssets; RevenuePerShare; BookValuePerShare;
    CurrentRatio; PE_Ratio;
    ReturnOnAssets; DividendYield; EPS
];

% Replace NaN and Inf values with 0
validIndices = ~isnan(RatioValues) & ~isinf(RatioValues);
RatioNames = RatioNames(validIndices);
RatioValues = RatioValues(validIndices);
RatioValues(isnan(RatioValues) | isinf(RatioValues)) = 0;

% Initialize performance evaluation
Performance = cell(size(RatioNames));

for i = 1:length(RatioNames)
    if strcmp(RatioNames{i}, 'P/E Ratio')
        if RatioValues(i) <= 10
            Performance{i} = 'Perfect';
        elseif RatioValues(i) <= 15
            Performance{i} = 'Excellent';
        elseif RatioValues(i) <= 25
            Performance{i} = 'Mediocre';
        else
            Performance{i} = 'Poor';
        end
    elseif strcmp(RatioNames{i}, 'Price-to-Sales')
        if RatioValues(i) <= 0.5
            Performance{i} = 'Perfect';
        elseif RatioValues(i) <= 1
            Performance{i} = 'Excellent';
        elseif RatioValues(i) <= 3
            Performance{i} = 'Mediocre';
        else
            Performance{i} = 'Poor';
        end
    elseif strcmp(RatioNames{i}, 'Price-to-Book')
        if RatioValues(i) <= 0.5
            Performance{i} = 'Perfect';
        elseif RatioValues(i) <= 1
            Performance{i} = 'Excellent';
        elseif RatioValues(i) <= 3
            Performance{i} = 'Mediocre';
        else
            Performance{i} = 'Poor';
        end
    elseif strcmp(RatioNames{i}, 'Debt-to-Equity')
        if RatioValues(i) <= 0.3
            Performance{i} = 'Perfect';
        elseif RatioValues(i) <= 0.5
            Performance{i} = 'Excellent';
        elseif RatioValues(i) <= 1
            Performance{i} = 'Mediocre';
        else
            Performance{i} = 'Poor';
        end
    elseif strcmp(RatioNames{i}, 'Dividend Yield')
        if RatioValues(i) >= 0.1
            Performance{i} = 'Perfect';
        elseif RatioValues(i) >= 0.05
            Performance{i} = 'Excellent';
        elseif RatioValues(i) >= 0.02
            Performance{i} = 'Mediocre';
        else
            Performance{i} = 'Poor';
        end
    elseif strcmp(RatioNames{i}, 'Gross Margin') || strcmp(RatioNames{i}, 'Net Profit Margin')
        if RatioValues(i) >= 0.4
            Performance{i} = 'Perfect';
        elseif RatioValues(i) >= 0.3
            Performance{i} = 'Excellent';
        elseif RatioValues(i) >= 0.2
            Performance{i} = 'Mediocre';
        else
            Performance{i} = 'Poor';
        end
    elseif strcmp(RatioNames{i}, 'Operating Margin')
        if RatioValues(i) >= 0.4
            Performance{i} = 'Perfect';
        elseif RatioValues(i) >= 0.2
            Performance{i} = 'Excellent';
        elseif RatioValues(i) >= 0.1
            Performance{i} = 'Mediocre';
        else
            Performance{i} = 'Poor';
        end
    elseif strcmp(RatioNames{i}, 'EV/EBITDA')
        if RatioValues(i) <= 5
            Performance{i} = 'Perfect';
        elseif RatioValues(i) <= 8
            Performance{i} = 'Excellent';
        elseif RatioValues(i) <= 12
            Performance{i} = 'Mediocre';
        else
            Performance{i} = 'Poor';
        end
    elseif strcmp(RatioNames{i}, 'Return on Equity') || strcmp(RatioNames{i}, 'Return on Assets')
        if RatioValues(i) >= 0.2
            Performance{i} = 'Perfect';
        elseif RatioValues(i) >= 0.15
            Performance{i} = 'Excellent';
        elseif RatioValues(i) >= 0.1
            Performance{i} = 'Mediocre';
        else
            Performance{i} = 'Poor';
        end
    elseif strcmp(RatioNames{i}, 'Revenue Per Share') || strcmp(RatioNames{i}, 'Free Cash Flow Per Share')
        if RatioValues(i) >= 0.3
            Performance{i} = 'Perfect';
        elseif RatioValues(i) >= 0.2
            Performance{i} = 'Excellent';
        elseif RatioValues(i) >= 0.1
            Performance{i} = 'Mediocre';
        else
            Performance{i} = 'Poor';
        end
    elseif strcmp(RatioNames{i}, 'Debt-to-Assets')
        if RatioValues(i) <= 0.2
            Performance{i} = 'Perfect';
        elseif RatioValues(i) <= 0.3
            Performance{i} = 'Excellent';
        elseif RatioValues(i) <= 0.6
            Performance{i} = 'Mediocre';
        else
            Performance{i} = 'Poor';
        end
    elseif strcmp(RatioNames{i}, 'Cash Flow to Debt')
        if RatioValues(i) >= 2
            Performance{i} = 'Perfect';
        elseif RatioValues(i) >= 1
            Performance{i} = 'Excellent';
        elseif RatioValues(i) >= 0.5
            Performance{i} = 'Mediocre';
        else
            Performance{i} = 'Poor';
        end
    elseif strcmp(RatioNames{i}, 'Book Value Per Share')
        if RatioValues(i) >= 1.5
            Performance{i} = 'Perfect';
        elseif RatioValues(i) >= 1
            Performance{i} = 'Excellent';
        elseif RatioValues(i) >= 0.5
            Performance{i} = 'Mediocre';
        else
            Performance{i} = 'Poor';
        end
    elseif strcmp(RatioNames{i}, 'Current Ratio')
        if RatioValues(i) >= 3
            Performance{i} = 'Perfect';
        elseif RatioValues(i) >= 2
            Performance{i} = 'Excellent';
        elseif RatioValues(i) >= 1
            Performance{i} = 'Mediocre';
        else
            Performance{i} = 'Poor';
        end
    else
        Performance{i} = 'N/A'; % For metrics without defined ranges
    end
end

% Construct the final table
ratiosTable = table(RatioNames, RatioValues, Performance, ...
    'VariableNames', {'RatioName', 'RatioValue', 'Performance'});

% Display the ratios table
disp('Stock Ratios Ordered by Importance:');
disp(ratiosTable);