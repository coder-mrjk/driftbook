"""Synthetic limit-order-book generator with deliberate regime shifts (so the project runs without live data)."""
import numpy as np, pandas as pd
def simulate(T=18000, shifts=(6000, 11000), seed=7):
    rng = np.random.default_rng(seed)
    reg = np.zeros(T, int); reg[shifts[0]:] = 1; reg[shifts[1]:] = 2
    beta = np.array([.25, -.4, .25])[reg]      # how strongly book imbalance predicts price (regime 1 flips sign)
    sig = np.array([.35, .56, .35])[reg]       # price noise
    sp = np.array([1, 2, 3])[reg] + rng.poisson(.2, T)   # spread in ticks
    imb = np.zeros(T)
    for t in range(1, T): imb[t] = .96 * imb[t-1] + .28 * rng.standard_normal()
    imb = np.tanh(imb)
    mid = 1000 + np.cumsum(beta * imb + sig * rng.standard_normal(T))
    b = rng.lognormal(3, .3, (T, 5)) * np.exp(.9 * imb[:, None] + .2 * rng.standard_normal((T, 5)))
    a = rng.lognormal(3, .3, (T, 5)) * np.exp(-.9 * imb[:, None] + .2 * rng.standard_normal((T, 5)))
    d = pd.DataFrame({'mid': mid, 'spread': sp, 'regime': reg})
    for i in range(5): d[f'b{i}'] = b[:, i]; d[f'a{i}'] = a[:, i]
    return d
