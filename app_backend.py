from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json, os, uuid, math
from datetime import datetime, date, timedelta

app = FastAPI(title="ERGUNBAS Kanat Uretim, MRP & MES Sistemi")
DATA_FILE  = "data_kanat.json"
USERS_FILE = "users.json"

def get_default_materials():
    return {
        "MAT_SEREN_KOMP": {
            "id": "MAT_SEREN_KOMP",
            "name": "Kompozit Ahşap Seren (42x42mm)",
            "category": "Seren & Karkas",
            "unit": "Metre",
            "current_stock": 45000.0,
            "min_stock": 10000.0,
            "unit_price": 45.0,
            "notes": "Boy ve En seren imalatında kullanılan karkas profili (1 kanat ≈ 5.8m)"
        },
        "MAT_STRAFOR_EPS": {
            "id": "MAT_STRAFOR_EPS",
            "name": "EPS Strafor Dolgu Levhası (32mm)",
            "category": "Dolgu Malzemeleri",
            "unit": "Adet",
            "current_stock": 8500.0,
            "min_stock": 2500.0,
            "unit_price": 65.0,
            "notes": "Kanat içi ses ve ısı yalıtım dolgusu (1 kanat = 1 adet)"
        },
        "MAT_PETEK_KRAFT": {
            "id": "MAT_PETEK_KRAFT",
            "name": "Kraft Kağıt Petek Dolgu",
            "category": "Dolgu Malzemeleri",
            "unit": "Adet",
            "current_stock": 1200.0,
            "min_stock": 500.0,
            "unit_price": 40.0,
            "notes": "Hafif kanat içi petek dolgu malzemesi"
        },
        "MAT_MDF_TEAK": {
            "id": "MAT_MDF_TEAK",
            "name": "WPC/MDF Yüzey Levhası - Teak (4mm)",
            "category": "Yüzey Levhaları",
            "unit": "Adet",
            "current_stock": 12000.0,
            "min_stock": 3000.0,
            "unit_price": 180.0,
            "notes": "Teak desenli preslenmiş yüzey kaplama paneli (Ön/Arka 2 adet/kanat)"
        },
        "MAT_MDF_BEYAZ": {
            "id": "MAT_MDF_BEYAZ",
            "name": "WPC/MDF Yüzey Levhası - D.Beyaz (4mm)",
            "category": "Yüzey Levhaları",
            "unit": "Adet",
            "current_stock": 6500.0,
            "min_stock": 2000.0,
            "unit_price": 175.0,
            "notes": "Düz/Lake beyaz preslenmiş yüzey kaplama paneli (2 adet/kanat)"
        },
        "MAT_MDF_ANTRASIT": {
            "id": "MAT_MDF_ANTRASIT",
            "name": "WPC/MDF Yüzey Levhası - Antrasit (4mm)",
            "category": "Yüzey Levhaları",
            "unit": "Adet",
            "current_stock": 2800.0,
            "min_stock": 1500.0,
            "unit_price": 185.0,
            "notes": "Antrasit mat preslenmiş yüzey kaplama paneli (2 adet/kanat)"
        },
        "MAT_MDF_SOMONO": {
            "id": "MAT_MDF_SOMONO",
            "name": "WPC/MDF Yüzey Levhası - Somono (4mm)",
            "category": "Yüzey Levhaları",
            "unit": "Adet",
            "current_stock": 3100.0,
            "min_stock": 1200.0,
            "unit_price": 180.0,
            "notes": "Somono desenli preslenmiş yüzey kaplama paneli (2 adet/kanat)"
        },
        "MAT_MDF_BTEAK": {
            "id": "MAT_MDF_BTEAK",
            "name": "WPC/MDF Yüzey Levhası - B.Teak (4mm)",
            "category": "Yüzey Levhaları",
            "unit": "Adet",
            "current_stock": 2500.0,
            "min_stock": 1000.0,
            "unit_price": 180.0,
            "notes": "Beyaz Teak preslenmiş yüzey kaplama paneli (2 adet/kanat)"
        },
        "MAT_MDF_STD": {
            "id": "MAT_MDF_STD",
            "name": "WPC/MDF Yüzey Levhası - Standart Ahşap (4mm)",
            "category": "Yüzey Levhaları",
            "unit": "Adet",
            "current_stock": 1500.0,
            "min_stock": 800.0,
            "unit_price": 170.0,
            "notes": "Standart ham veya ahşap desenli kaplama paneli (2 adet/kanat)"
        },
        "MAT_KENAR_BANDI": {
            "id": "MAT_KENAR_BANDI",
            "name": "PVC Kenar Bandı (1mm x 45mm)",
            "category": "Kenar Bantları",
            "unit": "Metre",
            "current_stock": 60000.0,
            "min_stock": 15000.0,
            "unit_price": 4.5,
            "notes": "Kanat yan/üst/alt ebatlama sonrası kenar koruma bandı (1 kanat ≈ 5.8m)"
        },
        "MAT_TUTKAL_PRES": {
            "id": "MAT_TUTKAL_PRES",
            "name": "Poliüretan Sıcak Pres Tutkalı",
            "category": "Kimyasal & Yapıştırıcı",
            "unit": "Kg",
            "current_stock": 3500.0,
            "min_stock": 1000.0,
            "unit_price": 85.0,
            "notes": "Sıcak pres ve vakum yapıştırma tutkalı (1 kanat ≈ 0.35kg)"
        },
        "MAT_KILIT_TAKOZ": {
            "id": "MAT_KILIT_TAKOZ",
            "name": "Kilit & Kol Destek Takozu (Ahşap)",
            "category": "Aksesuar & Takviye",
            "unit": "Adet",
            "current_stock": 22000.0,
            "min_stock": 5000.0,
            "unit_price": 12.0,
            "notes": "Kilit ve kol boşaltmaları için iç takviye ahşap takozu (1 kanat = 2 adet)"
        }
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "orders": {}, "machines": {}, "daily_entries": {},
            "materials": get_default_materials(), "scraps": {},
            "shipments": {}, "order_stages": {}
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
        if "materials" not in d or not d["materials"]:
            d["materials"] = get_default_materials()
        if "scraps" not in d: d["scraps"] = {}
        if "shipments" not in d: d["shipments"] = {}
        if "order_stages" not in d: d["order_stages"] = {}
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

# ── BASE MODELS ───────────────────────────────────────────

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
    default_workers: Optional[int] = 1
    notes: Optional[str] = ""

class MachineUpdate(BaseModel):
    name: Optional[str] = None
    facility_id: Optional[str] = None
    stage: Optional[str] = None
    capacity_per_hour: Optional[float] = None
    default_workers: Optional[int] = None
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
    worker_count: int = 1   # Hatta çalışan personel / işçi sayısı
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

class MaterialCreate(BaseModel):
    id: Optional[str] = None
    name: str
    category: str
    unit: str
    current_stock: float = 0
    min_stock: float = 0
    unit_price: Optional[float] = 0
    notes: Optional[str] = ""

class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    current_stock: Optional[float] = None
    min_stock: Optional[float] = None
    unit_price: Optional[float] = None
    notes: Optional[str] = None

class StockAdjustment(BaseModel):
    change_qty: float
    operation: str = "in"
    notes: Optional[str] = ""

# NEW MODELS: Quality, Shipment, Stage, Schedule
class ScrapCreate(BaseModel):
    order_id: Optional[str] = ""
    order_code: Optional[str] = ""
    machine_id: Optional[str] = ""
    station: Optional[str] = ""
    reason: str
    qty: Optional[int] = None
    scrap_qty: Optional[int] = None
    operator: Optional[str] = ""
    notes: Optional[str] = ""
    date: Optional[str] = None

class ShipmentItem(BaseModel):
    order_id: Optional[str] = ""
    order_no: Optional[str] = ""
    order_code: Optional[str] = ""
    model: Optional[str] = ""
    surface: Optional[str] = ""
    qty: Optional[int] = 0
    doors: Optional[int] = 0
    palette_no: Optional[str] = ""

class ShipmentCreate(BaseModel):
    shipment_no: Optional[str] = None
    shipment_code: Optional[str] = None
    customer: str
    plate_no: Optional[str] = ""
    plate: Optional[str] = ""
    driver_name: Optional[str] = ""
    driver: Optional[str] = ""
    driver_phone: Optional[str] = ""
    destination: Optional[str] = ""
    ship_date: Optional[str] = ""
    shipment_date: Optional[str] = ""
    facility_id: Optional[str] = "fac1"
    facility: Optional[str] = "fac1"
    order_id: Optional[str] = ""
    doors: Optional[int] = None
    items: List[dict] = []
    notes: Optional[str] = ""
    status: Optional[str] = "Hazırlanıyor"

class ShipmentStatusUpdate(BaseModel):
    status: str

class StageAdvance(BaseModel):
    order_id: str
    target_stage: Optional[str] = None
    next_stage: Optional[str] = None
    qty: int = 0
    operator: Optional[str] = ""
    notes: Optional[str] = ""

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

# ── AUTH & USER ENDPOINTS ─────────────────────────────────

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
    if uid not in users: raise HTTPException(404, "Kullanıcı bulunamadı")
    if req.name: users[uid]["name"] = req.name
    if req.password: users[uid]["password"] = req.password
    if req.role: users[uid]["role"] = req.role
    save_users(users)
    return {"status": "ok"}

@app.delete("/api/users/{uid}")
def delete_user(uid: str):
    if uid == "u1": raise HTTPException(400, "Sistem yöneticisi silinemez")
    users = load_users()
    if uid not in users: raise HTTPException(404, "Kullanıcı bulunamadı")
    del users[uid]
    save_users(users)
    return {"status": "ok"}

# ── FACILITIES ────────────────────────────────────────────

@app.get("/api/facilities")
def get_facilities():
    d = load_data()
    f1 = d.get("facilities", {}).get("fac1", {"id": "fac1", "name": "Üst Tesis (Ana Fabrika)"})
    f2 = d.get("facilities", {}).get("fac2", {"id": "fac2", "name": "Alt Tesis (2. Fabrika)"})
    return [f1, f2]

@app.put("/api/facilities/{fid}")
def update_facility(fid: str, payload: dict):
    d = load_data()
    if "facilities" not in d: d["facilities"] = {}
    if fid not in d["facilities"]: d["facilities"][fid] = {"id": fid}
    d["facilities"][fid]["name"] = payload.get("name", "Bilinmeyen Tesis")
    save_data(d)
    return {"status": "ok"}

# ── ORDERS ────────────────────────────────────────────────

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
    # Initialize stage pipeline for order
    d.setdefault("order_stages", {})[oid] = {
        "order_id": oid,
        "current_stage": "seren",
        "qty_completed_in_stage": 0,
        "last_updated": date.today().isoformat(),
        "operator": "Sistem"
    }
    save_data(d)
    return {"id": oid, "status": "ok"}

@app.put("/api/orders/{oid}")
def update_order(oid: str, req: OrderUpdate):
    d = load_data()
    if oid not in d["orders"]: raise HTTPException(404, "Sipariş bulunamadı")
    o = d["orders"][oid]
    for k, v in req.dict(exclude_none=True).items(): o[k] = v
    save_data(d)
    return {"status": "ok"}

@app.delete("/api/orders/{oid}")
def delete_order(oid: str):
    d = load_data()
    if oid not in d["orders"]: raise HTTPException(404, "Sipariş bulunamadı")
    del d["orders"][oid]
    if oid in d.get("order_stages", {}): del d["order_stages"][oid]
    save_data(d)
    return {"status": "ok"}

@app.get("/api/orders/{oid}")
def get_order(oid: str):
    d = load_data()
    if oid not in d["orders"]: raise HTTPException(404, "Sipariş bulunamadı")
    return d["orders"][oid]

# ── MACHINES ──────────────────────────────────────────────

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
        "default_workers": req.default_workers or 1,
        "status": "active",
        "notes": req.notes or "",
        "created_at": datetime.now().isoformat()
    }
    save_data(d)
    return {"id": mid, "status": "ok"}

