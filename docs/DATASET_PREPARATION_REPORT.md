# Demand Decision Intelligence

## Dataset Understanding, Cleaning & Preparation Report

> **Purpose:** This report explains the dataset, the problems found in
> the raw data, the preprocessing performed, the decisions taken, and
> the benefits of the prepared data. It is written as a simple team
> handoff document.

------------------------------------------------------------------------

# 1. Dataset Overview

**Dataset:** Flipkart Grocery Transaction and Product Details

**Kaggle:**
https://www.kaggle.com/datasets/aryansingh95/flipkart-grocery-transaction-and-product-details

The dataset contains grocery transaction/sales data and a product master
with product-level information.

## Raw Sales Files

There are 7 sales CSV files:

-   `fact_sales_apr1.csv`
-   `fact_sales_apr2.csv`
-   `fact_sales_may1.csv`
-   `fact_sales_may2.csv`
-   `fact_sales_jun1.csv`
-   `fact_sales_jun2.csv`
-   `fact_sales_jul1.csv`

Product master:

`dataset/raw/products/dim_product.csv`

------------------------------------------------------------------------

# 2. What Does the Data Contain?

The sales data contains transaction-level information such as:

-   Date
-   Product ID
-   Quantity
-   Selling price
-   Discount
-   Landing price
-   City
-   Order information

The product master contains:

-   Product name
-   Brand
-   Manufacturer
-   Product type
-   Category hierarchy

The sales data covers:

**01 April 2022 → 10 July 2022**

and contains data from **4 cities**.

------------------------------------------------------------------------

# 3. Raw Dataset Size

After combining the 7 sales files:

**46,706,387 transaction rows**

The data was not randomly reduced. Rows were removed only when there was
a clear data-quality reason. In practice, the cleaning process removed
**0 rows**.

------------------------------------------------------------------------

# 4. Date Validation

### Scripts

``` text
sales data/inspect_dates.py
sales data/validate_dates.py
```

### Checks

-   Missing dates
-   Invalid dates
-   Date format
-   Date range
-   Monthly distribution

### Result

-   Invalid dates: **0**
-   Missing dates: **0**
-   Format: `YYYY-MM-DD`
-   Date range: **2022-04-01 → 2022-07-10**

### Month-wise rows

  Month           Rows
  ------- ------------
  April     15,385,896
  May       12,356,432
  June      12,152,765
  July       6,811,294

### Benefit

The time information is reliable, which is important for time-series
forecasting.

------------------------------------------------------------------------

# 5. Sales Cleaning

### Script

``` text
sales data/clean_sales.py
```

### Result

  Metric                        Result
  ----------------------- ------------
  Input rows                46,706,387
  Output rows               46,706,387
  Rows removed                       0
  Missing landing price         79,355

The missing landing-price values were investigated separately instead of
deleting those transactions.

### Benefit

The original sales information was preserved without unnecessary row
deletion.

------------------------------------------------------------------------

# 6. Product Master Validation

### Scripts

``` text
sales data/validate_products.py
sales data/check_product_ids.py
```

### Result

  Check                         Result
  --------------------------- --------
  Product master rows           32,226
  Unique product IDs            32,226
  Duplicate product IDs              0
  Exact duplicate rows               0
  Missing brand name             1,438
  Missing manufacturer name      2,416

### Conclusion

The product master has unique product IDs and no duplicate IDs.

Some descriptive fields are missing, but they were not filled with
made-up values.

------------------------------------------------------------------------

# 7. Sales ↔ Product Mapping

### Script

``` text
sales data/join_sales_products.py
```

Sales product IDs were matched with the product master using
`product_id`.

## Product-level result

  Metric                         Result
  ---------------------------- --------
  Unique products in sales       17,304
  Products in product master     32,226
  Matched unique IDs             15,808
  Unmatched unique IDs            1,496

## Row-level result

  Metric                   Result
  ------------------ ------------
  Total sales rows     46,706,387
  Matched rows         46,174,265
  Unmatched rows          532,122
  Match rate           **98.86%**
  Unmatched rate        **1.14%**

