import pandas as pd

def money(x):
    x = pd.to_numeric(x, errors='coerce')
    if isinstance(x, pd.Series):
        return x.apply(lambda v: "" if pd.isna(v) else f"${v:,.2f}" if v >= 0 else f"-${-v:,.2f}")
    if pd.isna(x):
        return ""
    return f"${x:,.2f}" if x >= 0 else f"-${-x:,.2f}"