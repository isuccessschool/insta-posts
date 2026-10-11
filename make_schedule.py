"""python3 make_schedule.py 2026-10-14   -> day 1 of posts goes on that date"""
import json,sys,datetime as dt
start=dt.date.fromisoformat(sys.argv[1]); P=json.load(open("posts.json"))
for p in P:
    d=start+dt.timedelta(days=p["day"]-1)
    p["publish_at"]=f"{d.isoformat()}T{p['time']}:00+05:30"
json.dump(P,open("schedule.json","w"),ensure_ascii=False,indent=1); print("ok",P[0]["publish_at"],"->",P[-1]["publish_at"])
