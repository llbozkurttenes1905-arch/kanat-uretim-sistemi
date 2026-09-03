from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import json, os, uuid, calendar
from datetime import datetime, date, timedelta

app = FastAPI(title="ERGUNBAS Kanat Uretim Sistemi")
DATA_FILE  = "data_kanat.json"
USERS_FILE = "users.json"

DEFAULT_FACILITIES = {
    "fac1": {"id": "fac1", "name": "Üst Tesis (Ana Fabrika)"},
    "fac2": {"id": "fac2", "name": "Alt Tesis (2. Fabrika)"},
}

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"orders": {}, "machines": {}, "daily_entries": {}, "facilities": dict(DEFAULT_FACILITIES)}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    if "facilities" not in d or not d["facilities"]:
        d["facilities"] = dict(DEFAULT_FACILITIES)
    return d

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
    customer: str
    model: str
    qty: int
    delivery_date: str
    stages: List[str] = []
    notes: Optional[str] = ""

class OrderUpdate(BaseModel):
    customer: Optional[str] = None
    model: Optional[str] = None
    qty: Optional[int] = None
    delivery_date: Optional[str] = None
    stages: Optional[List[str]] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class MachineCreate(BaseModel):
    name: str
    stage: str
    capacity_per_hour: Optional[float] = 0
    notes: Optional[str] = ""

class MachineUpdate(BaseModel):
    name: Optional[str] = None
    stage: Optional[str] = None
    capacity_per_hour: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class StageEntry(BaseModel):
    stage: str
    machine_id: Optional[str] = ""
    output_qty: int = 0
    work_hours: Optional[float] = 0
    notes: Optional[str] = ""

class DailyOrderEntry(BaseModel):
    order_id: str
    shift: str
    operator: Optional[str] = ""
    stage_entries: List[StageEntry] = []

class DailyPayload(BaseModel):
    date: str
    entries: List[DailyOrderEntry] = []

class DowntimeEntry(BaseModel):
    machine_id: Optional[str] = ""
    stage: Optional[str] = ""
    reason: str
    duration_min: float = 0
    notes: Optional[str] = ""

class DailyDowntime(BaseModel):
    date: str
    downtimes: List[DowntimeEntry] = []

class FacilityUpdate(BaseModel):
    name: str

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
def list_facilities():
    d = load_data()
    return list(d["facilities"].values())

@app.put("/api/facilities/{fid}")
def update_facility(fid: str, req: FacilityUpdate):
    d = load_data()
    if fid not in d["facilities"]:
        d["facilities"][fid] = {"id": fid, "name": req.name}
    else:
        d["facilities"][fid]["name"] = req.name
    save_data(d)
    return {"status": "ok"}

@app.get("/api/orders")
def list_orders(facility_id: Optional[str] = Query(None)):
    d = load_data()
    orders = list(d["orders"].values())
    if facility_id and facility_id != "all":
        orders = [o for o in orders if (o.get("facility_id") or "fac1") == facility_id]
    daily = d.get("daily_entries", {})
    today_dt = date.today()
    
    for order in orders:
        oid = order["id"]
        total_out = 0
        stages = order.get("stages", [])
        last_stage = stages[-1] if stages else None
        
        for day_data in daily.values():
            for entry in day_data.get("entries", []):
                if entry["order_id"] == oid:
                    for se in entry.get("stage_entries", []):
                        if last_stage and se["stage"] == last_stage:
                            total_out += se.get("output_qty", 0)
                        elif not stages:
                            total_out += se.get("output_qty", 0)
                            
        order["produced_qty"] = total_out
        order["remaining_qty"] = max(0, order["qty"] - total_out)
        order["progress_pct"] = round(total_out / order["qty"] * 100, 1) if order["qty"] > 0 else 0
        
        try:
            deliv_dt = date.fromisoformat(order["delivery_date"])
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
            
    orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return orders

