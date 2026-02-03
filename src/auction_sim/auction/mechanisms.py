import numpy as np


def allocate(bids, qs, k):
    s = bids * qs
    idx = np.argsort(-s)[:k]
    return idx, s[idx]


def prices_first_price(bids, idx):
    return bids[idx]


def prices_gsp(bids, qs, idx):
    s = bids * qs
    p = []
    for i, j in enumerate(idx):
        if i + 1 < len(idx):
            nxt = idx[i + 1]
            p.append(s[nxt] / max(qs[j], 1e-9))
        else:
            p.append(0.0)
    return np.array(p)


def prices_vcg(bids, qs, slot_m):
    k = len(slot_m)
    s = bids * qs
    order = np.argsort(-s)[:k]
    p = np.zeros(k)
    for i in range(k):
        den = max(qs[order[i]], 1e-9)
        num = 0.0
        for j in range(i + 1, k):
            num += s[order[j]] * (slot_m[j - 1] - slot_m[j])
        p[i] = num / den
    return order, p
