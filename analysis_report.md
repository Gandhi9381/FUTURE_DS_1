# Business Sales Performance Analysis Report

## Objective
Analyze sales data to identify revenue trends, top-selling products, high-value categories, and regional performance.

## Data Approach
- A realistic synthetic dataset was generated with order date, region, category, product, segment, discount, sales, and profit fields.
- The data was cleaned by standardizing column names, parsing dates, validating numeric fields, and removing incomplete records.
- KPIs were calculated for revenue, profit, order count, average order value, and profit margin.

## Key Insights
1. Revenue is uneven across the year, with clear monthly seasonality that can be used for campaign and inventory planning.
2. Technology and Furniture drive the most value, while Office Supplies usually contribute steadier low-ticket volume.
3. A small set of products accounts for a large share of revenue, so top sellers deserve priority in stock planning.
4. Regional performance is concentrated, with one or two regions leading overall sales and profit.
5. Discounting improves volume but can reduce profitability on lower-margin items.

## Recommendations
- Double down on the best-selling category with targeted bundles and cross-sell offers.
- Protect high-performing regions with better stock availability and localized marketing.
- Review pricing and discount rules for low-margin products.
- Track revenue monthly so the business can prepare for seasonal demand peaks.
- Build a recurring dashboard review process for leadership and sales teams.

## Deliverable
Run the Streamlit app to view the dashboard:

```bash
streamlit run app.py
```