@app.post("/api/orders")
def create_order(req: OrderCreate):
    d = load_data()
    oid = "SIP-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    d["orders"][oid] = {
        "id": oid,
        "order_no": req.order_no,
        "customer": req.customer,
        "model": req.model,
        "qty": req.qty,
        "delivery_date": req.delivery_date,
        "stages": req.stages,
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
    prev_status = o.get("status")
    for k, v in req.dict(exclude_none=True).items():
        o[k] = v
    # "Sevkiyata Hazır" (done) olarak işaretlendiğinde tarihi otomatik kaydet;
    # yeniden açılırsa temizle — haftalık sevkiyat grafiği bu alanı kullanır.
    if req.status == "done" and prev_status != "done":
        o["ready_date"] = date.today().isoformat()
    elif req.status == "open":
        o["ready_date"] = None
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

DAY_NAMES_TR = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

@app.get("/api/orders/shipment-ready")
def shipment_ready_summary(facility_id: Optional[str] = Query(None), target_date: Optional[str] = Query(None)):
    """Bu hafta (veya seçilen haftada) 'Sevkiyata Hazır' olarak işaretlenen siparişlerin
    güne göre dağılımı — paketleme aşamasından çıkan siparişleri haftalık olarak gösterir."""
    d = load_data()
    orders = list(d["orders"].values())
    if facility_id and facility_id != "all":
        orders = [o for o in orders if (o.get("facility_id") or "fac1") == facility_id]

    try:
        ref_date = date.fromisoformat((target_date or date.today().isoformat())[:10])
    except Exception:
        ref_date = date.today()
    start_of_week = ref_date - timedelta(days=ref_date.weekday())

    by_date = {}
    for o in orders:
        rd = o.get("ready_date")
        if rd:
            by_date.setdefault(rd, []).append(o)

    days = []
    total_orders = 0
    total_qty = 0
    for i in range(7):
        cur_day = start_of_week + timedelta(days=i)
        cur_str = cur_day.isoformat()
        day_orders = by_date.get(cur_str, [])
        day_qty = sum(o.get("qty", 0) for o in day_orders)
        total_orders += len(day_orders)
        total_qty += day_qty
        days.append({
            "date": cur_str,
            "day_name": DAY_NAMES_TR[i],
            "is_today": cur_str == date.today().isoformat(),
            "order_count": len(day_orders),
            "qty": day_qty,
            "orders": [{"order_no": o.get("order_no"), "customer": o.get("customer"), "qty": o.get("qty", 0), "facility_id": o.get("facility_id") or "fac1"} for o in day_orders]
        })

    return {
        "start_date": start_of_week.isoformat(),
        "end_date": (start_of_week + timedelta(days=6)).isoformat(),
        "total_orders": total_orders,
        "total_qty": total_qty,
        "days": days
    }

@app.get("/api/orders/{oid}")
def get_order(oid: str):
    d = load_data()
    if oid not in d["orders"]:
        raise HTTPException(404, "Sipariş bulunamadı")
    return d["orders"][oid]

@app.get("/api/machines")
def list_machines(facility_id: Optional[str] = Query(None)):
    machines = list(load_data()["machines"].values())
    if facility_id and facility_id != "all":
        machines = [m for m in machines if (m.get("facility_id") or "fac1") == facility_id]
    return machines

