#!/usr/bin/env python3
"""Mechanical BIST 100 drawdown census and observable-entry backtest."""

from __future__ import annotations
import argparse, io
from pathlib import Path
import numpy as np
import pandas as pd
import requests

OLD_URL = "https://raw.githubusercontent.com/tuannasuhra/ec581/main/XU100.csv"
NEW_URL = "https://raw.githubusercontent.com/Ilkin22/BIST-Kriz-Analizi/main/Raw_Data_BIST%20100%20Historical%20Data.csv"
TRIGGERS = (0.10, 0.15, 0.20)
WEIGHTS = (0.25, 0.35, 0.40)

def read_text(src: str) -> str:
    p = Path(src)
    if p.exists():
        return p.read_text(encoding="utf-8-sig", errors="replace")
    r = requests.get(src, timeout=60)
    r.raise_for_status()
    return r.text

def load_old(src: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(read_text(src)), sep=";", header=None,
                     names=["Date","Open","High","Low","Close","Volume"], dtype=str)
    df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d", errors="coerce")
    for c in ["Open","High","Low","Close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce") / 100.0
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")
    return df.dropna(subset=["Date","High","Low","Close"])

def parse_volume(x):
    if pd.isna(x): return np.nan
    s = str(x).strip().replace(",", "")
    if not s or s == "-": return np.nan
    mult = 1.0
    if s.endswith("B"): mult, s = 1e9, s[:-1]
    elif s.endswith("M"): mult, s = 1e6, s[:-1]
    elif s.endswith("K"): mult, s = 1e3, s[:-1]
    try: return float(s) * mult
    except ValueError: return np.nan

def load_new(src: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(read_text(src)), dtype=str)
    df.columns = [c.strip().replace("\ufeff","") for c in df.columns]
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
    df = df.rename(columns={"Price":"Close","Vol.":"Volume"})
    for c in ["Open","High","Low","Close"]:
        df[c] = pd.to_numeric(df[c].str.replace(",","",regex=False), errors="coerce")
    df["Volume"] = df["Volume"].map(parse_volume)
    return df.dropna(subset=["Date","High","Low","Close"])

