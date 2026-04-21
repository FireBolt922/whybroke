"""Demo bug #2: pandas KeyError on a column the developer renamed last week.

Run:  python scripts/demo_bugs/02_pandas_keyerror.py 2>&1 | whybroke
"""

import pandas as pd


def load_events() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "event_id": [1, 2, 3],
            "user_id": [101, 102, 103],
            "timestamp": ["2026-04-01", "2026-04-02", "2026-04-03"],
        }
    )


def summarise(df: pd.DataFrame) -> pd.Series:
    # BUG: column was renamed from "user" to "user_id" — this raises KeyError.
    return df.groupby("user").size()


if __name__ == "__main__":
    df = load_events()
    print(summarise(df))