@app.get("/api/machines/work-hours/{date_key}")
def machine_work_hours(date_key: str, facility_id: Optional[str] = Query(None)):
    """Belirli bir gün için makine bazında çalışma saati ve üretim adedi."""
    d = load_data()
    machines = d.get("machines", {})
    day_data = d.get("daily_entries", {}).get(date_key, {})
    agg = {}
    for entry in day_data.get("entries", []):
        for se in entry.get("stage_entries", []):
            mid = se.get("machine_id") or ""
            if not mid:
                continue
            m = machines.get(mid)
            if facility_id and facility_id != "all":
                m_fac = (m.get("facility_id") or "fac1") if m else "fac1"
                if m_fac != facility_id:
                    continue
            if mid not in agg:
                agg[mid] = {
                    "machine_id": mid,
                    "name": m.get("name", mid) if m else mid,
                    "stage": m.get("stage", "") if m else "",
                    "facility_id": (m.get("facility_id") or "fac1") if m else "fac1",
                    "capacity_per_hour": m.get("capacity_per_hour", 0) if m else 0,
                    "work_hours": 0.0,
                    "output_qty": 0,
                }
            agg[mid]["work_hours"] += se.get("work_hours") or 0
            agg[mid]["output_qty"] += se.get("output_qty") or 0

    # Include machines with zero activity that day, so the chart shows the full fleet
    for mid, m in machines.items():
        if facility_id and facility_id != "all" and (m.get("facility_id") or "fac1") != facility_id:
            continue
        if mid not in agg:
            agg[mid] = {
                "machine_id": mid,
                "name": m.get("name", mid),
                "stage": m.get("stage", ""),
                "facility_id": m.get("facility_id") or "fac1",
                "capacity_per_hour": m.get("capacity_per_hour", 0),
                "work_hours": 0.0,
                "output_qty": 0,
            }

    result = list(agg.values())
    for r in result:
        r["work_hours"] = round(r["work_hours"], 2)
        cap = r.get("capacity_per_hour") or 0
        r["efficiency_pct"] = round((r["output_qty"] / (cap * r["work_hours"]) * 100), 1) if cap and r["work_hours"] else 0
    result.sort(key=lambda x: x["work_hours"], reverse=True)
    return {"date": date_key, "machines": result}

@app.get("/api/machines/production-summary")
def machine_production_summary(facility_id: Optional[str] = Query(None), period: Optional[str] = Query("daily"), target_date: Optional[str] = Query(None)):
    """Makine bazında, seçilen döneme (günlük/haftalık/aylık) göre toplam çalışma saati ve
    üretim adedi — Dashboard'daki tesis bazlı makine grafikleri için."""
    d = load_data()
    machines = d.get("machines", {})
    daily = d.get("daily_entries", {})

    try:
        ref_date = date.fromisoformat((target_date or date.today().isoformat())[:10])
    except Exception:
        ref_date = date.today()

    if period == "weekly":
        start = ref_date - timedelta(days=ref_date.weekday())
        date_list = [start + timedelta(days=i) for i in range(7)]
    elif period == "monthly":
        days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
        date_list = [date(ref_date.year, ref_date.month, i) for i in range(1, days_in_month + 1)]
    else:
        period = "daily"
        date_list = [ref_date]

    agg = {}
    for dt in date_list:
        day_data = daily.get(dt.isoformat(), {})
        for entry in day_data.get("entries", []):
            for se in entry.get("stage_entries", []):
                mid = se.get("machine_id") or ""
                if not mid:
                    continue
                m = machines.get(mid)
                if facility_id and facility_id != "all":
                    m_fac = (m.get("facility_id") or "fac1") if m else "fac1"
                    if m_fac != facility_id:
                        continue
                if mid not in agg:
                    agg[mid] = {
                        "machine_id": mid,
                        "name": m.get("name", mid) if m else mid,
                        "stage": m.get("stage", "") if m else "",
                        "facility_id": (m.get("facility_id") or "fac1") if m else "fac1",
                        "work_hours": 0.0,
                        "output_qty": 0,
                    }
                agg[mid]["work_hours"] += se.get("work_hours") or 0
                agg[mid]["output_qty"] += se.get("output_qty") or 0

    for mid, m in machines.items():
        if facility_id and facility_id != "all" and (m.get("facility_id") or "fac1") != facility_id:
            continue
        if mid not in agg:
            agg[mid] = {
                "machine_id": mid,
                "name": m.get("name", mid),
                "stage": m.get("stage", ""),
                "facility_id": m.get("facility_id") or "fac1",
                "work_hours": 0.0,
                "output_qty": 0,
            }

    result = list(agg.values())
    for r in result:
        r["work_hours"] = round(r["work_hours"], 2)
    result.sort(key=lambda x: x["work_hours"], reverse=True)

    return {
        "period": period,
        "start_date": date_list[0].isoformat(),
        "end_date": date_list[-1].isoformat(),
        "machines": result
    }
