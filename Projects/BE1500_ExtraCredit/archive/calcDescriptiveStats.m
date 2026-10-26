function stats = calcDescriptiveStats(T, colName)
% calcDescriptiveStats  Compute descriptive statistics for chosen data column.
%
%   stats = calcDescriptiveStats(T, colName)
%   Inputs:
%     T        - table of data
%     colName  - column name string (e.g., 'IlliteracyRate')
%   Output:
%     stats    - structure with mean, std, min, max

data = T.(colName);

if any(ismissing(data))
    disp('Warning: Missing data detected. NaN values omitted.');
end

stats.mean = mean(data, 'omitnan');
stats.std  = std(data, 'omitnan');
stats.min  = min(data);
stats.max  = max(data);

fprintf('\nDescriptive Statistics for %s:\n', colName);
fprintf('  Mean: %.3f\n', stats.mean);
fprintf('  Std:  %.3f\n', stats.std);
fprintf('  Min:  %.3f\n', stats.min);
fprintf('  Max:  %.3f\n', stats.max);
end