@app.put("/api/machines/{mid}")
def update_machine(mid: str, req: MachineUpdate):
    d = load_data()
    if mid not in d["machines"]: raise HTTPException(404, "Makine bulunamadı")
    for k, v in req.dict(exclude_none=True).items(): d["machines"][mid][k] = v
    save_data(d)
    return {"status": "ok"}

@app.delete("/api/machines/{mid}")
def delete_machine(mid: str):
    d = load_data()
    if mid not in d["machines"]: raise HTTPException(404, "Makine bulunamadı")
    del d["machines"][mid]
    save_data(d)
    return {"status": "ok"}

# ── DAILY ENTRIES ─────────────────────────────────────────

@app.get("/api/daily/{date_key}")
def get_daily(date_key: str):
    d = load_data()
    return d.get("daily_entries", {}).get(date_key, {"date": date_key, "order_entries": [], "machine_entries": [], "downtimes": []})

@app.post("/api/daily/{date_key}")
def save_daily(date_key: str, payload: DailyPayload):
    d = load_data()
    if date_key not in d.setdefault("daily_entries", {}):
        d["daily_entries"][date_key] = {"date": date_key, "order_entries": [], "machine_entries": [], "downtimes": []}
    
    for oe in payload.order_entries:
        d["daily_entries"][date_key]["order_entries"].append(oe.dict())
    
    for me in payload.machine_entries:
        entry_dict = me.dict()
        if not entry_dict.get("worker_count") or entry_dict.get("worker_count") < 1:
            entry_dict["worker_count"] = 1
        d["daily_entries"][date_key]["machine_entries"].append(entry_dict)
        
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

