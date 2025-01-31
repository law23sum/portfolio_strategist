% Import the CSV file and calculate total amounts for each account and direction

% Specify the path to the CSV file
csvFilePath = '/Users/chrisdixon/Desktop/finance/personal_loan.csv';

% Import the data from the CSV file
opts = detectImportOptions(csvFilePath);
data = readtable(csvFilePath, opts);

% Ensure the Amount column is numeric
if ~isnumeric(data.Amount)
    data.Amount = str2double(data.Amount);
end

% Ensure Account numbers are displayed fully as strings
data.Account = int64(data.Account);

% Create the first table: individual amounts grouped by account and direction
individualAmounts = sortrows(data, {'Direction'});

% Display the first table
disp('Individual amounts listed by account and direction:');
disp(individualAmounts);

% Save the first table to a CSV file
individualOutputFilePath = 'individual_account_details.csv';
writetable(individualAmounts, individualOutputFilePath);

% Create the second table: total amounts for each account
totalAmounts = varfun(@sum, data, 'InputVariables', 'Amount', 'GroupingVariables', {'Direction'});

% Display the second table
disp('Total amounts for each account:');
disp(totalAmounts);

% Notify user
fprintf('The individual amounts have been saved to: %s\n', individualOutputFilePath);
fprintf('The total amounts for each account have been saved to: %s\n', totalOutputFilePath);