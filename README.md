# Python Calculator Demo

A collection of Python scripts that generate interactive HTML reports for mathematical computations.

## Projects

### 1. Calculator System (`calculator.py`)

A general-purpose calculator that evaluates mathematical expressions using Python's `math` module and outputs results to a styled HTML report.

**Features**
- Basic arithmetic: `+`, `-`, `*`, `/`, `%`, `**`
- Math functions: `sqrt`, `sin`, `cos`, `tan`, `log`
- Constants: `pi`, `e`
- Dark-themed HTML output with color-coded results

**Run**
```bash
python calculator.py
```
Output: `calculator_result.html`

---

### 2. Multiplication Table (`multiplication_table.py`)

Generates a fully-styled 9×9 multiplication table and renders it as an HTML page with a color-gradient heatmap.

**Features**
- 81-cell interactive table (hover to zoom)
- Blue gradient heatmap (light = small values, dark = large values)
- Summary stats: total cells, min/max value, sum of all products
- White background, clean modern UI

**Run**
```bash
python multiplication_table.py
```
Output: `multiplication_table.html`

---

## Requirements

- Python 3.x (no external packages required)
- A modern web browser to view HTML output

## File Structure

```
├── calculator.py              # Calculator script
├── calculator_result.html     # Calculator HTML output
├── multiplication_table.py    # Multiplication table script
├── multiplication_table.html  # Multiplication table HTML output
└── README.md
```

## Sample Output

| Script | Highlights |
|---|---|
| `calculator.py` | 15 operations including trig, log, sqrt |
| `multiplication_table.py` | 9×9 table, sum of all products = 2025 = 45² |
