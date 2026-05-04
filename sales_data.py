from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DataConfig:
    seed: int = 42
    rows: int = 1200


REGIONS = ["North", "South", "East", "West"]
STATES = {
    "North": ["Delhi", "Punjab", "Haryana", "Uttarakhand"],
    "South": ["Karnataka", "Tamil Nadu", "Kerala", "Telangana"],
    "East": ["West Bengal", "Odisha", "Bihar", "Assam"],
    "West": ["Maharashtra", "Gujarat", "Rajasthan", "Goa"],
}
CATEGORIES = {
    "Technology": ["Laptop", "Tablet", "Headphones", "Smartphone", "Printer"],
    "Furniture": ["Office Chair", "Desk", "Bookshelf", "Dining Table", "Cabinet"],
    "Office Supplies": ["Paper", "Notebook", "Marker", "Pen Set", "Stapler"],
}
SEGMENTS = ["Consumer", "Corporate", "Home Office"]
CHANNELS = ["Online", "Retail", "Partner"]
SHIP_MODES = ["Standard", "Express", "Same Day"]


def _seasonality(month: int) -> float:
    return 1.0 + 0.18 * math.sin((month - 1) / 12 * 2 * math.pi) + (0.12 if month in {3, 11, 12} else 0.0)


def generate_sales_data(config: DataConfig = DataConfig()) -> pd.DataFrame:
    rng = np.random.default_rng(config.seed)

    dates = pd.date_range("2024-01-01", "2025-12-31", freq="D")
    date_choices = rng.choice(dates, size=config.rows, replace=True)
    date_choices = pd.to_datetime(date_choices)

    regions = rng.choice(REGIONS, size=config.rows, p=[0.27, 0.25, 0.20, 0.28])
    categories = rng.choice(list(CATEGORIES.keys()), size=config.rows, p=[0.42, 0.26, 0.32])
    segments = rng.choice(SEGMENTS, size=config.rows, p=[0.52, 0.28, 0.20])
    channels = rng.choice(CHANNELS, size=config.rows, p=[0.58, 0.28, 0.14])

    products = [rng.choice(CATEGORIES[category]) for category in categories]
    states = [rng.choice(STATES[region]) for region in regions]
    ship_modes = rng.choice(SHIP_MODES, size=config.rows, p=[0.56, 0.28, 0.16])

    base_price_map = {
        "Laptop": 1200,
        "Tablet": 650,
        "Headphones": 180,
        "Smartphone": 900,
        "Printer": 320,
        "Office Chair": 260,
        "Desk": 480,
        "Bookshelf": 210,
        "Dining Table": 720,
        "Cabinet": 350,
        "Paper": 18,
        "Notebook": 12,
        "Marker": 9,
        "Pen Set": 14,
        "Stapler": 16,
    }

    quantity = rng.integers(1, 8, size=config.rows)
    base_price = np.array([base_price_map[product] for product in products], dtype=float)
    month_factors = np.array([_seasonality(date.month) for date in date_choices])
    segment_factors = np.where(segments == "Corporate", 1.08, np.where(segments == "Home Office", 0.96, 1.0))
    channel_factors = np.where(channels == "Online", 0.97, np.where(channels == "Partner", 1.04, 1.0))

    price_noise = rng.normal(1.0, 0.08, size=config.rows)
    sales = base_price * quantity * month_factors * segment_factors * channel_factors * price_noise
    sales = np.round(np.maximum(sales, 8.0), 2)

    discount = np.clip(rng.normal(0.08, 0.06, size=config.rows), 0.0, 0.28)
    discount = np.where(categories == "Office Supplies", discount * 0.7, discount)
    discount = np.round(discount, 2)

    discounted_sales = sales * (1 - discount)
    margin_rate = np.where(categories == "Technology", 0.20, np.where(categories == "Furniture", 0.16, 0.24))
    profit_noise = rng.normal(0.0, 0.05, size=config.rows)
    profit = discounted_sales * (margin_rate + profit_noise) - rng.uniform(2, 18, size=config.rows)
    profit = np.round(profit, 2)

    customer_ids = [f"CUST-{n:05d}" for n in rng.integers(1000, 99999, size=config.rows)]
    order_ids = [f"ORD-{n:06d}" for n in range(1, config.rows + 1)]

    df = pd.DataFrame(
        {
            "order_id": order_ids,
            "order_date": date_choices,
            "customer_id": customer_ids,
            "region": regions,
            "state": states,
            "category": categories,
            "product_name": products,
            "segment": segments,
            "sales_channel": channels,
            "ship_mode": ship_modes,
            "quantity": quantity,
            "discount": discount,
            "sales": sales,
            "profit": profit,
        }
    )

    return df.sort_values("order_date").reset_index(drop=True)


def clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned.columns = [column.strip().lower() for column in cleaned.columns]
    cleaned["order_date"] = pd.to_datetime(cleaned["order_date"], errors="coerce")
    numeric_columns = ["quantity", "discount", "sales", "profit"]
    for column in numeric_columns:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    cleaned = cleaned.dropna(subset=["order_date", "sales", "profit", "category", "region", "product_name"])
    cleaned = cleaned[cleaned["sales"] > 0].copy()
    cleaned["month"] = cleaned["order_date"].dt.to_period("M").astype(str)
    cleaned["year"] = cleaned["order_date"].dt.year
    cleaned["order_value"] = cleaned["sales"] * (1 - cleaned["discount"].fillna(0))
    return cleaned


def load_sales_data(rows: int = 1200, seed: int = 42) -> pd.DataFrame:
    # Prefer a local CSV (e.g., a Kaggle export) placed in the `data/` folder.
    csv_path = _find_local_csv()
    if csv_path is not None:
        df = _load_csv(csv_path)
        if df is not None and not df.empty:
            return df

    # Fallback to synthetic generated data
    return clean_sales_data(generate_sales_data(DataConfig(seed=seed, rows=rows)))


def _find_local_csv() -> Optional[str]:
    data_dir = Path(__file__).parent / "data"
    if not data_dir.exists():
        return None
    candidates = sorted(data_dir.glob("*.csv"))
    return str(candidates[0]) if candidates else None


def _load_csv(path: str) -> Optional[pd.DataFrame]:
    try:
        df = pd.read_csv(path, parse_dates=["order_date"], infer_datetime_format=True)
        return clean_sales_data(df)
    except Exception:
        return None
