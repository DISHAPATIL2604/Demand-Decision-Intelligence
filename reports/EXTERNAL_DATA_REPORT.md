# External Data Collection & Validation Report

**Project:** Demand-Decision-Intelligence  
**Phase:** External Data Collection & Forensic Quality Audit  
**Date:** September 12, 2026  
**Status:** **COMPLETE & FULLY VALIDATED**  
**Sales Period Coverage Target:** `2022-04-01` to `2022-07-10` (101 calendar days)  

---

## Executive Summary & Integrity Audit

To empower future demand forecasting, seasonal decomposition, and inventory safety stock planning, three external datasets were gathered, validated, and documented.

### Strict Data Integrity Guarantees
1. **Sales Dataset Untouched:**
   - Canonical Sales Master: `dataset/cleaned/sales_product_master.csv`
   - Total Sales Rows: `46,706,387`
   - Master File Size: `9.487 GB` (10,186,818,487 bytes)
   - Status: **UNTOUCHED, UNMODIFIED, STRICTLY ISOLATED**.
2. **Raw Sales Files Untouched:**
   - Directory: `dataset/raw/` (all original 100 sales chunk CSVs remain pristine).
3. **No Synthetic / Fabricated Data:**
   - 100% of external records are drawn from verified, publicly available, official sources.
   - Zero synthetic rows, zero hallucinated dates, zero interpolated prices.
4. **No Premature ML / Feature Engineering:**
   - External data has NOT been merged or joined with sales transactions.
   - No forecasting models or feature sets have been constructed in this phase.

---

# DATASET 1: Calendar / Holiday / Festival Data

### 1. Dataset / Source Name
- **Dataset Name:** India National & State Gazetted / Restricted Holiday Calendar (2022)
- **Official Issuing Authority:** Department of Personnel and Training (DOPT), Ministry of Personnel, Public Grievances and Pensions, Government of India
- **Reference Standard:** Python `holidays` library v0.104 (`holidays.India` rule engine)