def create_machine(req: MachineCreate):
    d = load_data()
    mid = "MCH-" + str(uuid.uuid4())[:8].upper()
    d["machines"][mid] = {
        "id": mid,
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
    return d["daily_entries"].get(date_key, {"date": date_key, "entries": [], "downtimes": []})

@app.post("/api/daily/{date_key}")
def save_daily(date_key: str, payload: DailyPayload):
    d = load_data()
    entries = []
    for e in payload.entries:
        stage_list = []
        for se in e.stage_entries:
            stage_list.append({
                "stage": se.stage,
                "machine_id": se.machine_id,
                "output_qty": se.output_qty,
                "work_hours": se.work_hours,
                "notes": se.notes or ""
            })
        entries.append({
            "order_id": e.order_id,
            "shift": e.shift,
            "operator": e.operator,
            "stage_entries": stage_list,
            "total_output": sum(s["output_qty"] for s in stage_list)
        })
    if date_key not in d["daily_entries"]:
        d["daily_entries"][date_key] = {}
    d["daily_entries"][date_key].update({"date": date_key, "entries": entries})
    save_data(d)
    return {"status": "ok", "saved": len(entries)}

@app.post("/api/daily/{date_key}/downtime")
def save_downtime(date_key: str, payload: DailyDowntime):
    d = load_data()
    if date_key not in d["daily_entries"]:
        d["daily_entries"][date_key] = {"date": date_key, "entries": []}
    d["daily_entries"][date_key]["downtimes"] = [dt.dict() for dt in payload.downtimes]
    save_data(d)
    return {"status": "ok"}

TURKISH_MONTHS = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]

def _output_for_day(daily, day_str, order_facility, facility_id=None):
    total = 0
    day_entries = daily.get(day_str, {}).get("entries", [])
    for entry in day_entries:
        oid = entry.get("order_id")
        if facility_id and facility_id != "all" and order_facility.get(oid, "fac1") != facility_id:
            continue
        for se in entry.get("stage_entries", []):
            total += se.get("output_qty", 0)
    return total

