function predictIlliteracyTrend(T, country, colName, countryCol, yearCol)
% predictIlliteracyTrend  Fit a linear regression for the selected country's data.
%
%   predictIlliteracyTrend(T, country, colName, countryCol, yearCol)

% --- Identify rows for selected country ---
idx = strcmpi(T.(countryCol), country);
if ~any(idx)
    fprintf('Country "%s" not found in dataset.\n', country);
    return;
end

years  = T.(yearCol)(idx);
values = T.(colName)(idx);

% Remove missing data
validRows = ~isnan(years) & ~isnan(values);
years  = years(validRows);
values = values(validRows);

% --- Check for sufficient data ---
if numel(unique(years)) < 2
    fprintf('Not enough data points for "%s" to fit a regression.\n', country);
    return;
end

% --- Linear regression: y = p1*x + p2 ---
p = polyfit(years, values, 1);
futureYears = (max(years):max(years)+10)';     % predict next 10 years
predicted   = polyval(p, futureYears);

% --- Plot ---
figure;
plot(years, values, 'bo-', 'LineWidth', 1.5); hold on;
plot(futureYears, predicted, 'r--', 'LineWidth', 2);
xlabel('Year');
ylabel(strrep(colName, '_', ' '));
title(['Predicted Illiteracy Trend for ', country]);
legend('Actual', 'Predicted', 'Location', 'Best');
grid on;

% --- Print model summary ---
fprintf('\nModel for %s:\n', country);
fprintf('  Equation: y = %.4f*x + %.4f\n', p(1), p(2));
fprintf('  Predicted %s in year %d: %.3f\n', ...
    strrep(colName,'_',' '), futureYears(end), predicted(end));
end
