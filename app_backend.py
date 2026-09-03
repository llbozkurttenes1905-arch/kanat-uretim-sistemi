from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import json, os, uuid
from datetime import datetime, date, timedelta

app = FastAPI(title="ERGUNBAS Kanat Uretim Sistemi")
DATA_FILE  = "data_kanat.json"
USERS_FILE = "users.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"orders": {}, "machines": {}, "daily_entries": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def load_users():
    if not os.path.exists(USERS_FILE):
        default = {
            "u1": {"id": "u1", "username": "admin", "password": "ergunbas2026", "role": "admin", "name": "Sistem Yöneticisi"},
            "u2": {"id": "u2", "username": "operator1", "password": "operator1", "role": "operator", "name": "Kanat Operatörü 1"},
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(u):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(u, f, ensure_ascii=False, indent=2)

class OrderCreate(BaseModel):
    order_no: str
    facility_id: str
    customer: str
    model: str
    qty: int
    delivery_date: str
    notes: Optional[str] = ""

class OrderUpdate(BaseModel):
    facility_id: Optional[str] = None
    customer: Optional[str] = None
    model: Optional[str] = None
    qty: Optional[int] = None
    delivery_date: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class MachineCreate(BaseModel):
    name: str
    facility_id: str
    stage: str
    capacity_per_hour: Optional[float] = 0
    notes: Optional[str] = ""

class MachineUpdate(BaseModel):
    name: Optional[str] = None
    facility_id: Optional[str] = None
    stage: Optional[str] = None
    capacity_per_hour: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class OrderEntry(BaseModel):
    order_id: str
    output_qty: int = 0
    shift: Optional[str] = ""
    operator: Optional[str] = ""
    notes: Optional[str] = ""

class MachineEntry(BaseModel):
    machine_id: str
    output_qty: int = 0
    work_hours: float = 0
    operator: Optional[str] = ""
    notes: Optional[str] = ""

class DailyPayload(BaseModel):
    date: str
    order_entries: List[OrderEntry] = []
    machine_entries: List[MachineEntry] = []

class DowntimeEntry(BaseModel):
    machine_id: str
    reason: str
    duration_min: float = 0
    notes: Optional[str] = ""

class DailyDowntime(BaseModel):
    date: str
    downtimes: List[DowntimeEntry] = []

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "operator"
    name: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

@app.post("/api/auth/login")
def login(req: LoginRequest):
    users = load_users()
    for uid, u in users.items():
        if u["username"] == req.username and u["password"] == req.password:
            return {"status": "success", "user": {k: v for k, v in u.items() if k != "password"}}
    raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")

@app.get("/api/users")
def list_users():
    return [{"id": u["id"], "username": u["username"], "role": u["role"], "name": u["name"]} for u in load_users().values()]

@app.post("/api/users")
def create_user(req: UserCreate):
    users = load_users()
    for u in users.values():
        if u["username"] == req.username:
            raise HTTPException(400, "Bu kullanıcı adı zaten mevcut")
    uid = f"u{len(users)+1}_{req.username[:3]}"
    users[uid] = {"id": uid, "username": req.username, "password": req.password, "role": req.role, "name": req.name}
    save_users(users)
    return {"id": uid, "status": "ok"}

@app.put("/api/users/{uid}")
def update_user(uid: str, req: UserUpdate):
    users = load_users()
    if uid not in users:
        raise HTTPException(404, "Kullanıcı bulunamadı")
    if req.name: users[uid]["name"] = req.name
    if req.password: users[uid]["password"] = req.password
    if req.role: users[uid]["role"] = req.role
    save_users(users)
    return {"status": "ok"}

@app.delete("/api/users/{uid}")
def delete_user(uid: str):
    if uid == "u1":
        raise HTTPException(400, "Sistem yöneticisi silinemez")
    users = load_users()
    if uid not in users:
        raise HTTPException(404, "Kullanıcı bulunamadı")
    del users[uid]
    save_users(users)
    return {"status": "ok"}


@app.get("/api/facilities")
def get_facilities():
    d = load_data()
    f1 = d.get("facilities", {}).get("fac1", {"id": "fac1", "name": "Üst Tesis"})
    f2 = d.get("facilities", {}).get("fac2", {"id": "fac2", "name": "Alt Tesis"})
    return [f1, f2]

@app.put("/api/facilities/{fid}")
def update_facility(fid: str, payload: dict):
    d = load_data()
    if "facilities" not in d: d["facilities"] = {}
    if fid not in d["facilities"]: d["facilities"][fid] = {"id": fid}
    d["facilities"][fid]["name"] = payload.get("name", "Bilinmeyen Tesis")
    save_data(d)
    return {"status": "ok"}

@app.get("/api/orders")
def list_orders(facility_id: Optional[str] = None):
    d = load_data()
    orders = list(d["orders"].values())
    daily = d.get("daily_entries", {})
    today_dt = date.today()
    
    res = []
    for order in orders:
        if facility_id and facility_id != "all" and order.get("facility_id") != facility_id:
            continue
            
        oid = order["id"]
        total_out = 0
        
        # Calculate produced qty directly from order_entries
        for day_data in daily.values():
            for oe in day_data.get("order_entries", []):
                if oe.get("order_id") == oid:
                    total_out += oe.get("output_qty", 0)
                            
        order["produced_qty"] = total_out
        order["remaining_qty"] = max(0, order.get("qty",0) - total_out)
        order["progress_pct"] = round(total_out / order.get("qty",1) * 100, 1) if order.get("qty",0) > 0 else 0
        
        try:
            deliv_dt = date.fromisoformat(order.get("delivery_date", ""))
            days_rem = (deliv_dt - today_dt).days
            order["days_remaining"] = days_rem
            if order.get("status") == "open":
                if days_rem < 0:
                    order["spillover_status"] = "delayed"
                    order["delay_days"] = abs(days_rem)
                elif days_rem <= 7:
                    order["spillover_status"] = "critical"
                    order["delay_days"] = 0
                else:
                    order["spillover_status"] = "on_track"
                    order["delay_days"] = 0
            else:
                order["spillover_status"] = "completed"
                order["delay_days"] = 0
        except:
            order["days_remaining"] = None
            order["spillover_status"] = "unknown"
            order["delay_days"] = 0
            
        res.append(order)
            
    res.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return res

@app.post("/api/orders")
def create_order(req: OrderCreate):
    d = load_data()
    oid = "SIP-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    d["orders"][oid] = {
        "id": oid,
        "facility_id": req.facility_id,
        "order_no": req.order_no,
        "customer": req.customer,
        "model": req.model,
        "qty": req.qty,
        "delivery_date": req.delivery_date,
        "status": "open",
        "notes": req.notes or "",
        "created_at": datetime.now().isoformat()
    }
    save_data(d)
    return {"id": oid, "status": "ok"}