------------------------------------------------------------------------

# 8. What Happened to the Unmatched Sales?

### Script

``` text
sales data/investigate_unmatched_products.py
```

The **532,122 unmatched sales rows** were investigated.

They contained:

-   Quantity: **629,141**
-   Estimated sales value: **₹57,839,340**
-   Discount: **₹299,160.48**

### Decision

These rows were **not deleted**.

### Why?

An unmatched product ID does not automatically mean that the sales
transaction is invalid. The transaction can still contain valid
quantity, revenue and demand information.

Deleting them would remove real sales activity and could bias
forecasting.

### Benefit

We preserve the actual demand signal instead of losing 1.14% of sales
rows just because product metadata was unavailable.

------------------------------------------------------------------------

# 9. Missing Value Analysis

### Script

``` text
sales data/check_missing_values.py
```

Important missing values found:

  Field                                Missing Rows
  ---------------------------------- --------------
  Landing price                              79,355
  Product name/category attributes          532,122
  Brand name                             12,481,745
  Manufacturer name                         578,400

The product/category missing values are mainly related to the unmatched
product IDs.

------------------------------------------------------------------------

# 10. Landing Price Investigation

### Script

``` text
sales data/investigate_landing_price.py
```

We investigated the **79,355 missing landing-price rows**.

### Important findings

  Check                                     Result
  --------------------------------------- --------
  Missing quantity                               0
  Missing selling price                          0
  Quantity + selling price both missing          0
  Missing landing price                     79,355

### By month

  Month     Missing Rows
  ------- --------------
  April           21,164
  May              7,605
  June             4,095
  July            46,491

### By city

  City          Missing Rows
  ----------- --------------
  Delhi               32,214
  HR-NCR              22,901
  Mumbai              22,218
  Bengaluru            2,022

### Benefit

Instead of assuming missing landing price means a bad transaction, we
investigated whether reliable historical information could recover it.

------------------------------------------------------------------------

# 11. Landing Price Imputation Analysis

### Script

``` text
sales data/analyze_landing_price_imputation.py
```

### Result

-   Products with missing landing price: **757**
-   Products with valid historical landing price: **743**
-   Products with no valid historical landing price: **14**
-   Missing landing-price rows: **79,355**
-   Reliably fillable rows: **37,484 (47.24%)**
-   Not reliably fillable: **41,871 (52.76%)**

------------------------------------------------------------------------

# 12. Landing Price Imputation

### Script

``` text
sales data/impute_landing_price.py
```

### Final result

  Metric                      Rows
  ------------------- ------------
  Original rows         46,706,387
  Output rows           46,706,387
  Missing before            79,355
  Imputed                   37,484
  Remaining missing         41,871

### Decision

Only values supported by reliable historical product information were
imputed.

The remaining **41,871** values were left missing.

### Why?

We should not invent values simply to make the dataset 100% complete.

### Benefit

We recover useful information where evidence exists while avoiding
artificial data.

------------------------------------------------------------------------

# 13. Numerical Validation

### Scripts

``` text
sales data/validate_numerical_values.py
sales data/investigate_numerical_anomalies.py
```

## `procured_quantity`

-   Negative: **0**

-   Zero: **184,411**

-   Missing: **0**

-   1000: **0**

## `unit_selling_price`

-   Negative: **0**

-   Zero: **125,349**

-   Missing: **0**

-   ₹10,000: **18**

## `total_discount_amount`

-   Negative: **0**

-   Zero: **45,629,057**

-   Missing: **0**

-   ₹10,000: **0**

## `total_weighted_landing_price`

-   Negative: **0**

-   Zero: **23,606**

-   Missing: **41,871**

-   ₹10,000: **34**

### Decision

No negative numerical anomalies were found.

Zero and high values were not automatically deleted because unusual does
not necessarily mean invalid.

------------------------------------------------------------------------

# 14. Why We Did Not Randomly Delete Data

The main preprocessing rule was:

> **Do not delete data just because it looks unusual.**

Therefore:

