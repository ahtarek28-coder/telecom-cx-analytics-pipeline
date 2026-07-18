"""
Synthetic data generator for the telecom CX analytics pipeline demo.

Produces CSVs under data/raw/ that mirror the shape of real telecom CX
reporting sources: subscriber base, device location, network voice/data
performance, complaints, and churn labels. Each source is generated as of
its own reference date rather than a single shared "today" -- the same
multi-snapshot-alignment pattern documented in the data-engineering-skills
repo's KPI rollup write-up.
"""
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_SUBSCRIBERS = 5_000

END_DATE = date(2025, 6, 30)
BASE_SNAPSHOT_DATE = END_DATE - timedelta(days=60)  # subscriber base snapshot
NETWORK_SNAPSHOT_DATE = END_DATE  # latest network/usage snapshot
COMPLAINTS_START = END_DATE - timedelta(days=30)
COMPLAINTS_END = END_DATE
CHURN_SNAPSHOT_DATE = END_DATE - timedelta(days=30)

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

SCREEN_TYPES = ["Smartphone", "Feature Phone", "Tablet", "IoT Device"]
SCREEN_TYPE_WEIGHTS = [0.75, 0.05, 0.15, 0.05]
SEGMENTS = ["Mass", "High Value", "Youth", "SOHO"]
SITES = [f"SITE_{i:03d}" for i in range(1, 51)]
COMPLAINT_TYPES = ["Technical", "Billing", "Other"]
COMPLAINT_TYPE_WEIGHTS = [0.45, 0.35, 0.20]

rng = np.random.default_rng(SEED)


def make_msisdns(n):
    pool = np.arange(n * 3) + 10_000_000
    rng.shuffle(pool)
    return [f"9665{num}" for num in pool[:n]]


def gen_subscribers(msisdns):
    n = len(msisdns)
    subscription_age_days = rng.integers(1, 365 * 4, size=n)
    subscription_dates = [
        BASE_SNAPSHOT_DATE - timedelta(days=int(d)) for d in subscription_age_days
    ]
    return pd.DataFrame({
        "msisdn": msisdns,
        "dt": BASE_SNAPSHOT_DATE.isoformat(),
        "line_type": rng.choice(["PP", "PT"], size=n, p=[0.7, 0.3]),
        "line_subscription_date": subscription_dates,
        "screen_type": rng.choice(SCREEN_TYPES, size=n, p=SCREEN_TYPE_WEIGHTS),
        "p_segment": rng.choice(SEGMENTS, size=n),
        "arpu": rng.gamma(shape=2.0, scale=25, size=n).round(2),
        "voice_traffic": rng.gamma(shape=2.0, scale=120, size=n).round(1),
        "volte_success_ratio": rng.uniform(0.85, 0.999, size=n).round(4),
        "volte_drop_ratio": rng.uniform(0.001, 0.05, size=n).round(4),
    })


def gen_device_location(msisdns):
    n = len(msisdns)
    return pd.DataFrame({
        "msisdn": msisdns,
        "h09toh16_site": rng.choice(SITES, size=n),
        "h17toh00_site": rng.choice(SITES, size=n),
        "h01toh08_site": rng.choice(SITES, size=n),
    })


def gen_network_voice(msisdns, coverage=0.95):
    n = len(msisdns)
    covered = rng.random(n) < coverage
    df = pd.DataFrame({
        "msisdn": msisdns,
        "dt": NETWORK_SNAPSHOT_DATE.isoformat(),
        "call_success_ratio_2g": rng.uniform(0.9, 0.999, size=n).round(4),
        "call_drop_ratio_2g": rng.uniform(0.001, 0.03, size=n).round(4),
    })
    return df[covered].reset_index(drop=True)


def gen_network_data(msisdns, coverage=0.95):
    n = len(msisdns)
    covered = rng.random(n) < coverage
    # traffic stored in Kbit, matching the unit-conversion pitfall documented
    # in data-engineering-skills (divide by 8 * 1024**2 to get GB)
    df = pd.DataFrame({
        "msisdn": msisdns,
        "dt": NETWORK_SNAPSHOT_DATE.isoformat(),
        "data_traffic": rng.gamma(shape=2.0, scale=4_000_000, size=n).round(0),
        "dl_traffic_4g": rng.gamma(shape=2.0, scale=2_500_000, size=n).round(0),
        "dl_traffic_5g": rng.gamma(shape=1.5, scale=900_000, size=n).round(0),
        "dl_throughput_4g": rng.uniform(5, 80, size=n).round(2),
        "dl_throughput_5g": rng.uniform(50, 300, size=n).round(2),
    })
    return df[covered].reset_index(drop=True)


def gen_complaints(msisdns, complaint_rate=0.12):
    n = len(msisdns)
    n_complaints = int(n * complaint_rate)
    complainants = rng.choice(msisdns, size=n_complaints, replace=True)
    window_days = (COMPLAINTS_END - COMPLAINTS_START).days
    complaint_days = rng.integers(0, window_days + 1, size=n_complaints)
    dts = [
        (COMPLAINTS_START + timedelta(days=int(d))).isoformat() for d in complaint_days
    ]
    return pd.DataFrame({
        "msisdn": complainants,
        "dt": dts,
        "sr_classification": rng.choice(
            COMPLAINT_TYPES, size=n_complaints, p=COMPLAINT_TYPE_WEIGHTS
        ),
    })


def gen_churn_label(msisdns, churn_rate=0.08):
    n = len(msisdns)
    n_churned = int(n * churn_rate)
    churned_msisdns = rng.choice(msisdns, size=n_churned, replace=False)
    return pd.DataFrame({
        "msisdn": churned_msisdns,
        "dt": CHURN_SNAPSHOT_DATE.isoformat(),
    })


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    msisdns = make_msisdns(N_SUBSCRIBERS)

    tables = {
        "subscribers": gen_subscribers(msisdns),
        "device_location": gen_device_location(msisdns),
        "network_voice": gen_network_voice(msisdns),
        "network_data": gen_network_data(msisdns),
        "complaints": gen_complaints(msisdns),
        "churn_label": gen_churn_label(msisdns),
    }

    for name, df in tables.items():
        out_path = OUT_DIR / f"{name}.csv"
        df.to_csv(out_path, index=False)
        print(f"Wrote {len(df):,} rows to {out_path}")


if __name__ == "__main__":
    main()
