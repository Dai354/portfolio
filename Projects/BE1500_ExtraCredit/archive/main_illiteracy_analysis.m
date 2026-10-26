% ==================================================
% BE 1500 Extra Credit Project
% Main Script: main_illiteracy_analysis.m
% ==================================================

clc; clear; close all;

% --- Step 1: Load Dataset ---
filename = 'child_illiteracy_by_country.csv';
if ~isfile(filename)
    error('Data file "%s" not found. Check your working folder.', filename);
end

T = readtable(filename);
disp('Global Child Illiteracy dataset loaded successfully.');
disp('Detected column names:');
disp(T.Properties.VariableNames);

% --- Step 2: Identify columns automatically ---
namesLower = lower(T.Properties.VariableNames);

% Identify illiteracy column
illIdx = contains(namesLower, 'illiteracy') | contains(namesLower, 'illiterate');
if any(illIdx)
    colName = T.Properties.VariableNames{find(illIdx, 1)};
else
    colName = input('Enter the column name containing illiteracy data: ', 's');
end

% Identify year column
yearIdx = strcmpi(T.Properties.VariableNames, 'Year') | strcmpi(T.Properties.VariableNames, 'year');
if any(yearIdx)
    yearCol = T.Properties.VariableNames{yearIdx};
else
    yearCol = input('Enter the column name containing year data: ', 's');
end

% Identify country column
countryIdx = contains(namesLower, 'country');
if any(countryIdx)
    countryCol = T.Properties.VariableNames{find(countryIdx, 1)};
else
    countryCol = input('Enter the column name containing country names: ', 's');
end

fprintf('\nColumns in use:\n');
fprintf('  Illiteracy column: %s\n', colName);
fprintf('  Year column:       %s\n', yearCol);
fprintf('  Country column:    %s\n', countryCol);

% --- Step 3: Ensure numeric columns are numeric ---
if ~isnumeric(T.(yearCol))
    T.(yearCol) = str2double(string(T.(yearCol)));
end
if ~isnumeric(T.(colName))
    T.(colName) = str2double(string(T.(colName)));
end

% --- Step 4: Menu-driven program loop ---
choice = 0;
while choice ~= 5
    fprintf('\n=== Global Child Illiteracy Analysis ===\n');
    disp('1. View Descriptive Statistics');
    disp('2. Sort and View by Year (Bar Chart)');
    disp('3. Plot Illiteracy Trend by Country');
    disp('4. Predict Illiteracy by Country (Regression)');
    disp('5. Exit Program');

    choice = input('Choose an option (1–5): ');

    switch choice
        case 1
            % --- Descriptive statistics ---
            stats = calcDescriptiveStats(T, colName);
            disp(stats);

        case 2
            % --- Sort by year and create bar chart ---
            sortedT = sortrows(T, yearCol);
            validRows = ~isnan(sortedT.(yearCol)) & ~isnan(sortedT.(colName));
            sortedT = sortedT(validRows, :);
            disp(sortedT(1:min(10,height(sortedT)), :)); % preview
            figure;
            bar(sortedT.(yearCol), sortedT.(colName));
            title('Illiteracy Measure by Year');
            xlabel('Year'); ylabel(strrep(colName, '_', ' '));
            grid on;

        case 3
            % --- Plot trend by specific country ---
            country = input('Enter country name: ', 's');
            idx = strcmpi(T.(countryCol), country);
            if ~any(idx)
                fprintf('Country "%s" not found in dataset.\n', country);
            else
                figure;
                plot(T.(yearCol)(idx), T.(colName)(idx), '-o', ...
                    'LineWidth', 1.5, 'Color', [0 0.447 0.741]);
                title(['Illiteracy Trend for ', country]);
                xlabel('Year'); ylabel(strrep(colName, '_', ' '));
                grid on;
            end

        case 4
            % --- Regression-based prediction ---
            country = input('Enter country name for prediction: ', 's');
            predictIlliteracyTrend(T, country, colName, countryCol, yearCol);

        case 5
            % --- Exit program ---
            disp('Exiting program... Goodbye!');
            break;

        otherwise
            disp('Invalid selection. Please choose 1–5.');
    end
end
