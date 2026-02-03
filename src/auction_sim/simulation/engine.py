import numpy as np
import pandas as pd

from auction_sim.auction.mechanisms import allocate, prices_first_price, prices_gsp, prices_vcg
from auction_sim.auction.regulation import Regulator
from auction_sim.config import SimConfig
from auction_sim.market.sellers import make_sellers
from auction_sim.market.users import UserGenerator
from auction_sim.utils.features import sigmoid


def simulate_block(cfg: SimConfig, seed: int, start_offset: int):
    r = np.random.default_rng(seed)
    w = cfg.world
    ug = UserGenerator(
        w.embedding_dim, w.base_ctr, w.base_cvr, w.diurnal_amplitude, w.noise_std, seed
    )
    sellers = make_sellers(cfg, w.embedding_dim, seed + 1)
    k = w.slots
    slot_m = np.array(w.slot_multipliers[:k])
    ts0 = w.start_ts + start_offset
    n = w.batch_size
    u, ts, diurnal = ug.batch(n, ts0, w.horizon_hours)
    S = len(sellers)
    A = np.stack([s.ad_vec for s in sellers], axis=0)
    Q = u @ A.T
    Q = (Q - Q.mean()) / (Q.std() + 1e-6)
    CTR = sigmoid(Q) * w.base_ctr * diurnal.reshape(-1, 1)
    CVR = sigmoid(Q / 2) * w.base_cvr
    # spent = np.zeros(S)
    clicks = np.zeros(S)
    conv = np.zeros(S)
    revenue = np.zeros(S)
    ux_acc = 0.0
    rev_acc = 0.0
    welfare_acc = 0.0
    mech = w.mechanism
    reg = Regulator(w.regulation.min_quality, w.regulation.min_bid, w.regulation.reserve_cpc)
    for t in range(n):
        ctr_row = CTR[t]
        cvr_row = CVR[t]
        bids = np.zeros(S)
        qs = (ctr_row / ctr_row.max()) if ctr_row.max() > 0 else ctr_row + 1e-9
        elapsed = (ts[t] - w.start_ts) / (w.horizon_hours * 3600)
        for i, s in enumerate(sellers):
            bid, campaign = s.bid(
                p_ctr=ctr_row[i],
                p_cvr=cvr_row[i],
                elapsed_frac=elapsed,
            )

            if campaign is None:
                bids[i] = 0.0
            else:
                bids[i] = bid

        bids, qs = reg.screen(bids, qs)
        if mech == "first_price":
            idx, _ = allocate(bids, qs, k)
            prices = prices_first_price(bids, idx)
        elif mech == "vcg":
            idx, prices = prices_vcg(bids, qs, slot_m)
        else:
            idx, _ = allocate(bids, qs, k)
            prices = prices_gsp(bids, qs, idx)
        prices = np.maximum(prices, w.regulation.reserve_cpc)
        lm = slot_m[: len(idx)]
        ctr_show = ctr_row[idx] * lm
        click = r.random(len(idx)) < ctr_show
        conv_now = (r.random(len(idx)) < cvr_row[idx]) & click
        pay = prices * click
        for j, pos in enumerate(idx):
            seller = sellers[pos]
            seller.charge(pay[j], campaign=None)

            clicks[pos] += float(click[j])
            conv[pos] += float(conv_now[j])
            revenue[pos] += float(conv_now[j]) * seller.value_per_conversion

            welfare_acc += float(conv_now[j]) * sellers[pos].value_per_conversion
            rev_acc += float(pay[j])
        ux_acc += ctr_show.mean() if len(idx) > 0 else 0.0
    data = {
        "seller_id": [s.id for s in sellers],
        "cogs_ratio": [s.cogs_ratio for s in sellers],
        "spend": [s.spend for s in sellers],
        "clicks": clicks,
        "conversions": conv,
        "revenue": revenue,
    }
    df_s = pd.DataFrame(data)
    if w.metrics.roas_mode == "profit_over_spend":
        df_s["roas"] = df_s.apply(
            lambda r: ((r["revenue"] - r["spend"]) / r["spend"]) if r["spend"] > 0 else 0.0, axis=1
        )
    else:
        df_s["roas"] = df_s.apply(
            lambda r: (r["revenue"] / r["spend"]) if r["spend"] > 0 else 0.0, axis=1
        )
    if w.metrics.rocs_mode == "profit_after_cogs_over_spend":
        df_s["rocs"] = df_s.apply(
            lambda r: (((r["revenue"] * (1.0 - r["cogs_ratio"])) - r["spend"]) / r["spend"])
            if r["spend"] > 0
            else 0.0,
            axis=1,
        )
    else:
        df_s["rocs"] = df_s.apply(
            lambda r: (((r["revenue"] * (1.0 - r["cogs_ratio"])) - r["spend"]) / r["spend"])
            if r["spend"] > 0
            else 0.0,
            axis=1,
        )
    df_s["surplus"] = df_s["revenue"] - df_s["spend"]
    metrics = {
        "opportunities": n,
        "platform_revenue": rev_acc,
        "social_welfare": welfare_acc,
        "user_experience": ux_acc / n if n > 0 else 0.0,
        "mechanism": mech,
        "slots": k,
        "reserve_cpc": w.regulation.reserve_cpc,
        "ts_start": int(ts0),
        "ts_end": int(ts0) + n,
    }
    return df_s, pd.DataFrame([metrics])


def aggregate(results):
    sellers = []
    metrics = []
    for s, m in results:
        sellers.append(s)
        metrics.append(m)
    sf = (
        pd.concat(sellers, ignore_index=True)
        .groupby("seller_id", as_index=False)
        .sum(numeric_only=True)
    )
    tmp = pd.concat(metrics, ignore_index=True).sum(numeric_only=True)
    agg = tmp.to_frame().T
    return sf, agg
