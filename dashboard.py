from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

import sales_data as sd
from models import train_forecast_model


st.set_page_config(
    page_title="Sales Performance Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False)
def get_data() -> pd.DataFrame:
    return sd.load_sales_data(rows=1400, seed=42)


def get_data_source() -> str:
    csv = getattr(sd, "_find_local_csv", lambda: None)()
    return Path(csv).name if csv is not None else "synthetic (generator)"


def money(value: float) -> str:
    return f"${value:,.0f}"


def pct(value: float) -> str:
    return f"{value:.1f}%"


df = get_data()

with st.sidebar:
    st.title("Filters")
    min_date = df["order_date"].min().date()
    max_date = df["order_date"].max().date()
    selected_dates = st.date_input("Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    regions = st.multiselect("Region", options=sorted(df["region"].unique()), default=sorted(df["region"].unique()))
    categories = st.multiselect("Category", options=sorted(df["category"].unique()), default=sorted(df["category"].unique()))
    segments = st.multiselect("Segment", options=sorted(df["segment"].unique()), default=sorted(df["segment"].unique()))

if isinstance(selected_dates, tuple):
    start_date, end_date = selected_dates
else:
    start_date = end_date = selected_dates

filtered = df[
    (df["order_date"].dt.date >= start_date)
    & (df["order_date"].dt.date <= end_date)
    & (df["region"].isin(regions))
    & (df["category"].isin(categories))
    & (df["segment"].isin(segments))
].copy()

if filtered.empty:
    st.warning("No data matches the current filters. Expand the date range or select more categories and regions.")
    st.stop()

filtered["month_label"] = filtered["order_date"].dt.to_period("M").astype(str)
filtered["profit_margin"] = (filtered["profit"] / filtered["order_value"].replace(0, pd.NA)).fillna(0.0)

total_sales = filtered["sales"].sum()
total_profit = filtered["profit"].sum()
orders = filtered["order_id"].nunique()
avg_order_value = filtered["order_value"].mean()
order_value_sum = filtered["order_value"].sum()
margin = (total_profit / order_value_sum) if order_value_sum else 0.0

top_product = filtered.groupby("product_name", as_index=False)["sales"].sum().sort_values("sales", ascending=False).iloc[0]
top_category = filtered.groupby("category", as_index=False)["sales"].sum().sort_values("sales", ascending=False).iloc[0]
top_region = filtered.groupby("region", as_index=False)["sales"].sum().sort_values("sales", ascending=False).iloc[0]

monthly = filtered.groupby("month_label", as_index=False)[["sales", "profit"]].sum().sort_values("month_label")
category_perf = filtered.groupby("category", as_index=False)[["sales", "profit"]].sum().sort_values("sales", ascending=False)
region_perf = filtered.groupby("region", as_index=False)[["sales", "profit"]].sum().sort_values("sales", ascending=False)

st.title("Business Sales Performance Dashboard")
st.caption("Revenue trends, top-selling products, high-value categories, and regional performance in one client-ready view.")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Revenue", money(total_sales))
col2.metric("Profit", money(total_profit))
col3.metric("Orders", f"{orders:,}")
col4.metric("Avg. Order Value", money(avg_order_value))
col5.metric("Profit Margin", pct(margin * 100))

st.write("")

left, right = st.columns([1.6, 1.0])

with left:
    revenue_chart = px.line(
        monthly,
        x="month_label",
        y="sales",
        markers=True,
        title="Revenue Trend Over Time",
        labels={"month_label": "Month", "sales": "Revenue"},
    )
    revenue_chart.update_traces(line=dict(color="#17324d", width=4), marker=dict(size=8, color="#d97706"))
    revenue_chart.update_layout(height=430, template="plotly_white", margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(revenue_chart, width="stretch")

    # Forecast section
    with st.expander("Forecasting", expanded=False):
        st.write("Train a simple RandomForest model on monthly sales and forecast future revenue.")
        horizon = st.slider("Forecast horizon (months)", 1, 12, 3)
        n_lags = st.selectbox("Lag months to use", [1, 3, 6], index=1)
        train = st.button("Train Forecast Model")

        if train:
            with st.spinner("Training forecast model..."):
                # prepare monthly data for model
                monthly_for_model = monthly.rename(columns={"month_label": "ds", "sales": "y"})
                monthly_for_model["ds"] = pd.to_datetime(monthly_for_model["ds"] + "-01")
                try:
                    result = train_forecast_model(monthly_for_model, horizon_months=horizon, n_lags=n_lags)
                    fc = result.forecast
                    metrics = result.metrics

                    fig = px.line(
                        fc,
                        x="ds",
                        y=["y", "y_pred"],
                        labels={"ds": "Month", "value": "Revenue", "variable": "Series"},
                        title="Historical vs Forecast",
                    )
                    fig.update_traces(mode="lines+markers")
                    st.plotly_chart(fig, use_container_width=True)

                    st.write("Model performance on holdout:")
                    st.write(f"MAE: {metrics['mae']:.2f}, RMSE: {metrics['rmse']:.2f}")
                except Exception as exc:  # pragma: no cover - runtime guard
                    st.error(f"Forecasting failed: {exc}")

with right:
    insight_items = [
        f"Top product: {top_product['product_name']} ({money(top_product['sales'])})",
        f"Best category: {top_category['category']} ({money(top_category['sales'])})",
        f"Leading region: {top_region['region']} ({money(top_region['sales'])})",
        f"Margin health: {pct(margin * 100)} overall profit margin",
    ]
    st.subheader("Quick Insights")
    for item in insight_items:
        st.markdown(f"- {item}")
    st.subheader("Actionable View")
    st.info(
        "Focus on the highest-margin product-category pairs, protect the strongest region with inventory planning, and target discount-heavy products for pricing review."
    )

bottom_left, bottom_right = st.columns(2)

with bottom_left:
    category_chart = px.bar(
        category_perf,
        x="category",
        y="sales",
        color="profit",
        color_continuous_scale=["#fde68a", "#f59e0b", "#17324d"],
        title="Sales by Category",
        labels={"category": "Category", "sales": "Revenue", "profit": "Profit"},
    )
    category_chart.update_layout(height=420, template="plotly_white", margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(category_chart, width="stretch")

with bottom_right:
    region_chart = px.bar(
        region_perf,
        x="region",
        y="sales",
        color="profit",
        color_continuous_scale=["#dbeafe", "#60a5fa", "#17324d"],
        title="Regional Performance",
        labels={"region": "Region", "sales": "Revenue", "profit": "Profit"},
    )
    region_chart.update_layout(height=420, template="plotly_white", margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(region_chart, width="stretch")

st.subheader("Top 10 Products")
product_table = filtered.groupby(["product_name", "category"], as_index=False)[["sales", "profit", "quantity"]].sum().sort_values("sales", ascending=False).head(10)
product_table["margin"] = (product_table["profit"] / product_table["sales"]).round(3)
st.dataframe(
    product_table.rename(
        columns={
            "product_name": "Product",
            "category": "Category",
            "sales": "Revenue",
            "profit": "Profit",
            "quantity": "Units Sold",
            "margin": "Margin",
        }
    ),
    width="stretch",
    hide_index=True,
)

export_df = filtered.copy()
export_df["order_date"] = export_df["order_date"].dt.strftime("%Y-%m-%d")
st.download_button(
    "Download filtered data (CSV)",
    data=export_df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_sales_data.csv",
    mime="text/csv",
)

st.subheader("Business Recommendations")
recommendations = [
    f"Scale {top_category['category']} through inventory and bundle offers because it contributes the highest revenue share.",
    f"Prioritize {top_region['region']} for regional campaigns, since it is the strongest market in this period.",
    "Review pricing and discount rules for low-margin products to improve profitability without sacrificing volume.",
    "Use monthly trend monitoring to plan stock and marketing budgets around seasonal demand spikes.",
]
for recommendation in recommendations:
    st.markdown(f"- {recommendation}")

data_source = get_data_source()
st.caption(f"Data source: {data_source}. To use a Kaggle dataset, place the CSV into the `data/` folder.")