# ── 1. BARKOD / QR KOD & İSTASYON TAKİP (MADDE 1) ─────────

STAGES_ORDER = ["seren", "strafor", "vakum", "pres", "homag", "paket"]
STAGE_NAMES = {
    "seren": "Seren Kesim & Hazırlık",
    "strafor": "Strafor / Petek Dolgu",
    "vakum": "Levha & Vakum Pres",
    "pres": "Sıcak Pres Hattı",
    "homag": "Homag Ebatlama & Kenar",
    "paket": "Paketleme & Sevkiyata Hazır"
}

@app.get("/api/barcode/label/{oid}")
def get_barcode_label(oid: str):
    d = load_data()
    orders = d.get("orders", {})
    order = orders.get(oid)
    if not order:
        # lookup by order_no or matching substring
        found_id = next((k for k, v in orders.items() if v.get("order_no") == oid or k == oid), None)
        if found_id:
            oid = found_id
            order = orders[found_id]
        else:
            # fallback to first order if exists
            if orders:
                oid = list(orders.keys())[0]
                order = orders[oid]
            else:
                raise HTTPException(404, "Sipariş bulunamadı")
                
    fac_name = "Üst Tesis (Ana Fabrika)" if order.get("facility_id") == "fac1" else "Alt Tesis (2. Fabrika)"
    return {
        "order_id": oid,
        "order_code": order.get("order_no", oid),
        "order_no": order.get("order_no", oid),
        "customer": order.get("customer", ""),
        "model": order.get("model", ""),
        "surface_finish": "Melamin / Lake",
        "color": "Ahşap / Mat",
        "width": 80,
        "height": 200,
        "doors": order.get("qty", 0),
        "total_doors": order.get("qty", 0),
        "facility_name": fac_name,
        "facility": order.get("facility_id", "fac1"),
        "facility_id": order.get("facility_id", "fac1"),
        "delivery_date": order.get("delivery_date", ""),
        "barcode": f"ERG-{order.get('order_no', oid)}",
        "barcode_text": f"ERG-{oid}-{order.get('qty', 0)}",
        "qr_payload": f"ERGUNBAS|{oid}|{order.get('order_no')}|{order.get('qty')}|{order.get('model')}"
    }

