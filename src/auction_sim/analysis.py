import numpy as np
import pandas as pd
from scipy import stats


def compare(run_a: str, run_b: str):
    sa = pd.read_parquet(f"{run_a}/sellers.parquet")
    sb = pd.read_parquet(f"{run_b}/sellers.parquet")
    mm = []
    for k in ["spend", "clicks", "conversions", "revenue", "roas", "rocs", "surplus"]:
        a = sa[k].values
        b = sb[k].values
        t, p = stats.ttest_ind(a, b, equal_var=False)
        mm.append(
            {
                "metric": k,
                "mean_a": float(np.mean(a)),
                "mean_b": float(np.mean(b)),
                "delta": float(np.mean(b) - np.mean(a)),
                "pvalue": float(p),
            }
        )
    return pd.DataFrame(mm)