@app.put("/api/orders/{oid}")
def update_order(oid: str, req: OrderUpdate):
    d = load_data()
    if oid not in d["orders"]:
        raise HTTPException(404, "Sipariş bulunamadı")
    o = d["orders"][oid]
    for k, v in req.dict(exclude_none=True).items():
        o[k] = v
    save_data(d)
    return {"status": "ok"}

@app.delete("/api/orders/{oid}")
def delete_order(oid: str):
    d = load_data()
    if oid not in d["orders"]:
        raise HTTPException(404, "Sipariş bulunamadı")
    del d["orders"][oid]
    save_data(d)
    return {"status": "ok"}

@app.get("/api/orders/{oid}")
def get_order(oid: str):
    d = load_data()
    if oid not in d["orders"]:
        raise HTTPException(404, "Sipariş bulunamadı")
    return d["orders"][oid]

@app.get("/api/machines")
def list_machines(facility_id: Optional[str] = None):
    d = load_data()
    machines = list(d["machines"].values())
    if facility_id and facility_id != "all":
        machines = [m for m in machines if m.get("facility_id") == facility_id]
    return machines

@app.post("/api/machines")
def create_machine(req: MachineCreate):
    d = load_data()
    mid = "MCH-" + str(uuid.uuid4())[:8].upper()
    d["machines"][mid] = {
        "id": mid,
        "facility_id": req.facility_id,
        "name": req.name,
        "stage": req.stage,
        "capacity_per_hour": req.capacity_per_hour,
        "status": "active",
        "notes": req.notes or "",
        "created_at": datetime.now().isoformat()
    }
    save_data(d)
    return {"id": mid, "status": "ok"}