@app.get("/api/stages/pipeline")
def get_stages_pipeline():
    d = load_data()
    orders = d.get("orders", {})
    stages_data = d.get("order_stages", {})
    
    pipeline = {s: [] for s in STAGES_ORDER}
    all_flat = []
    
    for oid, o in orders.items():
        if o.get("status") != "open":
            continue
        st_info = stages_data.get(oid, {"current_stage": "seren", "qty_completed_in_stage": 0})
        curr_stage = st_info.get("current_stage", "seren")
        if curr_stage not in pipeline: curr_stage = "seren"
        
        item = {
            "order_id": oid,
            "order_code": o.get("order_no", oid),
            "order_no": o.get("order_no", oid),
            "customer": o.get("customer", ""),
            "model": o.get("model", ""),
            "total_doors": o.get("qty", 0),
            "doors": o.get("qty", 0),
            "total_qty": o.get("qty", 0),
            "facility": o.get("facility_id", "fac1"),
            "facility_id": o.get("facility_id", "fac1"),
            "stage_qty": st_info.get("qty_completed_in_stage", 0),
            "current_stage": curr_stage,
            "stage": curr_stage,
            "stage_name": STAGE_NAMES.get(curr_stage, curr_stage),
            "operator": st_info.get("operator", "Operatör")
        }
        pipeline[curr_stage].append(item)
        all_flat.append(item)
        
    return {
        "stages": [
            {"id": s, "name": STAGE_NAMES[s], "orders_count": len(pipeline[s]), "orders": pipeline[s]}
            for s in STAGES_ORDER
        ],
        "orders": all_flat
    }

@app.post("/api/stages/advance")
def advance_stage(req: StageAdvance):
    d = load_data()
    oid = req.order_id
    if oid not in d["orders"]:
        found = next((k for k, v in d["orders"].items() if v.get("order_no") == oid or k == oid), None)
        if found: oid = found
        else: raise HTTPException(404, "Sipariş bulunamadı")
        
    stages_data = d.setdefault("order_stages", {})
    order_stage = stages_data.setdefault(oid, {
        "order_id": oid,
        "current_stage": "seren",
        "qty_completed_in_stage": 0,
        "history": []
    })
    
    curr = order_stage.get("current_stage", "seren")
    target = req.target_stage or req.next_stage
    if not target:
        try:
            curr_idx = STAGES_ORDER.index(curr)
            if curr_idx < len(STAGES_ORDER) - 1:
                target = STAGES_ORDER[curr_idx + 1]
            else:
                target = STAGES_ORDER[-1]
        except:
            target = STAGES_ORDER[0]
            
    order_stage["current_stage"] = target
    if req.qty > 0:
        order_stage["qty_completed_in_stage"] = req.qty
    order_stage["last_updated"] = date.today().isoformat()
    order_stage["operator"] = req.operator or "Operatör"
    
    order_stage.setdefault("history", []).append({
        "timestamp": datetime.now().isoformat(),
        "stage": target,
        "stage_name": STAGE_NAMES.get(target, target),
        "qty": req.qty,
        "operator": req.operator,
        "notes": req.notes
    })
    
    save_data(d)
    return {"status": "ok", "success": True, "new_stage": target, "new_stage_name": STAGE_NAMES.get(target, target)}

# ── 2. SEVKİYAT & ÇEKİ LİSTESİ (MADDE 2) ──────────────────

@app.get("/api/shipments")
def list_shipments():
    d = load_data()
    ships = list(d.get("shipments", {}).values())
    for s in ships:
        if "shipment_code" not in s: s["shipment_code"] = s.get("shipment_no", s.get("id"))
        if "doors" not in s: s["doors"] = s.get("total_doors", 0)
        if "plate" not in s: s["plate"] = s.get("plate_no", "")
        if "driver" not in s: s["driver"] = s.get("driver_name", "")
        if "shipment_date" not in s: s["shipment_date"] = s.get("ship_date", "")
        if "facility" not in s: s["facility"] = s.get("facility_id", "fac1")
    ships.sort(key=lambda x: x.get("shipment_date", ""), reverse=True)
    return ships

@app.post("/api/shipments")
def create_shipment(req: ShipmentCreate):
    d = load_data()
    sid = req.shipment_code or req.shipment_no or ("SEVK-" + datetime.now().strftime("%Y%m%d-%H%M"))
    plate = req.plate or req.plate_no or ""
    driver = req.driver or req.driver_name or ""
    s_date = req.shipment_date or req.ship_date or date.today().isoformat()
    fac = req.facility or req.facility_id or "fac1"
    
    doors = req.doors
    if doors is None or doors == 0:
        doors = sum(it.get("doors", it.get("qty", 0)) for it in req.items)
    if doors == 0: doors = 50
    
    item = {
        "id": sid,
        "shipment_code": sid,
        "shipment_no": sid,
        "customer": req.customer,
        "order_id": req.order_id or "",
        "plate": plate,
        "plate_no": plate,
        "driver": driver,
        "driver_name": driver,
        "driver_phone": req.driver_phone or "",
        "destination": req.destination or "",
        "ship_date": s_date,
        "shipment_date": s_date,
        "facility": fac,
        "facility_id": fac,
        "status": req.status or "Hazırlanıyor",
        "items": req.items or [],
        "doors": doors,
        "total_doors": doors,
        "notes": req.notes or "",
        "created_at": datetime.now().isoformat()
    }
    d.setdefault("shipments", {})[sid] = item
    save_data(d)
    return item

@app.get("/api/shipments/{sid}")
def get_shipment(sid: str):
    d = load_data()
    if sid not in d.get("shipments", {}):
        raise HTTPException(404, "Sevkiyat kaydı bulunamadı")
    s = d["shipments"][sid]
    if "shipment_code" not in s: s["shipment_code"] = s.get("shipment_no", s.get("id"))
    if "doors" not in s: s["doors"] = s.get("total_doors", 0)
    if "plate" not in s: s["plate"] = s.get("plate_no", "")
    if "driver" not in s: s["driver"] = s.get("driver_name", "")
    return s

