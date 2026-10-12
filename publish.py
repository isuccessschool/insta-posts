"""Instagram auto-publisher (Instagram API with Instagram Login). Runs every 15 min via GitHub Actions.
Env: IG_TOKEN, IG_USER_ID, IMG_BASE (e.g. https://raw.githubusercontent.com/USER/REPO/main/images). DRY_RUN=1 to test."""
import json,os,sys,time,datetime as dt,urllib.request,urllib.parse
IST=dt.timezone(dt.timedelta(hours=5,minutes=30))
G="https://graph.instagram.com/v21.0"
DRY=os.environ.get("DRY_RUN")=="1"
MAX_LATE_H=4
def api(path,params=None,post=False):
    p=dict(params or {}); p["access_token"]=os.environ.get("IG_TOKEN","")
    data=urllib.parse.urlencode(p).encode()
    url=G+path if post else G+path+"?"+urllib.parse.urlencode(p)
    try:
        with urllib.request.urlopen(urllib.request.Request(url,data=data if post else None),timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e: raise RuntimeError(e.read().decode())
def wait(cid):
    for _ in range(30):
        s=api(f"/{cid}",{"fields":"status_code"}).get("status_code")
        if s=="FINISHED": return
        if s in("ERROR","EXPIRED"): raise RuntimeError("container "+s)
        time.sleep(5)
    raise RuntimeError("container timeout")
def publish(p):
    uid=os.environ["IG_USER_ID"]; base=os.environ["IMG_BASE"].rstrip("/")
    kids=[]
    for k in range(1,p["images"]+1):
        r=api(f"/{uid}/media",{"image_url":f"{base}/{p['path']}/{k:02d}.jpg","is_carousel_item":"true"},True)
        kids.append(r["id"])
    for c in kids: wait(c)
    r=api(f"/{uid}/media",{"media_type":"CAROUSEL","children":",".join(kids),"caption":p["caption"]},True)
    wait(r["id"])
    return api(f"/{uid}/media_publish",{"creation_id":r["id"]},True)["id"]
def main():
    posts=json.load(open("schedule.json"))   # made by make_schedule.py
    state=json.load(open("state.json")) if os.path.exists("state.json") else {}
    now=dt.datetime.now(IST); changed=False
    for p in posts:
        if p["id"] in state: continue
        t=dt.datetime.fromisoformat(p["publish_at"])
        if t>now: continue
        if (now-t).total_seconds()>MAX_LATE_H*3600:
            state[p["id"]]="missed (too late)"; changed=True; print("MISSED",p["id"]); continue
        if DRY: print("DRY-RUN would publish",p["id"],p["publish_at"],p["images"],"slides"); continue
        try:
            mid=publish(p); state[p["id"]]="posted "+mid; changed=True; print("POSTED",p["id"],mid)
        except Exception as e:
            print("FAILED",p["id"],e); state[p["id"]]="failed: "+str(e)[:200]; changed=True
        break   # one post per run keeps it safe
    if changed: json.dump(state,open("state.json","w"),indent=1)
main()