@app.get("/api/dashboard")
def dashboard(facility_id: Optional[str] = Query(None), period: Optional[str] = Query("weekly"), target_date: Optional[str] = Query(None)):
    d = load_data()
    orders_all = d.get("orders", {})
    machines = d.get("machines", {})
    daily = d.get("daily_entries", {})
    today_str = date.today().isoformat()
    today_dt = date.today()

    order_facility = {oid: (o.get("facility_id") or "fac1") for oid, o in orders_all.items()}

    # Filter orders/machines to the selected facility for counts & tables
    if facility_id and facility_id != "all":
        orders = {oid: o for oid, o in orders_all.items() if (o.get("facility_id") or "fac1") == facility_id}
        machines = {mid: m for mid, m in machines.items() if (m.get("facility_id") or "fac1") == facility_id}
    else:
        orders = orders_all

    try:
        ref_date = date.fromisoformat((target_date or today_str)[:10])
    except Exception:
        ref_date = today_dt

    start_of_week = ref_date - timedelta(days=ref_date.weekday())
    end_of_week   = start_of_week + timedelta(days=6)

    total_orders = len(orders)
    open_orders  = sum(1 for o in orders.values() if o.get("status") == "open")
    done_orders  = sum(1 for o in orders.values() if o.get("status") == "done")
    delayed_orders = 0
    sarkan_siparisler = []
    
    for oid, o in orders.items():
        if o.get("status") == "open":
            try:
                deliv_dt = date.fromisoformat(o["delivery_date"])
                days_rem = (deliv_dt - today_dt).days
                
                total_out = 0
                stages = o.get("stages", [])
                last_stage = stages[-1] if stages else None
                for day_data in daily.values():
                    for entry in day_data.get("entries", []):
                        if entry.get("order_id") == oid:
                            for se in entry.get("stage_entries", []):
                                if last_stage and se.get("stage") == last_stage:
                                    total_out += se.get("output_qty", 0)
                                elif not stages:
                                    total_out += se.get("output_qty", 0)
                
                kalan = max(0, o.get("qty", 0) - total_out)
                
                if days_rem < 0:
                    delayed_orders += 1
                    sarkan_siparisler.append({
                        "id": oid,
                        "order_no": o.get("order_no", ""),
                        "customer": o.get("customer", ""),
                        "model": o.get("model", ""),
                        "qty": o.get("qty", 0),
                        "produced_qty": total_out,
                        "remaining_qty": kalan,
                        "delivery_date": o.get("delivery_date", ""),
                        "delay_days": abs(days_rem),
                        "status_tag": "Sarktı (Gecikmiş)",
                        "severity": "high"
                    })
                elif days_rem <= 7:
                    sarkan_siparisler.append({
                        "id": oid,
                        "order_no": o.get("order_no", ""),
                        "customer": o.get("customer", ""),
                        "model": o.get("model", ""),
                        "qty": o.get("qty", 0),
                        "produced_qty": total_out,
                        "remaining_qty": kalan,
                        "delivery_date": o.get("delivery_date", ""),
                        "delay_days": 0,
                        "days_left": days_rem,
                        "status_tag": "Bu Hafta Teslim",
                        "severity": "medium"
                    })
            except Exception:
                pass

    today_output = _output_for_day(daily, today_str, order_facility, facility_id)

    weekly_output = 0
    weekly_days = []
    day_names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    for i in range(7):
        cur_day = start_of_week + timedelta(days=i)
        cur_str = cur_day.isoformat()
        day_out = _output_for_day(daily, cur_str, order_facility, facility_id)
        weekly_output += day_out
        weekly_days.append({
            "date": cur_str,
            "day_name": day_names[i],
            "is_today": cur_str == today_str,
            "output": day_out
        })

    # Monthly total for the referenced month
    days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
    monthly_output = 0
    for i in range(1, days_in_month + 1):
        cur_str = date(ref_date.year, ref_date.month, i).isoformat()
        monthly_output += _output_for_day(daily, cur_str, order_facility, facility_id)

    total_out = 0
    machine_out = {}
    stage_output = {}
    all_machines = d.get("machines", {})
    for day_data in daily.values():
        for entry in day_data.get("entries", []):
            oid = entry.get("order_id")
            if facility_id and facility_id != "all" and order_facility.get(oid, "fac1") != facility_id:
                continue
            for se in entry.get("stage_entries", []):
                total_out += se.get("output_qty", 0)
                stg = se.get("stage", "Genel")
                stage_output[stg] = stage_output.get(stg, 0) + se.get("output_qty", 0)
                mid = se.get("machine_id", "")
                if mid:
                    machine_out[mid] = machine_out.get(mid, 0) + se.get("output_qty", 0)

    mstats = [{"id": mid, "name": all_machines.get(mid, {}).get("name", mid), "output": q} for mid, q in machine_out.items()]
    mstats.sort(key=lambda x: x["output"], reverse=True)

    stage_stats = [{"stage": stg, "output": qty} for stg, qty in stage_output.items()]
    stage_stats.sort(key=lambda x: x["output"], reverse=True)

    facility_breakdown = {}
    for fid in DEFAULT_FACILITIES.keys() | {"fac1", "fac2"}:
        facility_breakdown[fid] = {
            "today_output": _output_for_day(daily, today_str, order_facility, fid),
            "weekly_output": sum(_output_for_day(daily, (start_of_week + timedelta(days=i)).isoformat(), order_facility, fid) for i in range(7)),
            "monthly_output": sum(_output_for_day(daily, date(ref_date.year, ref_date.month, i).isoformat(), order_facility, fid) for i in range(1, days_in_month + 1)),
        }

    return {
        "orders": {"total": total_orders, "open": open_orders, "done": done_orders, "delayed": delayed_orders},
        "machines_count": len(machines),
        "production": {
            "total_output": total_out
        },
        "today_summary": {
            "date": today_str,
            "output": today_output
        },
        "weekly_summary": {
            "start_date": start_of_week.isoformat(),
            "end_date": end_of_week.isoformat(),
            "total_output": weekly_output,
            "days": weekly_days
        },
        "monthly_summary": {
            "month_name": f"{TURKISH_MONTHS[ref_date.month-1]} {ref_date.year}",
            "total_output": monthly_output
        },
        "facility_breakdown": facility_breakdown,
        "sarkan_siparisler": sarkan_siparisler,
        "stage_stats": stage_stats,
        "machine_stats": mstats[:10]
    }

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_backend:app", host="0.0.0.0", port=8001, reload=True)