-   Unmatched products → **preserved**
-   Zero quantity → **preserved**
-   Zero selling price → **preserved**
-   Missing landing price → **investigated**
-   High selling price → **investigated**
-   High landing price → **investigated**
-   Random deletion → **not performed**

### Benefit

This reduces the chance of creating bias in demand analysis and ML
forecasting.

------------------------------------------------------------------------

# 15. Creating the Daily Demand Dataset

### Script

``` text
sales data/build_daily_demand.py
```

The raw transaction data is extremely large. For demand forecasting, the
useful question is:

> **How much of a product was demanded in a particular city on a
> particular day?**

Therefore, transactions were aggregated to:

**Product + City + Day**

### Output

``` text
dataset/processed/daily_product_demand.csv
```

### Result

  Metric                                    Result
  ------------------------ -----------------------
  Input transaction rows                46,706,387
  Daily rows                             1,764,981
  Products                                  17,304
  Cities                                         4
  Date range                 Apr 1 -- Jul 10, 2022

### Columns

``` text
date_
product_id
product_name
city_name
l0_category
l1_category
l2_category
daily_quantity
daily_revenue
order_count
```

------------------------------------------------------------------------

# 16. Why Daily Demand Data Is Better for Forecasting

Instead of repeatedly working with:

**46.7 million transaction rows**

we now have:

**1.76 million product-city-day records**

The important demand target is:

``` text
daily_quantity
```

This makes it easier to create:

-   Previous-day demand
-   7-day lag
-   14-day lag
-   28-day lag
-   Moving averages
-   Demand volatility
-   Weekday effects
-   Weekend effects

### Benefit

The data is now much more practical for forecasting while retaining the
core demand signal.

------------------------------------------------------------------------

# 17. Daily Demand Data Quality

After aggregation:

  Field                Missing
  ------------------ ---------
  `date_`                    0
  `daily_quantity`           0
  `daily_revenue`            0

There are **40,913 rows** with missing product/category descriptive
information because some sales product IDs were not found in the product
master.

The core demand fields remain usable.

------------------------------------------------------------------------

# 18. Final Business-Level Numbers

From the processed demand data:

### Total Quantity

**60,176,096 units**

### Estimated Revenue

**₹4,725,948,522**

Approximately:

**₹472.6 Crore**

### Products

**17,304**

### Cities

**4**

------------------------------------------------------------------------

# 19. City-wise Demand

  City            Quantity   Revenue
  ----------- ------------ ---------
  Delhi         28,075,593   ₹2.289B
  HR-NCR        15,339,245   ₹1.140B
  Bengaluru     11,747,370   ₹0.865B
  Mumbai         5,013,888   ₹0.432B

### Observation

Delhi has the highest quantity and revenue contribution among the four
cities.

------------------------------------------------------------------------

# 20. Overall Benefit of the Data Preparation

The preprocessing gives the project a reliable foundation for the next
stages.

### Before

``` text
46.7M transaction rows
        ↓
Missing values
        ↓
Product mapping gaps
        ↓
Large transaction-level data
        ↓
Not directly convenient for forecasting
```

### After

``` text
Validated sales
        ↓
Product mapping
        ↓
Careful missing-value treatment
        ↓
Numerical validation
        ↓
Daily product-city demand
        ↓
Forecasting-ready foundation
```

### Main benefits

1.  Dates are validated.
2.  Duplicate product IDs were ruled out.
3.  98.86% of sales rows were successfully mapped to product data.
4.  Unmatched sales were preserved instead of being unnecessarily
    deleted.
5.  Reliable missing landing prices were recovered.
6.  Unreliable values were not artificially invented.
7.  Negative numerical anomalies were ruled out.
8.  Transaction-level data was converted to daily demand.
9.  The working dataset became much smaller and easier to use.
10. The data is now ready for forecasting and ML feature creation.

------------------------------------------------------------------------

# 21. Complete Data Preparation Pipeline