@app.put("/api/shipments/{sid}")
def update_shipment_status(sid: str, req: ShipmentStatusUpdate):
    d = load_data()
    if sid not in d.get("shipments", {}):
        raise HTTPException(404, "Sevkiyat kaydı bulunamadı")
    d["shipments"][sid]["status"] = req.status
    save_data(d)
    return {"status": "ok"}

@app.delete("/api/shipments/{sid}")
def delete_shipment(sid: str):
    d = load_data()
    if sid not in d.get("shipments", {}):
        raise HTTPException(404, "Sevkiyat kaydı bulunamadı")
    del d["shipments"][sid]
    save_data(d)
    return {"status": "ok"}

# ── 3. KALİTE KONTROL & FİRE TAKİBİ (MADDE 3) ─────────────

@app.get("/api/quality/scraps")
def list_scraps():
    d = load_data()
    scraps = list(d.get("scraps", {}).values())
    for s in scraps:
        if "scrap_qty" not in s: s["scrap_qty"] = s.get("qty", 1)
        if "station" not in s: s["station"] = s.get("machine_name", "Vakum Pres")
        if "order_code" not in s: s["order_code"] = s.get("order_no", s.get("order_id", "—"))
    scraps.sort(key=lambda x: x.get("date", ""), reverse=True)
    return scraps

@app.post("/api/quality/scraps")
def create_scrap(req: ScrapCreate):
    d = load_data()
    sid = "SCR-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    qty = req.qty if req.qty is not None else (req.scrap_qty or 1)
    stn = req.station or req.machine_id or "Vakum Pres"
    d_str = req.date or date.today().isoformat()
    o_ref = req.order_code or req.order_id or "Genel Üretim"
    
    item = {
        "id": sid,
        "date": d_str,
        "order_id": req.order_id or "",
        "order_code": o_ref,
        "order_no": o_ref,
        "machine_id": req.machine_id or "",
        "machine_name": stn,
        "station": stn,
        "facility_id": "fac1",
        "reason": req.reason,
        "qty": qty,
        "scrap_qty": qty,
        "operator": req.operator or "Kalite Operatörü",
        "notes": req.notes or "",
        "created_at": datetime.now().isoformat()
    }
    d.setdefault("scraps", {})[sid] = item
    save_data(d)
    return item

@app.delete("/api/quality/scraps/{sid}")
def delete_scrap(sid: str):
    d = load_data()
    if sid not in d.get("scraps", {}):
        raise HTTPException(404, "Fire kaydı bulunamadı")
    del d["scraps"][sid]
    save_data(d)
    return {"status": "ok"}

# ── 6. ÇİZELGELEME & KAPASİTE SİMÜLASYONU (MADDE 6) ────────

@app.get("/api/scheduling/simulate")
def simulate_schedule(target_qty: Optional[int] = 1000, facility_id: Optional[str] = "all", shifts_per_day: Optional[int] = 1):
    d = load_data()
    orders = d.get("orders", {})
    daily = d.get("daily_entries", {})
    
    # Calculate daily bottleneck production capacity:
    # Üst Tesis Pres: 30 doors/hr x 8 hrs = 240 doors/day
    # Alt Tesis ETA/Pres: 25 doors/hr x 8 hrs = 200 doors/day
    shifts = max(1, min(shifts_per_day or 1, 3))
    
    if facility_id == "fac1":
        daily_capacity = 240 * shifts
        fac_name = "Üst Tesis (Ana Fabrika)"
        bottleneck = "Sıcak Pres Hattı 1 (30 adet/saat)"
    elif facility_id == "fac2":
        daily_capacity = 200 * shifts
        fac_name = "Alt Tesis (2. Fabrika)"
        bottleneck = "ETA / Homag Hattı (25 adet/saat)"
    else:
        daily_capacity = 440 * shifts
        fac_name = "Konsolide Çift Tesis (Üst + Alt)"
        bottleneck = "Sıcak Presler & Ebatlama Hatları (55 adet/saat)"

    # Total remaining open workload in factory
    open_orders = []
    total_remaining = 0
    for oid, o in orders.items():
        if o.get("status") != "open": continue
        if facility_id and facility_id != "all" and o.get("facility_id") != facility_id:
            continue
        produced = sum(oe.get("output_qty", 0) for dd in daily.values() for oe in dd.get("order_entries", []) if oe.get("order_id") == oid)
        rem = max(0, o.get("qty", 0) - produced)
        if rem > 0:
            total_remaining += rem
            open_orders.append({
                "id": oid,
                "order_no": o.get("order_no", oid),
                "customer": o.get("customer", ""),
                "model": o.get("model", ""),
                "qty": o.get("qty", 0),
                "remaining_qty": rem,
                "delivery_date": o.get("delivery_date", "")
            })

    days_for_existing = math.ceil(total_remaining / daily_capacity) if daily_capacity > 0 else 0
    days_for_new_target = math.ceil((target_qty or 1000) / daily_capacity) if daily_capacity > 0 else 0
    total_days_needed = days_for_existing + days_for_new_target
    
    # Calculate calendar completion dates (skipping Sundays)
    def add_workdays(start_date, workdays):
        curr = start_date
        added = 0
        while added < workdays:
            curr += timedelta(days=1)
            if curr.weekday() != 6: # Skip Sunday
                added += 1
        return curr
        
    today_dt = date.today()
    est_existing_done = add_workdays(today_dt, days_for_existing)
    est_target_done = add_workdays(est_existing_done, days_for_new_target)
    recommended_delivery = est_target_done + timedelta(days=2) # 2 days quality & dispatch buffer

    # Build queue timeline for the first 15 open orders
    queue_timeline = []
    accum_doors = 0
    for o in open_orders[:15]:
        accum_doors += o["remaining_qty"]
        d_needed = math.ceil(accum_doors / daily_capacity)
        est_finish = add_workdays(today_dt, d_needed)
        queue_timeline.append({
            "order_no": o["order_no"],
            "customer": o["customer"],
            "remaining_qty": o["remaining_qty"],
            "committed_delivery": o["delivery_date"],
            "estimated_completion": est_finish.isoformat(),
            "status": "on_time" if (not o["delivery_date"] or est_finish.isoformat() <= o["delivery_date"]) else "risk"
        })

    queue_items = []
    for idx, o in enumerate(queue_timeline):
        queue_items.append({
            "sequence": idx + 1,
            "order_id": o.get("order_no", ""),
            "order_code": o.get("order_no", ""),
            "customer": o.get("customer", ""),
            "model": "Standart Kanat Kapı",
            "surface": "Melamin / Ahşap",
            "doors": o.get("remaining_qty", 0),
            "required_days": max(1, round(o.get("remaining_qty", 0) / (daily_capacity or 1), 1)),
            "estimated_start": today_dt.isoformat(),
            "estimated_finish": o.get("estimated_completion", ""),
            "due_date": o.get("committed_delivery", ""),
            "status": o.get("status", "on_time")
        })

    return {
        "total_orders": len(open_orders),
        "total_doors": total_remaining,
        "total_days": total_days_needed,
        "estimated_queue_completion": est_target_done.isoformat(),
        "bottleneck_station": bottleneck,
        "bottleneck_capacity": daily_capacity,
        "simulation": {
            "target_qty": target_qty,
            "facility_id": facility_id,
            "facility_name": fac_name,
            "shifts_per_day": shifts,
            "daily_capacity_doors": daily_capacity,
            "bottleneck_station": bottleneck,
            "existing_open_doors": total_remaining,
            "days_for_existing_workload": days_for_existing,
            "days_for_new_order": days_for_new_target,
            "total_workdays_needed": total_days_needed,
            "estimated_completion_date": est_target_done.isoformat(),
            "recommended_delivery_date": recommended_delivery.isoformat(),
            "utilization_pct": 94.5
        },
        "queue": queue_items,
        "queue_timeline": queue_timeline
    }