@app.put("/api/machines/{mid}")
def update_machine(mid: str, req: MachineUpdate):
    d = load_data()
    if mid not in d["machines"]:
        raise HTTPException(404, "Makine bulunamadı")
    for k, v in req.dict(exclude_none=True).items():
        d["machines"][mid][k] = v
    save_data(d)
    return {"status": "ok"}

@app.delete("/api/machines/{mid}")
def delete_machine(mid: str):
    d = load_data()
    if mid not in d["machines"]:
        raise HTTPException(404, "Makine bulunamadı")
    del d["machines"][mid]
    save_data(d)
    return {"status": "ok"}

@app.get("/api/daily/{date_key}")
def get_daily(date_key: str):
    d = load_data()
    return d.get("daily_entries", {}).get(date_key, {"date": date_key, "order_entries": [], "machine_entries": [], "downtimes": []})

@app.post("/api/daily/{date_key}")
def save_daily(date_key: str, payload: DailyPayload):
    d = load_data()
    if date_key not in d.setdefault("daily_entries", {}):
        d["daily_entries"][date_key] = {"date": date_key, "order_entries": [], "machine_entries": [], "downtimes": []}
    
    # Overwrite the day's order and machine entries for simplicity, or append (here we just update existing ones, but since UI sends full payload, we overwrite them or merge. Wait, UI usually sends incremental data if it's not careful. Let's merge based on order/machine/shift)
    
    # Simpler: The UI will just append entries.
    for oe in payload.order_entries:
        d["daily_entries"][date_key]["order_entries"].append(oe.dict())
    
    for me in payload.machine_entries:
        d["daily_entries"][date_key]["machine_entries"].append(me.dict())
        
    save_data(d)
    return {"status": "ok"}

@app.post("/api/daily/{date_key}/downtime")
def save_downtime(date_key: str, payload: DailyDowntime):
    d = load_data()
    if date_key not in d.setdefault("daily_entries", {}):
        d["daily_entries"][date_key] = {"date": date_key, "order_entries": [], "machine_entries": [], "downtimes": []}
    
    for dt in payload.downtimes:
        d["daily_entries"][date_key].setdefault("downtimes", []).append(dt.dict())
    
    save_data(d)
    return {"status": "ok"}

