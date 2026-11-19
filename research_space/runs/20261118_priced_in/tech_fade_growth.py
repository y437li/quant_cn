"""Fade vs constant growth: first-year growth g0 with growth decaying x0.7 a year over 10 years, exit PE 15, 9% discount; implied 2028 exit PE on consensus FY2028 (inputs from tech_implied_growth.py)."""
import numpy as np
r=0.09
def val(p,g0,h,exit_pe,yrs=10):
    v,x,g=0,p,g0
    for t in range(1,yrs+1):
        x*=1+g; v+=x/(1+r)**t; g*=h
    return v+exit_pe*x/(1+r)**yrs
def solve(mv,p,h,exit_pe):
    lo,hi=-0.5,5.0
    if val(p,hi,h,exit_pe)<mv: return np.nan
    for _ in range(100):
        m=(lo+hi)/2; lo,hi=(m,hi) if val(p,m,h,exit_pe)<mv else (lo,m)
    return lo
D=[("中际旭创","高点",15416,149.5,751,"20260622"),("中际旭创","现在",4629,259,990,"20261117"),("新易盛","高点",8512,107.4,511,"20260625"),("新易盛","现在",2232,145.8,559,"20261117"),
("工业富联","高点",16084,406.5,1016,"20260603"),("工业富联","现在",7124,531.7,1028,"20261117"),("兆易创新","高点",5895,28.7,85,"20260629"),("兆易创新","现在",1510,116.3,196,"20261117"),
("寒武纪","高点",10025,27.2,159,"20260630"),("寒武纪","现在",5690,41.7,219,"20261117"),("海光信息","高点",8607,27.3,90,"20260630"),("海光信息","现在",4242,34.3,90,"20261117")]
print("name when | const g (exit15) | fade h=0.7: g0, yr5 g, profit x10y | implied 2028 exit PE on consensus")
for n,w,mv,ttm,c28,d in D:
    gc=solve(mv,ttm,1.0,15); g0=solve(mv,ttm,0.7,15)
    gs=[g0*0.7**t for t in range(10)]; mult=np.prod([1+x for x in gs])
    yrs=(2028.99-(int(d[:4])+int(d[4:6])/12))
    pe28=mv*(1+r)**yrs/c28
    print(f"{n} {w} | {gc*100:4.0f}% | g0 {g0*100:4.0f}%, yr5 {gs[4]*100:3.0f}%, x{mult:4.1f} | {pe28:5.1f}")