``` text
Kaggle Dataset
      │
      ▼
7 Raw Sales CSVs
      │
      ▼
Combine Sales
      │
      ▼
46.7M Transaction Rows
      │
      ├── Date Validation
      │
      ├── Numerical Validation
      │
      └── Duplicate / Product Validation
      │
      ▼
Sales ↔ Product Mapping
      │
      ├── 98.86% Matched
      └── 1.14% Unmatched → Preserved
      │
      ▼
Missing Value Investigation
      │
      ▼
Landing Price Imputation
      │
      ▼
Daily Product Demand
      │
      ▼
1.76M Product-City-Day Rows
      │
      ▼
Forecasting / ML
```

------------------------------------------------------------------------

# 22. Scripts Used

## Combining & Cleaning

``` text
sales data/combine_sales.py
sales data/clean_sales.py
```

## Validation

``` text
sales data/inspect_dates.py
sales data/validate_dates.py
sales data/check_missing_values.py
sales data/check_product_ids.py
sales data/validate_products.py
sales data/validate_numerical_values.py
```

## Product Mapping & Missing Values

``` text
sales data/join_sales_products.py
sales data/investigate_unmatched_products.py
sales data/investigate_landing_price.py
sales data/analyze_landing_price_imputation.py
sales data/impute_landing_price.py
sales data/investigate_numerical_anomalies.py
```

## Daily Demand

``` text
sales data/build_daily_demand.py
```

------------------------------------------------------------------------

# 23. Important Files for Team Members

If a team member already has the original Kaggle dataset:

### For ML / Forecasting

Use:

``` text
dataset/processed/daily_product_demand.csv
```

Approximate size:

**205 MB**

### For understanding/reproducing preprocessing

Use the scripts inside:

``` text
sales data/
```

### Large files

Do not unnecessarily share or recreate the \~9 GB processed
transaction-level file for normal forecasting work.

Large datasets should not be pushed to GitHub.

------------------------------------------------------------------------

# 24. Current Project Status

  Stage                            Status
  -------------------------------- -------------
  Raw data collection              ✅ Complete
  Date validation                  ✅ Complete
  Sales cleaning                   ✅ Complete
  Product validation               ✅ Complete
  Product mapping                  ✅ Complete
  Missing-value investigation      ✅ Complete
  Landing-price imputation         ✅ Complete
  Numerical validation             ✅ Complete
  Daily demand aggregation         ✅ Complete
  EDA                              ✅ Complete
  Forecasting feature foundation   ✅ Complete
  Baseline forecasting             🔄 Next
  ML model training                🔄 Next
  Model evaluation                 🔄 Next
  Inventory decision system        🔄 Later

------------------------------------------------------------------------

# 25. Next Step

The dataset preparation stage is complete.

The next phase is:

``` text
Daily Demand
      ↓
Baseline Forecast
      ↓
Naive Forecast
      ↓
7-Day Moving Average
      ↓
28-Day Moving Average
      ↓
MAE / RMSE / WAPE
      ↓
Machine Learning Models
      ↓
Train → Predict → Evaluate
      ↓
Best Model
      ↓
Demand Forecast
      ↓
Inventory / Reorder Decision
```

**Forecast target:**

``` text
daily_quantity
```

**Forecast level:**

``` text
Product + City + Day
```

------------------------------------------------------------------------

# 26. Important Note About `order_count`

The current `order_count` in `daily_product_demand.csv` was calculated
chunk-wise and then aggregated.

Therefore, if an `order_id` crosses a chunk boundary, it can potentially
be counted more than once.

So:

> **Do not treat `order_count` as an exact unique-order count for final
> business reporting.**

For the current forecasting work, the main target remains:

``` text
daily_quantity
```

------------------------------------------------------------------------

# Final Conclusion

The raw grocery dataset was large and contained several data-quality
issues, especially missing landing prices and product-master mapping
gaps.

Instead of deleting problematic rows or filling values without evidence,
the data was investigated step-by-step. This allowed us to preserve real
sales activity while recovering values wherever reliable information
existed.

The final `daily_product_demand.csv` converts the large transaction
dataset into a practical **product-city-day demand dataset** and
provides the foundation required for forecasting, machine learning, and
eventually inventory decision-making.

**Data preparation is complete. The project is now ready for the Machine
Learning / Forecasting stage.**