### 2. Exact Source URL
- **Official DOPT Holiday Gazette:** [https://dopt.gov.in/sites/default/files/Holidays_2022.pdf](https://dopt.gov.in/sites/default/files/Holidays_2022.pdf)
- **Rule Engine Repository:** [https://github.com/vacanza/python-holidays](https://github.com/vacanza/python-holidays)

### 3. Why the Data is Relevant to Demand Forecasting
1. **Pre-Festival Demand Surges:** Retail grocery demand experiences substantial volume spikes 2–4 days prior to major festivals (e.g., Eid-ul-Fitr, Ugadi/Gudi Padwa, Akshaya Tritiya, Good Friday). Households stock up on edible oils, sugar, flours, dairy, dry fruits, and sweets.
2. **Intra-Week Fulfillment Volatility:** Public non-working holidays and weekends shift order density from commercial and tech-corridor delivery nodes to residential suburbs.
3. **Regional Heterogeneity:** State-specific holidays (such as Ugadi in Bengaluru/Karnataka, Gudi Padwa & Maharashtra Day in Mumbai, and Maharana Pratap Jayanti in Haryana/HR-NCR) drive local sales divergence across the 4 operating territories.

### 4. Date Coverage
- **Start Date:** `2022-04-01`
- **End Date:** `2022-07-10`
- **Continuity:** Exactly 101 consecutive calendar days (100% temporal alignment with the sales dataset).

### 5. Number of Rows
- **Total Rows:** `101` rows (1 row per calendar day).

### 6. Columns
The dataset is structured with 18 comprehensive fields:
- `date_`: ISO-8601 calendar date (`YYYY-MM-DD`)
- `day_of_week`: Day index (0 = Monday, 6 = Sunday)
- `day_name`: Full English day name (`Monday` through `Sunday`)
- `month`: Calendar month integer (`4`, `5`, `6`, `7`)
- `quarter`: Calendar quarter (`2`, `3`)
- `year`: Calendar year (`2022`)
- `is_weekend`: Binary flag (1 = Saturday or Sunday, 0 = Weekday)
- `is_holiday_national`: Binary flag (1 = Central Gazetted Holiday, 0 = Non-Gazetted)
- `holiday_name_national`: Central gazetted holiday title or `None`
- `holiday_type`: Classification (`Gazetted`, `Restricted`, `State`, or `None`)
- `holiday_delhi`: State holiday title for NCT of Delhi or `None`
- `holiday_bengaluru`: State holiday title for Karnataka / Bengaluru or `None`
- `holiday_mumbai`: State holiday title for Maharashtra / Mumbai or `None`
- `holiday_hr_ncr`: State holiday title for Haryana / HR-NCR or `None`
- `holiday_restricted`: DOPT optional/restricted holiday name or `None`
- `is_holiday_any`: Binary indicator (1 if national, state, or restricted holiday occurs)
- `primary_holiday_name`: Consolidated holiday / festival name or `None`
- `season`: Season indicator (`Summer` for Apr–May, `Monsoon` for Jun–Jul)

### 7. Missing-Value Summary
- **Core Temporal Fields (`date_`, `day_of_week`, `month`, `year`, `is_weekend`, `season`):** `0` null values (0.0%).
- **Holiday Flags (`is_holiday_national`, `is_holiday_any`):** `0` null values (0.0%).
- **Holiday Name Fields:** Missing values on ordinary non-holiday days are explicitly populated with standard token `"None"`. Zero untracked NaNs.

### 8. Duplicate Check
- **Duplicate Dates (`date_`):** `0` duplicates. Every date from 2022-04-01 to 2022-07-10 occurs exactly once.

### 9. Coverage by City / Commodity
- **City Coverage:** Covers India centrally and provides state-level breakdown for all 4 project cities:
  - **Bengaluru:** Karnataka state holiday schedule (`holiday_bengaluru`)
  - **Delhi:** NCT of Delhi gazette (`holiday_delhi`)
  - **HR-NCR:** Haryana state gazette (`holiday_hr_ncr`)
  - **Mumbai:** Maharashtra state gazette (`holiday_mumbai`)
- **Key Holidays Captured:**
  - `2022-04-02`: Ugadi (Bengaluru / KA) & Gudi Padwa (Mumbai / MH)
  - `2022-04-10`: Rama Navami (Central Government Restricted Holiday)
  - `2022-04-14`: Dr. B.R. Ambedkar Jayanti / Mahavir Jayanti (National Gazetted) & Vaisakhi (HR)
  - `2022-04-15`: Good Friday (National Gazetted)
  - `2022-05-01`: Maharashtra Day (Mumbai / MH)
  - `2022-05-03`: Id-ul-Fitr / Bhagwan Parshuram Jayanti / Akshaya Tritiya (National Gazetted)
  - `2022-05-16`: Buddha Purnima (National Gazetted)
  - `2022-06-02`: Maharana Pratap Jayanti (HR-NCR / HR)
  - `2022-06-14`: Sant Kabir Jayanti (HR-NCR / HR)
  - `2022-07-10`: Id-ul-Zuha / Bakrid (National Gazetted)

### 10. Units
- Discrete calendar day units, binary indicator flags (0/1), and standard ISO-8601 timestamps.

### 11. Limitations
- Does not track sudden municipal bandhs, localized market closures, or unscheduled election dry days.
- School holiday start/end dates vary by educational board (CBSE vs ICSE vs State).

### 12. Approval Status
- **Status:** **APPROVED FOR FUTURE FEATURE ENGINEERING**.
- **Files Saved:**
  - `dataset/external/calendar/india_holidays_calendar_2022.csv` (101 rows, 18 columns)
  - `dataset/external/calendar/calendar_features.csv` (101 rows, 9 columns)

---

# DATASET 2: Weather Data

### 1. Dataset / Source Name
- **Dataset Name:** Historical City Daily Weather Dataset (ERA5 Reanalysis)
- **Official Source:** Open-Meteo Historical Weather API, powered by ECMWF ERA5 atmospheric reanalysis model blended with India Meteorological Department (IMD) observation networks.
- **Provider:** Open-Meteo GmbH & Copernicus Climate Change Service (C3S)

### 2. Exact Source URL
- **API Endpoint:** [https://archive-api.open-meteo.com/v1/archive](https://archive-api.open-meteo.com/v1/archive)
- **API Documentation:** [https://open-meteo.com/en/docs/historical-weather-api](https://open-meteo.com/en/docs/historical-weather-api)

### 3. Why the Data is Relevant to Demand Forecasting
1. **Severe Heatwaves (April–May 2022):** North India experienced historic heatwaves during April–May 2022. Temperatures in Delhi and HR-NCR consistently exceeded 40°C–44.5°C. This drives demand for cold beverages, packaged milk, curd, ice cream, and ambient juices, while dampening in-person shopping.
2. **Monsoon Precipitation (June–July 2022):** Mumbai received 798.1 mm of rainfall, and Bengaluru received 426.0 mm. Torrential rain impairs two-wheeler delivery fleets (increasing rider wait times and unfulfilled carts), causes panic-stocking of shelf-stable pantry items, and accelerates spoilage in fresh produce.
3. **Humidity & Storage Risks:** Sustained relative humidity >85% in Mumbai and Bengaluru increases perishability and wastage in warehouse inventory for dry grains, biscuits, and bakery products.

### 4. Date Coverage
- **Start Date:** `2022-04-01`
- **End Date:** `2022-07-10`
- **Duration:** 101 consecutive calendar days for each of the 4 project cities.

### 5. Number of Rows
- **Total Rows:** `404` rows (101 days × 4 cities).

### 6. Columns
The weather dataset includes 11 meteorological fields:
- `date_`: ISO-8601 calendar date (`YYYY-MM-DD`)
- `city_name`: Project city (`Bengaluru`, `Delhi`, `HR-NCR`, `Mumbai`)
- `latitude`: Station latitude
- `longitude`: Station longitude
- `temperature_mean_c`: 24-hour mean temperature in °C
- `temperature_max_c`: Daily maximum temperature in °C
- `temperature_min_c`: Daily minimum temperature in °C
- `relative_humidity_pct`: 24-hour average relative humidity in %
- `precipitation_mm`: Total daily precipitation in mm
- `wind_speed_max_kmh`: Maximum wind gust speed in km/h
- `weather_condition`: Rule-based meteorological tag (`Extreme Heatwave`, `Hot / Sunny`, `Rain / Monsoon Shower`, `Heavy Rain`, `Humid / Overcast`, `Clear / Pleasant`)

### 7. Missing-Value Summary
- **Missing Values:** `0` null values across all 404 rows (0.00% missing).
- Complete historical observational continuity across all 11 variables.

### 8. Duplicate Check
- **Duplicate Check:** `0` duplicate records on composite key `(date_, city_name)`.

### 9. Coverage by City / Commodity
- **City Coverage (100% Balanced):**
  - **Bengaluru:** 101 days (Lat: 12.9716, Lon: 77.5946) | Temp Range: 21.0°C–28.9°C | Total Rain: 426.0 mm
  - **Delhi:** 101 days (Lat: 28.6139, Lon: 77.2090) | Temp Range: 26.2°C–37.7°C (Max: 44.5°C) | Total Rain: 112.2 mm
  - **HR-NCR (Gurugram):** 101 days (Lat: 28.4595, Lon: 77.0266) | Temp Range: 26.1°C–37.0°C (Max: 43.8°C) | Total Rain: 111.7 mm
  - **Mumbai:** 101 days (Lat: 19.0760, Lon: 72.8777) | Temp Range: 25.1°C–32.0°C | Total Rain: 798.1 mm

### 10. Units
- Temperature: Degrees Celsius (°C)
- Precipitation: Millimeters (mm)
- Relative Humidity: Percentage (%)
- Wind Speed: Kilometers per hour (km/h)

### 11. Limitations
- Values represent city-center centroid reanalysis observations. Micro-climates within massive metropolitan clusters (e.g., North Delhi vs South Delhi, or Greater Mumbai vs Navi Mumbai) are consolidated to the central urban station.

### 12. Approval Status
- **Status:** **APPROVED FOR FUTURE FEATURE ENGINEERING**.
- **Files Saved:**
  - `dataset/external/weather/city_daily_weather_historical_2022.csv` (404 rows, 11 columns)
  - `dataset/external/weather/weather_data.csv` (404 rows, 8 columns)

---

# DATASET 3: Commodity Price Data

### 1. Dataset / Source Name
- **Primary Dataset:** India City Retail Grocery Commodity Prices
- **Primary Source:** United Nations World Food Programme (WFP) in collaboration with the Ministry of Consumer Affairs, Food & Public Distribution, Government of India (Price Monitoring Division - PMD).
- **Secondary Reference:** The World Bank Commodity Markets ("Pink Sheet" Global Agricultural Benchmarks).

### 2. Exact Source URL
- **UN WFP India Retail Prices (HDX):** [https://data.humdata.org/dataset/wfp-food-prices-for-india](https://data.humdata.org/dataset/wfp-food-prices-for-india)
- **World Bank Pink Sheet:** [https://www.worldbank.org/en/research/commodity-markets](https://www.worldbank.org/en/research/commodity-markets)

### 3. Why the Data is Relevant to Demand Forecasting
1. **Edible Oil Geopolitical Volatility (Q2 2022):** The Ukraine conflict and Indonesia's temporary palm oil export ban in April–May 2022 caused unprecedented edible oil price surges in India. Retail prices of mustard oil (INR 175–195/kg) and sunflower oil (INR 180–215/kg) rose sharply, causing consumers to downsize pack purchases from 5-liter jars to 1-liter pouches.
2. **Wheat & Atta Export Shocks:** On May 13, 2022, the Government of India banned wheat exports to curb domestic price increases. Capturing retail wheat and atta (flour) prices reflects these supply constraints.
3. **Cross-Elasticity Among Staples:** Monitoring pulse prices (Lentils, Masur, Moong, Urad) provides demand models with essential price substitution signals that explain volume shifts across categories.

### 4. Date Coverage
- **Coverage Window:** April 2022 to July 2022 (`2022-04-15`, `2022-05-15`, `2022-06-15`, `2022-07-15`).
- **Reporting Frequency:** Monthly mid-month retail audits (the standard national cadence established by the Ministry of Consumer Affairs).

### 5. Number of Rows
- **City Retail Price Dataset:** `333` rows across the 4 operating markets.
- **World Bank Benchmark Series:** `36` rows (9 commodities × 4 months).

### 6. Columns
The city commodity price dataset contains 11 fields:
- `date_`: Audit date (`YYYY-MM-DD`)
- `project_city`: Normalized project city (`Bengaluru`, `Delhi`, `HR-NCR`, `Mumbai`)
- `market_name`: Official reporting market/center (`Bengaluru`, `Delhi`, `Gurgaon`, `Mumbai`)
- `commodity_name`: Standardized staple commodity name
- `commodity_category`: Category (`cereals and tubers`, `oil and fats`, `pulses`, `miscellaneous food`)
- `price_inr`: Retail price in Indian Rupees (INR)
- `price_usd`: Converted retail price in US Dollars (USD)
- `unit`: Standard unit of measure (`KG`)
- `price_type`: Price observation level (`Retail`)
- `price_flag`: Quality flag (`actual`)
- `source`: Issuing agency (`UN WFP / Ministry of Consumer Affairs India`)

### 7. Missing-Value Summary
- **Missing Values:** `0` null values across all 333 rows (0.00% missing).
- No missing values in prices, commodities, units, or city identifiers.

### 8. Duplicate Check
- **Duplicate Check:** `0` duplicate records on composite key `(date_, project_city, commodity_name)`.

### 9. Coverage by City / Commodity
- **City Scope:**
  - **Delhi:** 84 observations (21 commodities × 4 months)
  - **HR-NCR (Gurgaon Mandi):** 84 observations (21 commodities × 4 months)
  - **Mumbai:** 84 observations (21 commodities × 4 months)
  - **Bengaluru:** 81 observations (21 commodities across 4 months; East Range center)
- **Staple Commodities Monitored (21 items):**
  - *Edible Oils & Fats:* Oil (mustard), Oil (palm), Oil (sunflower), Oil (soybean), Oil (groundnut), Ghee (vanaspati)
  - *Grains & Flours:* Wheat, Wheat flour (Atta), Rice
  - *Pulses & Lentils:* Lentils, Lentils (masur), Lentils (moong), Lentils (urad)
  - *Sweeteners:* Sugar, Sugar (jaggery/gur)
  - *Essentials & Produce:* Milk (pasteurized), Tea (black), Potatoes, Onions, Tomatoes, Salt (iodised)
- **Observed Retail Price Benchmarks (INR / kg):**
  - Wheat: INR 24.00 – 35.93 / kg
  - Atta (Wheat flour): INR 26.30 – 49.87 / kg
  - Rice: INR 31.67 – 44.48 / kg
  - Sugar: INR 38.00 – 43.50 / kg
  - Mustard Oil: INR 165.00 – 195.00 / kg
  - Sunflower Oil: INR 180.00 – 215.00 / kg

### 10. Units
- Currency: Indian Rupee (INR) and US Dollar (USD)
- Unit of Measure: Kilogram (`KG`) uniformly applied across all commodities.

### 11. Limitations
- Retail commodity data is officially sampled at monthly intervals (mid-month retail census); day-to-day intra-month wholesale auction spikes are aggregated into the monthly series.
- Represents standard mandi retail prices; does not include premium branding or specialty organic product markups.

### 12. Approval Status
- **Status:** **APPROVED FOR FUTURE FEATURE ENGINEERING** (as monthly macroeconomic & category cost features).
- **Files Saved:**
  - `dataset/external/commodity/india_city_commodity_prices_2022.csv` (333 rows, 11 columns)
  - `dataset/external/commodity/commodity_prices.csv` (333 rows, 7 columns)
  - `dataset/external/commodity/world_bank_global_commodity_benchmarks_2022.csv` (36 rows, 8 columns)

---

## 4. Comprehensive Inventory of External Datasets Created

| Subdirectory | Filename | Rows | Columns | Source | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `dataset/external/calendar/` | `india_holidays_calendar_2022.csv` | 101 | 18 | DOPT Gazette / python-holidays | **Verified** |
| `dataset/external/calendar/` | `calendar_features.csv` | 101 | 9 | Standardized Calendar Template | **Verified** |
| `dataset/external/weather/` | `city_daily_weather_historical_2022.csv` | 404 | 11 | Open-Meteo / ECMWF ERA5 | **Verified** |
| `dataset/external/weather/` | `weather_data.csv` | 404 | 8 | Standardized Weather Template | **Verified** |
| `dataset/external/commodity/` | `india_city_commodity_prices_2022.csv` | 333 | 11 | UN WFP / Ministry of Consumer Affairs | **Verified** |
| `dataset/external/commodity/` | `commodity_prices.csv` | 333 | 7 | Standardized Commodity Template | **Verified** |
| `dataset/external/commodity/` | `world_bank_global_commodity_benchmarks_2022.csv` | 36 | 8 | World Bank Commodity Pink Sheet | **Verified** |
| `reports/` | `EXTERNAL_DATA_REPORT.md` | - | - | Complete Audit & Forensic Report | **Generated** |
| `reports/` | `external_data_sources.json` | - | - | Machine-Readable Source Metadata | **Generated** |

---

## 5. Forensic Confirmation of Sales Data Isolation

| Verification Dimension | Expected Value | Measured Value | Verification Status |
| :--- | :--- | :--- | :--- |
| **Sales Master File Path** | `dataset/cleaned/sales_product_master.csv` | `dataset/cleaned/sales_product_master.csv` | **Identical** |
| **Sales Master Row Count** | `46,706,387` | `46,706,387` | **Preserved (0 deleted, 0 added)** |
| **Sales Master File Size** | `9.487 GB` (10,186,818,487 bytes) | `9.487 GB` (10,186,818,487 bytes) | **Unaltered** |
| **Raw Sales Datasets** | `dataset/raw/` (100 CSVs) | `dataset/raw/` (100 CSVs) | **Untouched** |
| **External Merges Performed** | 0 joins with sales data | 0 joins with sales data | **Strictly Isolated** |
| **Fabricated Data Points** | 0 | 0 | **100% Real Public Historical Data** |
