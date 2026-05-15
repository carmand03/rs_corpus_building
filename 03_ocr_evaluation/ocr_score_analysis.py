# OCR Score Analysis and Visualization Script

```python
# =============================================
# OCR SCORE ANALYSIS
# =============================================
# This script:
# 1. Loads the dataset
# 2. Cleans and prepares the data
# 3. Computes summary statistics
# 4. Produces visualizations for:
#    - General OCR score distribution
#    - Distribution by language
#    - Distribution by newspaper/source
#    - Distribution over time periods
# =============================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------------------------
# Load dataset
# ---------------------------------------------

file_path = "proquest_with_ocr_scores.csv"
df = pd.read_csv(file_path)

# ---------------------------------------------
# Basic cleaning
# ---------------------------------------------

# Convert date column to datetime
# Original format appears to be YYYYMMDD

df['Date'] = pd.to_datetime(df['Date'].astype(str), format='%Y%m%d', errors='coerce')

# Extract year and decade

df['year'] = df['Date'].dt.year
df['decade'] = (df['year'] // 10) * 10

# Remove rows with missing OCR scores

df = df[df['ocr_score'].notna()]

# ---------------------------------------------
# GENERAL SUMMARY STATISTICS
# ---------------------------------------------

print("\n==============================")
print("GENERAL OCR SCORE STATISTICS")
print("==============================\n")

print(df['ocr_score'].describe())

print("\nMedian OCR score:", df['ocr_score'].median())
print("\nVariance:", df['ocr_score'].var())
print("\nSkewness:", df['ocr_score'].skew())

# ---------------------------------------------
# SUMMARY BY LANGUAGE
# ---------------------------------------------

print("\n==============================")
print("OCR SCORE BY LANGUAGE")
print("==============================\n")

language_stats = (
    df.groupby('language')['ocr_score']
    .agg(['count', 'mean', 'median', 'std', 'min', 'max'])
    .sort_values(by='mean', ascending=False)
)

print(language_stats)

# ---------------------------------------------
# SUMMARY BY NEWSPAPER / SOURCE
# ---------------------------------------------

print("\n==============================")
print("OCR SCORE BY SOURCE")
print("==============================\n")

source_stats = (
    df.groupby('Source')['ocr_score']
    .agg(['count', 'mean', 'median', 'std', 'min', 'max'])
    .sort_values(by='mean', ascending=False)
)

print(source_stats)

# ---------------------------------------------
# SUMMARY BY DECADE
# ---------------------------------------------

print("\n==============================")
print("OCR SCORE BY DECADE")
print("==============================\n")

decade_stats = (
    df.groupby('decade')['ocr_score']
    .agg(['count', 'mean', 'median', 'std', 'min', 'max'])
)

print(decade_stats)

# ---------------------------------------------
# Set plotting style
# ---------------------------------------------

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)

# ---------------------------------------------
# 1. GENERAL DISTRIBUTION (HISTOGRAM)
# ---------------------------------------------

plt.figure(figsize=(10, 6))

sns.histplot(
    df['ocr_score'],
    bins=20,
    kde=True
)

plt.title('Distribution of OCR Scores')
plt.xlabel('OCR Score')
plt.ylabel('Frequency')

plt.tight_layout()
plt.show()

# ---------------------------------------------
# 2. OCR DISTRIBUTION BY LANGUAGE
# ---------------------------------------------

plt.figure(figsize=(10, 6))

sns.boxplot(
    data=df,
    x='language',
    y='ocr_score'
)

plt.title('OCR Scores by Language')
plt.xlabel('Language')
plt.ylabel('OCR Score')

plt.tight_layout()
plt.show()

# Optional violin plot

plt.figure(figsize=(10, 6))

sns.violinplot(
    data=df,
    x='language',
    y='ocr_score'
)

plt.title('Distribution of OCR Scores by Language')
plt.xlabel('Language')
plt.ylabel('OCR Score')

plt.tight_layout()
plt.show()

# ---------------------------------------------
# 3. OCR DISTRIBUTION BY NEWSPAPER / SOURCE
# ---------------------------------------------
# Keep only top newspapers by number of articles
# to avoid overcrowding

TOP_N = 15

top_sources = (
    df['Source']
    .value_counts()
    .head(TOP_N)
    .index
)

subset_sources = df[df['Source'].isin(top_sources)]

plt.figure(figsize=(14, 8))

sns.boxplot(
    data=subset_sources,
    x='Source',
    y='ocr_score'
)

plt.xticks(rotation=45, ha='right')
plt.title(f'OCR Scores by Newspaper (Top {TOP_N} Sources)')
plt.xlabel('Newspaper / Source')
plt.ylabel('OCR Score')

plt.tight_layout()
plt.show()

# ---------------------------------------------
# 4. OCR SCORES OVER TIME (DECADES)
# ---------------------------------------------

plt.figure(figsize=(12, 6))

sns.boxplot(
    data=df,
    x='decade',
    y='ocr_score'
)

plt.title('OCR Scores by Decade')
plt.xlabel('Decade')
plt.ylabel('OCR Score')

plt.tight_layout()
plt.show()

# ---------------------------------------------
# 5. TEMPORAL TREND (MEAN OCR SCORE OVER TIME)
# ---------------------------------------------

mean_by_year = (
    df.groupby('year')['ocr_score']
    .mean()
    .reset_index()
)

plt.figure(figsize=(14, 6))

sns.lineplot(
    data=mean_by_year,
    x='year',
    y='ocr_score'
)

plt.title('Average OCR Score Over Time')
plt.xlabel('Year')
plt.ylabel('Mean OCR Score')

plt.tight_layout()
plt.show()

# ---------------------------------------------
# 6. HEATMAP: LANGUAGE x DECADE
# ---------------------------------------------

heatmap_data = (
    df.pivot_table(
        values='ocr_score',
        index='language',
        columns='decade',
        aggfunc='mean'
    )
)

plt.figure(figsize=(12, 5))

sns.heatmap(
    heatmap_data,
    annot=True,
    cmap='viridis'
)

plt.title('Mean OCR Score by Language and Decade')

plt.tight_layout()
plt.show()

# ---------------------------------------------
# Export summary tables (optional)
# ---------------------------------------------

language_stats.to_csv('ocr_stats_by_language.csv')
source_stats.to_csv('ocr_stats_by_source.csv')
decade_stats.to_csv('ocr_stats_by_decade.csv')

print("\nAnalysis complete.")
print("Summary tables exported as CSV files.")
```