def load_supplement(path: str | None) -> pd.DataFrame:
    if not path:
        return pd.DataFrame(columns=["Date","Open","High","Low","Close","Volume"])
    df = pd.read_csv(path)
    for c in ["Open","Volume"]:
        if c not in df: df[c] = np.nan
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for c in ["Open","High","Low","Close","Volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["Date","High","Low","Close"])

def combine(*dfs) -> pd.DataFrame:
    parts=[]
    for priority,df in enumerate(dfs,1):
        z=df[["Date","Open","High","Low","Close","Volume"]].copy()
        z["_p"]=priority
        parts.append(z)
    out=pd.concat(parts,ignore_index=True)
    return (out.sort_values(["Date","_p"]).drop_duplicates("Date",keep="last")
            .sort_values("Date").drop(columns="_p").reset_index(drop=True))

def detect_drawdowns(p: pd.DataFrame, threshold: float) -> pd.DataFrame:
    rows=[]; peak_i=0; peak=float(p.loc[0,"Close"]); trough_i=0; falling=False
    def add(rec_i):
        nonlocal peak_i,peak,trough_i
        trough=float(p.loc[trough_i,"Close"]); dd=trough/peak-1
        if dd <= -threshold:
            rows.append(dict(peak_i=peak_i,peak_date=p.loc[peak_i,"Date"],peak_close=peak,
                             trough_i=trough_i,trough_date=p.loc[trough_i,"Date"],
                             trough_close=trough,max_drawdown=dd,recovery_i=rec_i,
                             peak_recovery_date=(pd.NaT if rec_i is None else p.loc[rec_i,"Date"]),
                             open_episode=(rec_i is None)))
    for i in range(1,len(p)):
        c=float(p.loc[i,"Close"])
        if not falling:
            if c >= peak:
                peak_i=i; peak=c; trough_i=i
            else:
                falling=True; trough_i=i
        else:
            if c < float(p.loc[trough_i,"Close"]): trough_i=i
            if c >= peak:
                add(i); peak_i=i; peak=c; trough_i=i; falling=False
    if falling: add(None)
    return pd.DataFrame(rows)

def first_idx(mask: pd.Series, start: int, end: int):
    x=mask.iloc[start:end+1]
    hits=x[x].index
    return None if len(hits)==0 else int(hits[0])

def apply_rules(p: pd.DataFrame, e: pd.DataFrame) -> pd.DataFrame:
    out=e.copy()
    for t in TRIGGERS:
        tag=f"d{int(t*100)}"
        levels=[]; fills=[]; days=[]; extra=[]
        for _,r in out.iterrows():
            level=float(r.peak_close)*(1-t)
            end=int(r.recovery_i) if pd.notna(r.recovery_i) else len(p)-1
            fill=first_idx(p["Low"]<=level,int(r.peak_i)+1,end)
            if fill is None:
                levels.append(level); fills.append(pd.NaT); days.append(np.nan); extra.append(np.nan); continue
            rec=first_idx(p["Close"]>=level,max(fill,int(r.trough_i)),end)
            levels.append(level); fills.append(p.loc[fill,"Date"])
            days.append(np.nan if rec is None else (p.loc[rec,"Date"]-p.loc[fill,"Date"]).days)
            extra.append(min(0.0,float(r.trough_close)/level-1))
        out[f"{tag}_level"]=levels
        out[f"{tag}_fill_date"]=fills
        out[f"{tag}_episode_days"]=days
        out[f"{tag}_extra_close_dd"]=extra

    dep=[]; cost=[]; last=[]; sdays=[]; sdd=[]; portdd=[]
    for _,r in out.iterrows():
        fills=[]
        for t,w in zip(TRIGGERS,WEIGHTS):
            tag=f"d{int(t*100)}"
            fd=r[f"{tag}_fill_date"]
            if pd.notna(fd):
                fills.append((w,float(r[f"{tag}_level"]),pd.Timestamp(fd)))
        if not fills:
            dep.append(0.0); cost.append(np.nan); last.append(pd.NaT); sdays.append(np.nan); sdd.append(np.nan); portdd.append(0.0); continue
        deployed=sum(w for w,_,_ in fills)
        avg=deployed/sum(w/px for w,px,_ in fills)
        lf=max(d for _,_,d in fills)
        lf_i=int(p.index[p["Date"]==lf][0])
        end=int(r.recovery_i) if pd.notna(r.recovery_i) else len(p)-1
        rec=first_idx(p["Close"]>=avg,max(lf_i,int(r.trough_i)),end)
        dd=min(0.0,float(r.trough_close)/avg-1)
        dep.append(deployed); cost.append(avg); last.append(lf)
        sdays.append(np.nan if rec is None else (p.loc[rec,"Date"]-lf).days)
        sdd.append(dd); portdd.append(deployed*dd)
    out["staged_capital_deployed"]=dep
    out["staged_avg_cost"]=cost
    out["staged_last_fill_date"]=last
    out["staged_episode_days"]=sdays
    out["staged_extra_close_dd"]=sdd
    out["staged_full_portfolio_trough_return"]=portdd
    return out

def summary(e: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    specs=[
        ("-10%","d10_fill_date","d10_episode_days","d10_extra_close_dd"),
        ("-15%","d15_fill_date","d15_episode_days","d15_extra_close_dd"),
        ("-20%","d20_fill_date","d20_episode_days","d20_extra_close_dd"),
        ("Staged","staged_last_fill_date","staged_episode_days","staged_extra_close_dd"),
    ]
    completed=e[~e.open_episode].copy()
    for name,fillc,dayc,ddc in specs:
        f=completed[completed[fillc].notna()]
        d=f[dayc].dropna()
        rows.append(dict(strategy=name,completed_episodes=len(completed),trades_filled=len(f),
                         fill_rate=len(f)/len(completed),mean_recovery_days=d.mean(),
                         median_recovery_days=d.median(),recovery_le_30=(d<=30).mean(),
                         recovery_le_90=(d<=90).mean(),recovery_le_180=(d<=180).mean(),
                         mean_extra_close_dd=f[ddc].mean(),worst_extra_close_dd=f[ddc].min()))
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--old-csv",default=OLD_URL)
    ap.add_argument("--new-csv",default=NEW_URL)
    ap.add_argument("--supplement")
    ap.add_argument("--out",default="results")
    ap.add_argument("--min-drawdown",type=float,default=0.10)
    args=ap.parse_args()

    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    prices=combine(load_old(args.old_csv),load_new(args.new_csv),load_supplement(args.supplement))
    episodes=apply_rules(prices,detect_drawdowns(prices,args.min_drawdown))
    episodes.to_csv(out/"all_drawdown_episodes.csv",index=False)
    summary(episodes).to_csv(out/"strategy_summary.csv",index=False)
    prices.to_csv(out/"merged_prices.csv",index=False)
    print(f"Rows: {len(prices):,} | {prices.Date.min().date()} to {prices.Date.max().date()}")
    print(f"Drawdowns >= {args.min_drawdown:.0%}: {len(episodes)}")
    print(summary(episodes).to_string(index=False))

if __name__=="__main__":
    main()
