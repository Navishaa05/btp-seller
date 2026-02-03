class Regulator:
    def __init__(self, min_quality: float = 0.0, min_bid: float = 0.0, reserve_cpc: float = 0.0):
        self.min_quality = min_quality
        self.min_bid = min_bid
        self.reserve_cpc = reserve_cpc

    def screen(self, bids, qs):
        m = (qs >= self.min_quality) & (bids >= self.min_bid)
        return bids * m, qs * m
