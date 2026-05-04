# Business Sales Performance Analytics

Client-ready sales analysis project built with Python and Streamlit.

## What It Does
- Cleans and structures sales data
- Analyzes revenue trends over time
- Identifies top-selling products
- Highlights high-value categories
- Compares regional performance
- Surfaces business recommendations for decision-makers

## Files
- [app.py](app.py) - launcher that starts the dashboard with Streamlit
- [dashboard.py](dashboard.py) - Streamlit dashboard
- [sales_data.py](sales_data.py) - synthetic dataset generator and cleaning logic
- [analysis_report.md](analysis_report.md) - written summary of insights and recommendations
- [requirements.txt](requirements.txt) - dependencies

## Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the dashboard:
   ```bash
   python app.py
   ```

Optional launcher flags:

```bash
python app.py --port 8502
python app.py --no-browser
```

## Using a Kaggle / Real Sales CSV
To use a real Sales or Retail dataset (for example from Kaggle), download the CSV and place it in the project's `data/` folder. The dashboard will automatically load the first CSV it finds and fall back to the synthetic generator if none are present.

- Recommended Kaggle datasets: search for "Retail Sales" or "Store Sales" on Kaggle and download the CSV export.
- Place the file at `data/your_sales_file.csv`.

Then run the app as above; the dashboard caption shows which data file is being used.

## Suggested Submission Text
"I built a business sales performance dashboard that analyzes revenue trends, top-selling products, high-value categories, and regional performance. The project includes data cleaning, KPI analysis, interactive visualizations, and actionable recommendations for business growth."

## Notes
The dataset in this project is synthetic and generated for demonstration. You can replace it with a real CSV export from a business, online store, or ERP system without changing the dashboard logic.

If you prefer, you can also launch it directly with:

```bash
streamlit run dashboard.py
```
