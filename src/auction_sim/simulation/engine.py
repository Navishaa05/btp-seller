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
    
    clicks_acc = np.zeros(S)
    conv_acc = np.zeros(S)
    revenue_acc = np.zeros(S)
    ux_acc = 0.0
    platform_rev_acc = 0.0
    welfare_acc = 0.0
    
    # --- History Tracking ---
    history_logs = []
    log_interval = 1000 

    mech = w.mechanism
    reg = Regulator(w.regulation.min_quality, w.regulation.min_bid, w.regulation.reserve_cpc)

    for t in range(n):
        ctr_row = CTR[t]
        cvr_row = CVR[t]
        bids = np.zeros(S)
        elapsed = (ts[t] - w.start_ts) / (w.horizon_hours * 3600)
        
        # 1. ACT
        for i, s in enumerate(sellers):
            bid, _ = s.bid(p_ctr=ctr_row[i], p_cvr=cvr_row[i], elapsed_frac=elapsed)
            bids[i] = bid

        # 2. AUCTION
        qs = (ctr_row / ctr_row.max()) if ctr_row.max() > 0 else ctr_row + 1e-9
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
        
        # 3. USER SIMULATION
        lm = slot_m[: len(idx)]
        ctr_show = ctr_row[idx] * lm
        has_clicked = r.random(len(idx)) < ctr_show
        has_converted = (r.random(len(idx)) < cvr_row[idx]) & has_clicked
        pay = prices * has_clicked

        # 4. OBSERVE & UPDATE
        winners_map = {pos: j for j, pos in enumerate(idx)}
        for i, seller in enumerate(sellers):
            if i in winners_map:
                j = winners_map[i]
                seller.observe_and_adapt(has_clicked[j], has_converted[j], pay[j], elapsed)
                
                clicks_acc[i] += float(has_clicked[j])
                conv_acc[i] += float(has_converted[j])
                revenue_acc[i] += float(has_converted[j]) * seller.value_per_conversion
                welfare_acc += float(has_converted[j]) * seller.value_per_conversion
                platform_rev_acc += float(pay[j])
            else:
                seller.observe_and_adapt(0, 0, 0.0, elapsed)

        # 5. LOG SNAPSHOT (Page 3/4 metrics)
        if t % log_interval == 0:
            for s in sellers:
                history_logs.append({
                    "seller_id": s.id,
                    "policy": s.policy,
                    "elapsed_frac": elapsed,
                    "shading": s.base_bid_shading,
                    "spend": s.spend,
                    "roas": (s.revenue / s.spend) if s.spend > 0 else 0.0
                })

        ux_acc += ctr_show.mean() if len(idx) > 0 else 0.0

    data = {
        "seller_id": [s.id for s in sellers],
        "policy": [s.policy for s in sellers],
        "spend": [s.spend for s in sellers],
        "clicks": clicks_acc,
        "revenue": revenue_acc,
    }
    df_s = pd.DataFrame(data)
    df_s["roas"] = df_s["revenue"] / df_s["spend"].replace(0, np.nan)
    
    metrics = {
        "opportunities": n,
        "platform_revenue": platform_rev_acc,
        "social_welfare": welfare_acc,
        "user_experience": ux_acc / n if n > 0 else 0.0,
        "mechanism": mech,
        "slots": k,
        "reserve_cpc": w.regulation.reserve_cpc,
        "ts_start": int(ts0),
        "ts_end": int(ts0) + n,
    }
    
    return df_s, pd.DataFrame([metrics]), pd.DataFrame(history_logs)

def aggregate(results):
    sellers, metrics = [], []
    for s, m, _ in results:
        sellers.append(s)
        metrics.append(m)
    
    # 1. Sum up the raw counts first
    sf = pd.concat(sellers).groupby(["seller_id", "policy"], as_index=False).sum(numeric_only=True)
    # Recalculate ROAS correctly (Total Revenue / Total Spend)
    sf["roas"] = sf["revenue"] / sf["spend"].replace(0, np.nan)
    sf["surplus"] = sf["revenue"] - sf["spend"]
    
    # 2. Aggregate Global Metrics
    # Only sum numeric columns like revenue/welfare
    agg = pd.concat(metrics).sum(numeric_only=True).to_frame().T
    
    # 3. Restore static values (Don't sum slots or reserve prices)
    first_metric_df = results[0][1]
    agg["reserve_cpc"] = first_metric_df["reserve_cpc"].values[0]
    agg["slots"] = first_metric_df["slots"].values[0]
    agg["mechanism"] = first_metric_df["mechanism"].values[0]
    
    return sf, agg