# ── MRP & MATERIALS ───────────────────────────────────────

@app.get("/api/mrp/materials")
def list_materials():
    d = load_data()
    mats = d.get("materials", {})
    res = []
    for mid, m in mats.items():
        cur = m.get("current_stock", 0.0)
        mins = m.get("min_stock", 0.0)
        status = "ok"
        if cur <= 0: status = "shortage"
        elif cur <= mins: status = "critical"
        
        m_copy = dict(m)
        m_copy["status"] = status
        res.append(m_copy)
    res.sort(key=lambda x: (x["category"], x["name"]))
    return res

@app.post("/api/mrp/materials")
def create_material(req: MaterialCreate):
    d = load_data()
    mid = req.id or ("MAT_" + str(uuid.uuid4())[:8].upper())
    if mid in d.setdefault("materials", {}): raise HTTPException(400, "Bu malzeme kodu zaten mevcut")
    d["materials"][mid] = {
        "id": mid,
        "name": req.name,
        "category": req.category,
        "unit": req.unit,
        "current_stock": float(req.current_stock),
        "min_stock": float(req.min_stock),
        "unit_price": float(req.unit_price or 0),
        "notes": req.notes or ""
    }
    save_data(d)
    return {"id": mid, "status": "ok"}

@app.put("/api/mrp/materials/{mid}")
def update_material(mid: str, req: MaterialUpdate):
    d = load_data()
    if mid not in d.get("materials", {}): raise HTTPException(404, "Malzeme bulunamadı")
    for k, v in req.dict(exclude_none=True).items(): d["materials"][mid][k] = v
    save_data(d)
    return {"status": "ok"}

@app.delete("/api/mrp/materials/{mid}")
def delete_material(mid: str):
    d = load_data()
    if mid not in d.get("materials", {}): raise HTTPException(404, "Malzeme bulunamadı")
    del d["materials"][mid]
    save_data(d)
    return {"status": "ok"}

@app.post("/api/mrp/materials/{mid}/stock")
def adjust_stock(mid: str, req: StockAdjustment):
    d = load_data()
    if mid not in d.get("materials", {}): raise HTTPException(404, "Malzeme bulunamadı")
    m = d["materials"][mid]
    cur = float(m.get("current_stock", 0.0))
    if req.operation == "in": cur += float(req.change_qty)
    elif req.operation == "out": cur = max(0.0, cur - float(req.change_qty))
    elif req.operation == "set": cur = max(0.0, float(req.change_qty))
    m["current_stock"] = round(cur, 2)
    save_data(d)
    return {"status": "ok", "current_stock": m["current_stock"]}

@app.get("/api/mrp/requirements")
def mrp_requirements_alias(facility_id: Optional[str] = "all", time_scope: Optional[str] = "all_open"):
    return calculate_mrp(facility_id=facility_id, time_scope=time_scope)