## Notes

### Required packages

Install packages if necessary:

```bash
pip install pandas matplotlib seaborn numpy
```

### Recommended interpretation

* Histograms help identify skewness and concentration of OCR quality.
* Boxplots reveal variability and outliers across languages/newspapers.
* Temporal plots can show improvements or deterioration in OCR quality over time.
* The heatmap is useful for detecting interactions between language and period.

### Possible extensions included below

The following analyses extend the script with deeper statistical exploration.

Add these sections at the end of the script.

```python
# =============================================
# EXTENSION 1: OCR SCORE VS ARTICLE LENGTH
# =============================================
# This examines whether longer articles tend
# to have poorer OCR quality.

# Compute text length
# Replace 'Full Text' with the actual text column if needed

text_column = 'Full Text'

if text_column in df.columns:

    df['text_length'] = (
        df[text_column]
        .astype(str)
        .str.len()
    )

    print("
==============================")
    print("OCR SCORE VS ARTICLE LENGTH")
    print("==============================
")

    correlation = df['ocr_score'].corr(df['text_length'])
    print("Correlation between OCR score and text length:", correlation)

    plt.figure(figsize=(10, 6))

    sns.scatterplot(
        data=df,
        x='text_length',
        y='ocr_score',
        alpha=0.4
    )

    plt.title('OCR Score vs Article Length')
    plt.xlabel('Article Length (characters)')
    plt.ylabel('OCR Score')

    plt.tight_layout()
    plt.show()

# =============================================
# EXTENSION 2: IDENTIFY SOURCES WITH POOR OCR
# =============================================

poor_sources = (
    df.groupby('Source')['ocr_score']
    .mean()
    .sort_values()
)

print("
==============================")
print("SOURCES WITH LOWEST OCR SCORES")
print("==============================
")

print(poor_sources.head(20))

plt.figure(figsize=(12, 8))

poor_sources.head(15).plot(kind='barh')

plt.title('Newspapers with Lowest Average OCR Scores')
plt.xlabel('Average OCR Score')
plt.ylabel('Source')

plt.tight_layout()
plt.show()

# =============================================
# EXTENSION 3: DETECT OCR OUTLIERS
# =============================================
# Detect extremely poor OCR records using IQR

Q1 = df['ocr_score'].quantile(0.25)
Q3 = df['ocr_score'].quantile(0.75)
IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

outliers = df[
    (df['ocr_score'] < lower_bound) |
    (df['ocr_score'] > upper_bound)
]

print("
==============================")
print("OCR OUTLIERS")
print("==============================
")

print("Number of outliers:", len(outliers))

print(outliers[
    ['Source', 'language', 'Date', 'ocr_score']
].head())

# Export outliers
outliers.to_csv('ocr_outliers.csv', index=False)

# =============================================
# EXTENSION 4: ROLLING AVERAGE OVER TIME
# =============================================
# Smooth temporal variation in OCR quality

rolling_data = (
    df.groupby('year')['ocr_score']
    .mean()
    .rolling(window=5, center=True)
    .mean()
)

plt.figure(figsize=(14, 6))

plt.plot(rolling_data.index, rolling_data.values)

plt.title('5-Year Rolling Average of OCR Scores')
plt.xlabel('Year')
plt.ylabel('Rolling Mean OCR Score')

plt.tight_layout()
plt.show()

# =============================================
# EXTENSION 5: STATISTICAL TESTS
# =============================================
# Test whether OCR distributions differ
# significantly across languages and newspapers

from scipy.stats import kruskal
from scipy.stats import f_oneway

# ---------- Language comparison ----------

language_groups = [
    group['ocr_score'].dropna().values
    for _, group in df.groupby('language')
]

if len(language_groups) > 1:

    kw_stat, kw_p = kruskal(*language_groups)

    print("
==============================")
    print("KRUSKAL-WALLIS TEST: LANGUAGES")
    print("==============================
")

    print("Statistic:", kw_stat)
    print("p-value:", kw_p)

    if kw_p < 0.05:
        print("Result: significant differences between languages")
    else:
        print("Result: no significant differences detected")

# ---------- Source comparison ----------
# Restrict to major newspapers to avoid noise

major_sources = (
    df['Source']
    .value_counts()
    .head(10)
    .index
)

source_subset = df[df['Source'].isin(major_sources)]

source_groups = [
    group['ocr_score'].dropna().values
    for _, group in source_subset.groupby('Source')
]

if len(source_groups) > 1:

    kw_stat2, kw_p2 = kruskal(*source_groups)

    print("
==============================")
    print("KRUSKAL-WALLIS TEST: SOURCES")
    print("==============================
")

    print("Statistic:", kw_stat2)
    print("p-value:", kw_p2)

    if kw_p2 < 0.05:
        print("Result: significant differences between newspapers")
    else:
        print("Result: no significant differences detected")

# =============================================
# EXTENSION 6: DENSITY PLOTS BY LANGUAGE
# =============================================
# Better than histograms for comparing distributions

plt.figure(figsize=(12, 6))

for lang in df['language'].dropna().unique():

    subset = df[df['language'] == lang]

    sns.kdeplot(
        subset['ocr_score'],
        label=lang,
        fill=False
    )

plt.title('Density Distribution of OCR Scores by Language')
plt.xlabel('OCR Score')
plt.ylabel('Density')

plt.legend()
plt.tight_layout()
plt.show()

# =============================================
# EXTENSION 7: HEATMAP OF NEWSPAPER x DECADE
# =============================================
# Restrict to major newspapers

major_sources = (
    df['Source']
    .value_counts()
    .head(10)
    .index
)

heatmap_subset = df[df['Source'].isin(major_sources)]

source_decade = heatmap_subset.pivot_table(
    values='ocr_score',
    index='Source',
    columns='decade',
    aggfunc='mean'
)

plt.figure(figsize=(14, 8))

sns.heatmap(
    source_decade,
    annot=True,
    cmap='magma'
)

plt.title('Mean OCR Scores by Newspaper and Decade')

plt.tight_layout()
plt.show()

# =============================================
# EXTENSION 8: SAVE ALL FIGURES AUTOMATICALLY
# =============================================
# Example usage:
# plt.savefig('figure_name.png', dpi=300)
# Add before each plt.show()

# Example:
# plt.savefig('ocr_histogram.png', dpi=300)

print("
Extended analysis complete.")
```

## Additional analytical directions

Depending on your research goals, you may also consider:

* Comparing OCR quality between colonial and local newspapers
* Testing whether multilingual newspapers have lower OCR accuracy
* Measuring OCR deterioration during wartime periods
* Mapping OCR quality geographically if publication place is available
* Using NLP quality metrics alongside OCR scores
* Performing clustering of newspapers based on OCR characteristics
* Building predictive models of OCR quality using publication metadata
