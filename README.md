# Data Cleaning Pipeline Documentation

This document provides a comprehensive overview of the data cleaning process implemented in `data_cleaning_script.py`.

## Overview

The data cleaning pipeline standardizes and cleans raw CSV files containing project management data, converting inconsistent formats into clean, standardized datasets ready for analysis.

## Files Processed

| Raw File | Cleaned Output | Description |
|----------|----------------|-------------|
| `Projetos_raw.csv` | `Projetos_clean.csv` | Projects data with priorities, dates, and costs |
| `Custos_raw.csv` | `Custos_clean.csv` | Cost entries and financial data |
| `Horas_raw.csv` | `Horas_clean.csv` | Time tracking entries and work hours |
| `KPIs_raw.csv` | `KPIs_clean.csv` | KPIs and metrics data with mixed data types |

## Data Transformations Applied

### 1. Date Standardization
**Target Format:** `YYYY-MM-DD`

**Transformations:**
- Brazilian format: `20/02/26` → `2026-02-20`
- Mixed format: `2025-13-05` → `2025-05-13` (corrected invalid dates)
- Period format: `07.01.2026` → `2026-01-07`
- Day-month-year: `17-03-2026` → `2026-03-17`

**Features:**
- Invalid date detection and correction
- Multiple input format support
- Empty value preservation

### 2. Currency Cleaning
**Target Format:** Float values (e.g., `16591.06`)

**Transformations:**
- Brazilian format: `"R$ 16.591,06"` → `16591.06`
- US format: `"R$ 25,000.00"` → `25000.00`
- Simple format: `"24.811,04"` → `24811.04`
- Estimation annotations: `"R$ 20.916,29 (estim,)"` → `20916.29`

**Features:**
- Automatic format detection (Brazilian vs US)
- Typo corrections (`O`→`0`, `I`→`1`)
- Estimation annotation removal
- Thousands separator handling

### 3. Priority Standardization
**Target Format:** Lowercase without accents

**Transformations:**
- `"Média"` → `"media"` (accent removal)
- `"Baixa"` → `"baixa"` (lowercase conversion)
- `"Alta"` → `"alta"`
- `"Urgente"` → `"urgente"`
- `"BAIXA"` → `"baixa"` (case normalization)

**Features:**
- Accent character removal using Unicode normalization
- Case standardization
- Empty value preservation

### 4. Status Standardization
**Target Categories:** `critico`, `atrasado`, `em dia`, `pausado`

**Transformations:**
- Multiple language variations mapped to 4 standardized categories
- Accent removal from `"Crítico"` → `"critico"`
- Case normalization: `"EM DIA"` → `"em dia"`
- Status variations: `"On Hold"` → `"pausado"`

**Mapped Variations:**
- **Critical:** `critico`, `critical`, `critique`
- **Delayed:** `atrasado`, `delayed`
- **On Schedule:** `em dia`, `on schedule`, `on time`
- **Paused:** `pausado`, `on hold`, `em espera`, `aguardando`, `waiting`

### 5. Percentage Handling
**Target Format:** Integer percentages (e.g., `95%`)

**Transformations:**
- Currency to percentage: `"R$ 0,95"` → `"95%"`
- Decimal percentages: `"68,91"` → `"69%"`
- Existing percentages: `"90%"` → `"90%"`
- Percentage capping at 100%

**Features:**
- Currency-to-percentage conversion for KPIs
- Brazilian decimal format support
- Value capping to prevent over-100% values

### 6. Time Conversion
**Target Format:** Hours as decimal values

**Transformations:**
- Time format: `"3:30"` → `3.5` hours
- Decimal hours: `"2.08"` → `2.08` hours
- Brazilian decimal: `"3,6"` → `3.6` hours

### 7. Null Value Handling
**Target Format:** Empty strings for all null representations

**Transformations:**
- Pandas NaN values → `""` (empty string)
- String nulls: `"nan"`, `"null"`, `"none"`, `"n/a"` → `""`
- Empty values preserved as `""`
- Consistent behavior across all standardization methods

**Features:**
- Multi-layer null detection and conversion
- Post-processing safety net with `finalize_dataframe()`
- CSV export with `na_rep=''` parameter
- Validation to confirm clean outputs
- Comprehensive null pattern matching

### 8. Remote Work Standardization
**Target Format:** `s/n` (sim/não)

**Transformations:**
- Various boolean formats mapped to `s/n`
- Case and accent handling

## Implementation Details

### Core Methods

#### Standardization Methods
- `standardize_date()` - Date format standardization
- `standardize_currency()` - Currency cleaning and conversion
- `standardize_prioridade()` - Priority accent removal and lowercase
- `standardize_status()` - Status mapping to 4 categories
- `standardize_conclusao()` - Percentage handling for completion rates
- `standardize_meta()` - Mixed currency/percentage conversion for KPIs
- `convert_to_hours()` - Time format conversion
- `standardize_remote()` - Remote work boolean standardization