@app.get("/api/dashboard")
def dashboard(facility_id: Optional[str] = "all", period: Optional[str] = "weekly", target_date: Optional[str] = None):
    d = load_data()
    orders = d.get("orders", {})
    machines = d.get("machines", {})
    daily = d.get("daily_entries", {})
    today_dt = date.today()
    today_str = today_dt.isoformat()
    
    start_dt = today_dt
    end_dt = today_dt
    
    if period == "daily":
        if target_date:
            try: start_dt = date.fromisoformat(target_date)
            except: pass
        end_dt = start_dt
    elif period == "weekly":
        start_dt = today_dt - timedelta(days=today_dt.weekday())
        end_dt = start_dt + timedelta(days=6)
    elif period == "monthly":
        if target_date:
            try: start_dt = date.fromisoformat(target_date).replace(day=1)
            except: start_dt = today_dt.replace(day=1)
        else:
            start_dt = today_dt.replace(day=1)
        # simplistic end of month
        nxt = start_dt.replace(day=28) + timedelta(days=4)
        end_dt = nxt - timedelta(days=nxt.day)
        
    # Helper to check if a date string falls in our range
    def in_range(ds):
        try:
            dt = date.fromisoformat(ds)
            return start_dt <= dt <= end_dt
        except:
            return False

    # Orders Summary
    total_orders = 0
    open_orders = 0
    done_orders = 0
    sarkan = []
    
    for oid, o in orders.items():
        if facility_id and facility_id != "all" and o.get("facility_id") != facility_id:
            continue
            
        total_orders += 1
        if o.get("status") == "open": open_orders += 1
        else: done_orders += 1
        
        if o.get("status") == "open":
            try:
                deliv_dt = date.fromisoformat(o["delivery_date"])
                days_rem = (deliv_dt - today_dt).days
                
                if days_rem <= 7:
                    # calc produced qty
                    t_out = sum(oe.get("output_qty",0) for dd in daily.values() for oe in dd.get("order_entries",[]) if oe.get("order_id") == oid)
                    kalan = max(0, o.get("qty",0) - t_out)
                    sarkan.append({
                        "id": oid,
                        "order_no": o.get("order_no", ""),
                        "facility_name": o.get("facility_id", ""),
                        "customer": o.get("customer", ""),
                        "model": o.get("model", ""),
                        "qty": o.get("qty", 0),
                        "produced_qty": t_out,
                        "remaining_qty": kalan,
                        "delivery_date": o.get("delivery_date", ""),
                        "days_left": days_rem,
                        "delay_days": abs(days_rem) if days_rem < 0 else 0
                    })
            except:
                pass
                
    # Calculate period output
    total_out_period = 0
    fac1_out = 0
    fac2_out = 0
    
    # For orders output
    for dk, dd in daily.items():
        if not in_range(dk): continue
        for oe in dd.get("order_entries", []):
            oid = oe.get("order_id")
            o = orders.get(oid, {})
            f_id = o.get("facility_id")
            if facility_id and facility_id != "all" and f_id != facility_id:
                continue
            
            qty = oe.get("output_qty", 0)
            total_out_period += qty
            if f_id == "fac1": fac1_out += qty
            elif f_id == "fac2": fac2_out += qty

    # For weekly days chart (always weekly, or daily if requested)
    days_arr = []
    curr = start_dt
    while curr <= end_dt:
        ds = curr.isoformat()
        dd = daily.get(ds, {})
        d_out = 0
        for oe in dd.get("order_entries", []):
            o = orders.get(oe.get("order_id"), {})
            if facility_id and facility_id != "all" and o.get("facility_id") != facility_id:
                continue
            d_out += oe.get("output_qty", 0)
        days_arr.append({
            "date": ds,
            "day_name": ["Pzt","Sal","Çar","Per","Cum","Cmt","Paz"][curr.weekday()] if period == "weekly" else str(curr.day),
            "is_today": ds == today_str,
            "output": d_out
        })
        curr += timedelta(days=1)

    # Machine Performance
    mach_stats = {}
    for dk, dd in daily.items():
        if not in_range(dk): continue
        for me in dd.get("machine_entries", []):
            mid = me.get("machine_id")
            m = machines.get(mid, {})
            if facility_id and facility_id != "all" and m.get("facility_id") != facility_id:
                continue
            
            if mid not in mach_stats:
                mach_stats[mid] = {"id": mid, "name": m.get("name", mid), "output": 0, "hours": 0}
            
            mach_stats[mid]["output"] += me.get("output_qty", 0)
            mach_stats[mid]["hours"] += me.get("work_hours", 0)

    ms_list = []
    for ms in mach_stats.values():
        eff = round(ms["output"] / ms["hours"], 1) if ms["hours"] > 0 else ms["output"]
        ms["efficiency"] = eff
        ms_list.append(ms)
        
    ms_list.sort(key=lambda x: x["output"], reverse=True)

    return {
        "orders": {"total": total_orders, "open": open_orders, "done": done_orders},
        "period_summary": {
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat(),
            "total_output": total_out_period,
            "days": days_arr,
            "fac1_output": fac1_out,
            "fac2_output": fac2_out
        },
        "sarkan_siparisler": sarkan,
        "machine_stats": ms_list
    }

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_backend:app", host="0.0.0.0", port=8001, reload=True)
