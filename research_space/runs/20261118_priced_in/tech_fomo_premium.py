"""FOMO premium: market cap over a fundamental value built from consensus FY2026-28 (at that date),
growth after 2028 starting at the FY27->28 consensus growth and fading x0.7 a year to 2035, exit PE
15 in 2035, 9% discount, earnings treated as distributable (generous: no capex deduction)."""
r,H,EXIT=0.09,0.7,15
D=[("中际旭创",2026.47,15416,300,563,751,2026.88,4629,336,657,990),
   ("新易盛",2026.48,8512,184,292,511,2026.88,2232,193,379,559),
   ("工业富联",2026.42,16084,614,834,1016,2026.88,7124,606,846,1028),
   ("兆易创新",2026.49,5895,56,69,85,2026.88,1510,140,177,196),
   ("寒武纪",2026.49,10025,53,103,159,2026.88,5690,55,125,219),
   ("海光信息",2026.49,8607,44,65,90,2026.88,4242,43,67,90),
   ("中芯国际",2026.52,14810,68,81,94,2026.88,9714,92,119,148),
   ("北方华创",2026.50,6788,72,104,135,2026.88,4140,70,111,147)]
def value(t0,c26,c27,c28,h=H,exit_pe=EXIT):
    prof={2026:c26,2027:c27,2028:c28}; g=c28/c27-1; x=c28
    for y in range(2029,2036): g*=h; x*=1+g; prof[y]=x
    v=0
    for y,p in prof.items():
        t=(y+1.0)-t0  # profit received at year end
        if y==2026: p=p*max(0,(2027-t0))  # only the remaining part of 2026
        v+=p/(1+r)**t
    return v+exit_pe*prof[2035]/(1+r)**(2036-t0)
print("name | peak cap, fair, premium | now cap, fair, premium | fair with no fade (h=1, exit 25) at peak")
for n,t0,mv,a,b,c,t1,mv1,a1,b1,c1 in D:
    f0=value(t0,a,b,c); f1=value(t1,a1,b1,c1); fhi=value(t0,a,b,c,h=1.0,exit_pe=25)
    print(f"{n} | {mv:6.0f} {f0:6.0f} {mv/f0*100-100:+5.0f}% | {mv1:6.0f} {f1:6.0f} {mv1/f1*100-100:+5.0f}% | {fhi:7.0f} ({mv/fhi*100-100:+.0f}%)")