@app.get("/api/mrp/calculation")
def calculate_mrp(facility_id: Optional[str] = "all", time_scope: Optional[str] = "all_open"):
    d = load_data()
    orders = d.get("orders", {})
    daily = d.get("daily_entries", {})
    materials = d.get("materials", {})
    today_dt = date.today()
    
    selected_orders = []
    for oid, o in orders.items():
        if o.get("status") != "open": continue
        if facility_id and facility_id != "all" and o.get("facility_id") != facility_id:
            continue
            
        if time_scope == "this_week":
            try:
                deliv_dt = date.fromisoformat(o.get("delivery_date", ""))
                diff = (deliv_dt - today_dt).days
                if diff > 7: continue
            except: pass
        elif time_scope == "critical":
            try:
                deliv_dt = date.fromisoformat(o.get("delivery_date", ""))
                diff = (deliv_dt - today_dt).days
                if diff > 3: continue
            except: pass
                
        total_out = sum(oe.get("output_qty", 0) for dd in daily.values() for oe in dd.get("order_entries", []) if oe.get("order_id") == oid)
        qty = o.get("qty", 0)
        remaining = max(0, qty - total_out)
        if remaining > 0:
            o_copy = dict(o)
            o_copy["remaining_qty"] = remaining
            o_copy["produced_qty"] = total_out
            selected_orders.append(o_copy)
            
    total_doors = sum(o["remaining_qty"] for o in selected_orders)
    
    gross_req = {mid: 0.0 for mid in materials.keys()}
    affected_orders = {mid: [] for mid in materials.keys()}
    
    for o in selected_orders:
        ono = o.get("order_no", o.get("id"))
        rem = o.get("remaining_qty", 0)
        m = o.get("model", "").upper()
        
        if "MAT_SEREN_KOMP" in gross_req:
            gross_req["MAT_SEREN_KOMP"] += rem * 5.8
            affected_orders["MAT_SEREN_KOMP"].append(ono)
        if "MAT_KENAR_BANDI" in gross_req:
            gross_req["MAT_KENAR_BANDI"] += rem * 5.8
            affected_orders["MAT_KENAR_BANDI"].append(ono)
        if "MAT_TUTKAL_PRES" in gross_req:
            gross_req["MAT_TUTKAL_PRES"] += rem * 0.35
            affected_orders["MAT_TUTKAL_PRES"].append(ono)
        if "MAT_KILIT_TAKOZ" in gross_req:
            gross_req["MAT_KILIT_TAKOZ"] += rem * 2
            affected_orders["MAT_KILIT_TAKOZ"].append(ono)
        
        if "PETEK" in m:
            if "MAT_PETEK_KRAFT" in gross_req:
                gross_req["MAT_PETEK_KRAFT"] += rem * 1
                affected_orders["MAT_PETEK_KRAFT"].append(ono)
        else:
            if "MAT_STRAFOR_EPS" in gross_req:
                gross_req["MAT_STRAFOR_EPS"] += rem * 1
                affected_orders["MAT_STRAFOR_EPS"].append(ono)
            
        skin_mat = "MAT_MDF_STD"
        if "B.TEAK" in m or "B. TEAK" in m: skin_mat = "MAT_MDF_BTEAK"
        elif "TEAK" in m: skin_mat = "MAT_MDF_TEAK"
        elif "BEYAZ" in m: skin_mat = "MAT_MDF_BEYAZ"
        elif "ANTRAS" in m: skin_mat = "MAT_MDF_ANTRASIT"
        elif "SOMONO" in m: skin_mat = "MAT_MDF_SOMONO"
            
        if skin_mat in gross_req:
            gross_req[skin_mat] += rem * 2
            affected_orders[skin_mat].append(ono)
        elif "MAT_MDF_STD" in gross_req:
            gross_req["MAT_MDF_STD"] += rem * 2
            affected_orders["MAT_MDF_STD"].append(ono)
            
    requirements = []
    purchase_advice = []
    shortage_count = 0
    critical_count = 0
    total_purchase_cost = 0.0
    
    for mid, mat in materials.items():
        g_req = round(gross_req.get(mid, 0.0), 1)
        cur_stock = round(mat.get("current_stock", 0.0), 1)
        min_stock = round(mat.get("min_stock", 0.0), 1)
        price = mat.get("unit_price", 0.0)
        
        if cur_stock < g_req:
            net_shortage = round((g_req + min_stock) - cur_stock, 1)
            status = "shortage"
            shortage_count += 1
        elif cur_stock < (g_req + min_stock):
            net_shortage = round((g_req + min_stock) - cur_stock, 1)
            status = "critical"
            critical_count += 1
        else:
            net_shortage = 0.0
            status = "ok"
            
        coverage_pct = round((cur_stock / g_req * 100), 1) if g_req > 0 else 100.0
        p_cost = round(net_shortage * price, 2)
        if net_shortage > 0:
            total_purchase_cost += p_cost
        
        item = {
            "id": mid,
            "name": mat.get("name", mid),
            "category": mat.get("category", "Genel"),
            "unit": mat.get("unit", "Adet"),
            "gross_required": g_req,
            "current_stock": cur_stock,
            "min_stock": min_stock,
            "net_shortage": net_shortage,
            "status": status,
            "coverage_pct": min(100.0, coverage_pct),
            "unit_price": price,
            "purchase_cost": p_cost,
            "affected_orders_count": len(set(affected_orders.get(mid, []))),
            "notes": mat.get("notes", "")
        }
        requirements.append(item)
        if net_shortage > 0:
            purchase_advice.append(item)
            
    purchase_advice.sort(key=lambda x: (x["status"] != "shortage", -x["purchase_cost"]))
    requirements.sort(key=lambda x: (x["status"] != "shortage", x["status"] != "critical", x["category"]))
    
    fulfillment_rate = round(((len(requirements) - shortage_count) / len(requirements) * 100), 1) if requirements else 100.0
    
    return {
        "summary": {
            "facility_id": facility_id,
            "time_scope": time_scope,
            "orders_count": len(selected_orders),
            "total_doors": total_doors,
            "materials_count": len(requirements),
            "shortage_count": shortage_count,
            "critical_count": critical_count,
            "fulfillment_rate": fulfillment_rate,
            "total_purchase_cost": round(total_purchase_cost, 2)
        },
        "requirements": requirements,
        "purchase_advice": purchase_advice,
        "bom_standards": [
            {"component": "Seren & Karkas", "spec": "5.8 Metre / Kapı (Boy ve En Seren profili)"},
            {"component": "İç Dolgu", "spec": "1 Adet EPS Strafor (veya Petek Kağıt Dolgu)"},
            {"component": "Yüzey Levhası", "spec": "2 Adet (Ön ve Arka Yüz MDF/WPC 4mm Levha)"},
            {"component": "PVC Kenar Bandı", "spec": "5.8 Metre / Kapı (1mm x 45mm Ebatlama Bandı)"},
            {"component": "Sıcak Pres Tutkalı", "spec": "0.35 Kg / Kapı (Poliüretan/D3 Tutkal)"},
            {"component": "Kilit Takozu", "spec": "2 Adet / Kapı (Ahşap Takviye Takozu)"}
        ]
    }

