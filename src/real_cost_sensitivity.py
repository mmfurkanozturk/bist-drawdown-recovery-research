#!/usr/bin/env python3
"""Inflation-adjusted breakeven and transaction-cost sensitivity helpers."""

from __future__ import annotations
import argparse, io
from pathlib import Path
import numpy as np
import pandas as pd
import requests

FRED_CPI = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CP0000TRM086NEST"
TRIGGERS=(0.10,0.15,0.20)
WEIGHTS=(0.25,0.35,0.40)

def load_cpi(url: str = FRED_CPI) -> pd.Series:
    r=requests.get(url,timeout=60); r.raise_for_status()
    df=pd.read_csv(io.StringIO(r.text))
    df["DATE"]=pd.to_datetime(df["DATE"],errors="coerce")
    df["CP0000TRM086NEST"]=pd.to_numeric(df["CP0000TRM086NEST"],errors="coerce")
    df=df.dropna()
    return df.set_index(df["DATE"].dt.to_period("M"))["CP0000TRM086NEST"]

def cpi_for(ts, cpi):
    return float(cpi.loc[pd.Timestamp(ts).to_period("M")])

def single_real_recovery(prices, fill_date, entry, trough_date, fee, cpi):
    fill_i=int(prices.index[prices.Date==pd.Timestamp(fill_date)][0])
    trough_i=int(prices.index[prices.Date==pd.Timestamp(trough_date)][0])
    entry_cpi=cpi_for(fill_date,cpi)
    units=1/(entry*(1+fee))
    for i in range(max(fill_i,trough_i),len(prices)):
        proceeds=units*prices.loc[i,"Close"]*(1-fee)
        if proceeds/cpi_for(prices.loc[i,"Date"],cpi) >= 1/entry_cpi:
            return prices.loc[i,"Date"], (prices.loc[i,"Date"]-pd.Timestamp(fill_date)).days
    return pd.NaT, np.nan

def staged_real_recovery(prices, fills, trough_date, fee, cpi):
    fills=[x for x in fills if pd.notna(x[2])]
    if not fills: return pd.NaT,np.nan
    shares=[]; real_outflow=0.0
    last=max(pd.Timestamp(x[2]) for x in fills)
    for w,price,date in fills:
        shares.append(w/(price*(1+fee)))
        real_outflow += w/cpi_for(date,cpi)
    trough_i=int(prices.index[prices.Date==pd.Timestamp(trough_date)][0])
    start=max(int(prices.index[prices.Date==last][0]),trough_i)
    for i in range(start,len(prices)):
        proceeds=sum(q*prices.loc[i,"Close"]*(1-fee) for q in shares)
        if proceeds/cpi_for(prices.loc[i,"Date"],cpi) >= real_outflow:
            return prices.loc[i,"Date"], (prices.loc[i,"Date"]-last).days
    return pd.NaT,np.nan

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--prices",default="results/merged_prices.csv")
    ap.add_argument("--episodes",default="results/all_drawdown_episodes.csv")
    ap.add_argument("--out",default="results/real_cost_sensitivity.csv")
    args=ap.parse_args()

    prices=pd.read_csv(args.prices,parse_dates=["Date"])
    eps=pd.read_csv(args.episodes,parse_dates=["peak_date","trough_date",
        "d10_fill_date","d15_fill_date","d20_fill_date","staged_last_fill_date"])
    cpi=load_cpi()

    rows=[]
    for fee in [0,0.0005,0.001,0.0025]:
        for _,r in eps[~eps.open_episode].iterrows():
            for t in TRIGGERS:
                tag=f"d{int(t*100)}"
                fd=r.get(f"{tag}_fill_date")
                if pd.isna(fd): continue
                level=float(r.peak_close)*(1-t)
                rd,days=single_real_recovery(prices,fd,level,r.trough_date,fee,cpi)
                rows.append(dict(fee_per_side=fee,strategy=tag,peak_date=r.peak_date,
                                 fill_date=fd,real_recovery_date=rd,real_recovery_days=days))
            fills=[
                (0.25,float(r.peak_close)*0.90,r.get("d10_fill_date")),
                (0.35,float(r.peak_close)*0.85,r.get("d15_fill_date")),
                (0.40,float(r.peak_close)*0.80,r.get("d20_fill_date")),
            ]
            rd,days=staged_real_recovery(prices,fills,r.trough_date,fee,cpi)
            rows.append(dict(fee_per_side=fee,strategy="staged",peak_date=r.peak_date,
                             fill_date=r.staged_last_fill_date,real_recovery_date=rd,
                             real_recovery_days=days))
    out=pd.DataFrame(rows)
    Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    out.to_csv(args.out,index=False)
    print(out.groupby(["fee_per_side","strategy"]).real_recovery_days.agg(["count","mean","median"]))

if __name__=="__main__":
    main()