#### File Processing Methods
- `clean_projetos_raw()` - Processes project data
- `clean_custos_raw()` - Processes cost data
- `clean_horas_raw()` - Processes time tracking data
- `clean_kpis_raw()` - Processes KPIs and metrics data

#### Utility Methods
- `remove_accents()` - Unicode accent removal using NFD normalization
- `load_raw_data()` - CSV file loading with error handling
- `generate_quality_report()` - Comprehensive cleaning statistics
- `finalize_dataframe()` - Post-processing cleanup to remove all null values
- `validate_clean_output()` - Verification that cleaned dataframes have no null values

### Error Handling

The pipeline includes comprehensive error handling:
- **Invalid Dates:** Warning messages and empty value preservation
- **Parse Errors:** Graceful degradation with detailed warnings
- **Missing Files:** Continuation with error reporting
- **Format Issues:** Warning logs with problematic values

### Quality Reporting

Each cleaning operation generates detailed statistics:
- Total records processed
- Successfully standardized values by category
- Success rates
- Warnings and errors encountered

**Example Quality Report:**
```
File: Projetos_raw.csv
  Total Records: 36
  Dates Standardized: 68
  Conclusao Standardized: 18
  Currency Cleaned: 36
  Priority Lowercase: 36
  Status Lowercase: 36
  Success Rate: 100.0%
```

## Usage

### Running the Cleaning Pipeline

```bash
# Clean all CSV files
python data_cleaning_script.py

# Or if the script is in a different directory
python path/to/data_cleaning_script.py
```

### Output Structure

```
data/
├── csv/                    # Raw input files
│   ├── Projetos_raw.csv
│   ├── Custos_raw.csv
│   ├── Horas_raw.csv
│   └── KPIs_raw.csv
├── cleaned/                # Processed output files
│   ├── Projetos_clean.csv
│   ├── Custos_clean.csv
│   ├── Horas_clean.csv
│   └── KPIs_clean.csv
└── logs/                   # Quality reports
    ├── cleaning_report.txt
    └── detailed_warnings.log
```

## Data Flow

```
Raw CSV Files → Validation → Transformation → Standardization → Cleaned CSV Files
                                     ↓
                              Quality Reporting → Logs
```

### Transformation Pipeline per File

1. **Projetos_raw.csv:**
   - Priority: Accent removal + lowercase
   - Status: Mapping to 4 standardized categories
   - Dates: Multiple format standardization
   - Currency: Brazilian format cleaning

2. **Custos_raw.csv:**
   - Dates: Multiple format standardization
   - Currency: Brazilian format cleaning
   - Boolean fields: s/n standardization

3. **Horas_raw.csv:**
   - Dates: Multiple format standardization
   - Time: HH:MM to decimal hours conversion
   - Remote: Boolean standardization

4. **KPIs_raw.csv:**
   - Meta: Currency-to-percentage conversion
   - Mixed data type handling

## Technical Specifications

### Dependencies
- **pandas:** Data manipulation and CSV handling
- **re:** Regular expression pattern matching
- **unicodedata:** Unicode normalization for accent removal
- **pathlib:** Modern path handling
- **datetime:** Date parsing and validation

### Character Encoding
- **Input:** UTF-8 encoding expected
- **Output:** UTF-8 encoding enforced
- **Accent Handling:** Unicode NFD normalization

### Data Types
- **Dates:** String → datetime → String (YYYY-MM-DD)
- **Currency:** String → Float
- **Percentages:** Mixed → String (percentage format)
- **Booleans:** Mixed → String (s/n)

## Quality Assurance

### Validation Steps
1. **Format Detection:** Automatic identification of input formats
2. **Conversion Testing:** Each transformation tested with sample data
3. **Error Logging:** Comprehensive warning and error capture
4. **Data Integrity:** Preservation of non-empty valid values
5. **Null Value Verification:** Validation confirms no null values remain in cleaned files
6. **Multi-layer Safety:** Individual method checks + post-processing cleanup

### Known Limitations
- Invalid dates are converted to empty values
- Unrecognized formats trigger warnings but preserve data
- Very large datasets may require memory optimization

## Maintenance

### Adding New Transformations
1. Add new standardization method to `DataCleaner` class
2. Call method in appropriate `clean_*_raw()` function
3. Update quality reporting metrics
4. Test with sample data

### Extending to New Files
1. Create new `clean_*_raw()` method following existing pattern
2. Add to `run_all_cleaning()` workflow
3. Update documentation
4. Test integration

## Version History

- **v1.0:** Basic cleaning for Projetos, Custos, Horas
- **v1.1:** Added accent removal for priority column
- **v1.2:** Added KPIs cleaning with currency-to-percentage conversion
- **v1.3:** Comprehensive null value handling with multi-layer cleanup and validation

---

**Note:** This documentation reflects the current state of the data cleaning pipeline. For the most up-to-date information, refer to the source code and recent commit messages.