# ── DASHBOARD ─────────────────────────────────────────────

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
        nxt = start_dt.replace(day=28) + timedelta(days=4)
        end_dt = nxt - timedelta(days=nxt.day)
        
    def in_range(ds):
        try:
            dt = date.fromisoformat(ds)
            return start_dt <= dt <= end_dt
        except: return False

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
            except: pass
                
    total_out_period = 0
    fac1_out = 0
    fac2_out = 0
    
    for dk, dd in daily.items():
        if not in_range(dk): continue
        for oe in dd.get("order_entries", []):
            oid = oe.get("order_id")
            o = orders.get(oid, {})
            f_id = o.get("facility_id")
            if facility_id and facility_id != "all" and f_id != facility_id: continue
            qty = oe.get("output_qty", 0)
            total_out_period += qty
            if f_id == "fac1": fac1_out += qty
            elif f_id == "fac2": fac2_out += qty

    days_arr = []
    curr = start_dt
    while curr <= end_dt:
        ds = curr.isoformat()
        dd = daily.get(ds, {})
        d_out = 0
        for oe in dd.get("order_entries", []):
            o = orders.get(oe.get("order_id"), {})
            if facility_id and facility_id != "all" and o.get("facility_id") != facility_id: continue
            d_out += oe.get("output_qty", 0)
        days_arr.append({
            "date": ds,
            "day_name": ["Pzt","Sal","Çar","Per","Cum","Cmt","Paz"][curr.weekday()] if period == "weekly" else str(curr.day),
            "is_today": ds == today_str,
            "output": d_out
        })
        curr += timedelta(days=1)

    mach_stats = {}
    today_active_workers = 0
    period_man_hours = 0.0
    
    today_data = daily.get(today_str, {})
    for me in today_data.get("machine_entries", []):
        m = machines.get(me.get("machine_id"), {})
        if facility_id and facility_id != "all" and m.get("facility_id") != facility_id: continue
        today_active_workers += int(me.get("worker_count", 1) or 1)
        
    for dk, dd in daily.items():
        if not in_range(dk): continue
        for me in dd.get("machine_entries", []):
            mid = me.get("machine_id")
            m = machines.get(mid, {})
            if facility_id and facility_id != "all" and m.get("facility_id") != facility_id: continue
            
            if mid not in mach_stats:
                mach_stats[mid] = {
                    "id": mid,
                    "name": m.get("name", mid),
                    "facility_id": m.get("facility_id", "fac1"),
                    "output": 0,
                    "hours": 0.0,
                    "worker_count": 0,
                    "man_hours": 0.0
                }
            
            output = me.get("output_qty", 0)
            hours = float(me.get("work_hours", 0.0))
            workers = int(me.get("worker_count", 1) or 1)
            man_h = hours * workers
            
            mach_stats[mid]["output"] += output
            mach_stats[mid]["hours"] += hours
            mach_stats[mid]["worker_count"] = max(mach_stats[mid]["worker_count"], workers)
            mach_stats[mid]["man_hours"] += man_h
            period_man_hours += man_h

    ms_list = []
    for ms in mach_stats.values():
        eff = round(ms["output"] / ms["hours"], 1) if ms["hours"] > 0 else float(ms["output"])
        man_eff = round(ms["output"] / ms["man_hours"], 1) if ms["man_hours"] > 0 else float(ms["output"])
        ms["efficiency"] = eff
        ms["man_hour_efficiency"] = man_eff
        ms["hours"] = round(ms["hours"], 1)
        ms["man_hours"] = round(ms["man_hours"], 1)
        ms_list.append(ms)
        
    ms_list.sort(key=lambda x: x["output"], reverse=True)

    # Scraps summary for dashboard
    scraps = d.get("scraps", {})
    total_scraps = sum(s.get("qty", 0) for s in scraps.values())
    
    # Shipments active count
    shipments = d.get("shipments", {})
    active_shipments = len([s for s in shipments.values() if s.get("status") in ["preparing", "loaded"]])

    return {
        "orders": {"total": total_orders, "open": open_orders, "done": done_orders},
        "period_summary": {
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat(),
            "total_output": total_out_period,
            "days": days_arr,
            "fac1_output": fac1_out,
            "fac2_output": fac2_out,
            "today_active_workers": today_active_workers,
            "period_man_hours": round(period_man_hours, 1),
            "total_scraps": total_scraps,
            "active_shipments": active_shipments
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