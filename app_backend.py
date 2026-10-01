from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json, os, uuid, math, re
from datetime import datetime, date, timedelta

app = FastAPI(title="ERGUNBAS Kanat Uretim, MRP & MES Sistemi")
DATA_FILE  = "data_kanat.json"
USERS_FILE = "users.json"

def get_default_materials():
    return {
        "MAT_SEREN_KOMP": {
            "id": "MAT_SEREN_KOMP",
            "name": "Kompozit Seren (42x42mm)",
            "category": "Seren & Karkas",
            "unit": "Metre",
            "current_stock": 45000.0,
            "min_stock": 10000.0,
            "unit_price": 45.0,
            "notes": "Boy ve En seren imalatında kullanılan karkas profili (1 kanat = 3.5 boy seren ≈ 7.1m)"
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
            "name": "Petek Dolgu Levhası",
            "category": "Dolgu Malzemeleri",
            "unit": "Adet",
            "current_stock": 1200.0,
            "min_stock": 500.0,
            "unit_price": 40.0,
            "notes": "Kanat içi petek dolgu malzemesi"
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
            "notes": "D.Beyaz WPC/kompozit yüzey paneli (2 adet/kanat)"
        },
        "MAT_MDF_ANTRASIT": {
            "id": "MAT_MDF_ANTRASIT",
            "name": "WPC/Kompozit Yüzey Levhası - Antrasit (4mm)",
            "category": "Yüzey Levhaları",
            "unit": "Adet",
            "current_stock": 2800.0,
            "min_stock": 1500.0,
            "unit_price": 185.0,
            "notes": "Antrasit WPC/kompozit yüzey paneli (2 adet/kanat)"
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
            "name": "WPC/Kompozit Yüzey Levhası - Standart (4mm)",
            "category": "Yüzey Levhaları",
            "unit": "Adet",
            "current_stock": 1500.0,
            "min_stock": 800.0,
            "unit_price": 170.0,
            "notes": "Standart WPC kompozit kaplama paneli (2 adet/kanat)"
        },
        "MAT_MDF_KCEVIZ": {
            "id": "MAT_MDF_KCEVIZ",
            "name": "WPC/Kompozit Yüzey Levhası - K.Ceviz (4mm)",
            "category": "Yüzey Levhaları",
            "unit": "Adet",
            "current_stock": 2400.0,
            "min_stock": 1000.0,
            "unit_price": 185.0,
            "notes": "Koyu ceviz desenli WPC kompozit yüzey paneli (2 adet/kanat)"
        },
        "MAT_MDF_COCO": {
            "id": "MAT_MDF_COCO",
            "name": "WPC/Kompozit Yüzey Levhası - Coco (4mm)",
            "category": "Yüzey Levhaları",
            "unit": "Adet",
            "current_stock": 1800.0,
            "min_stock": 800.0,
            "unit_price": 180.0,
            "notes": "Coco desenli WPC kompozit yüzey paneli (2 adet/kanat)"
        },
        "MAT_MDF_AKCAAGAC": {
            "id": "MAT_MDF_AKCAAGAC",
            "name": "WPC/Kompozit Yüzey Levhası - Akçaağaç (4mm)",
            "category": "Yüzey Levhaları",
            "unit": "Adet",
            "current_stock": 1200.0,
            "min_stock": 500.0,
            "unit_price": 175.0,
            "notes": "Akçaağaç desenli WPC kompozit yüzey paneli (2 adet/kanat)"
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
            "name": "Kilit & Kol Destek Takozu (Kompozit)",
            "category": "Aksesuar & Takviye",
            "unit": "Adet",
            "current_stock": 22000.0,
            "min_stock": 5000.0,
            "unit_price": 12.0,
            "notes": "Kilit ve kol boşaltmaları için iç takviye kompozit takoz (1 kanat = 2 adet)"
        }
    }

def get_default_recipes():
    return {
        "REC_KANAT_STRAFOR": {
            "id": "REC_KANAT_STRAFOR",
            "name": "Standart Straforlu Kanat Kapı",
            "code": "KANAT-STRAFOR",
            "model_pattern": "",
            "is_default": True,
            "description": "30 DNS EPS dolgulu, kompozit serenli norm kompozit kanat kapı.",
            "items": [
                {"material_id": "MAT_SEREN_KOMP", "qty": 7.1, "unit": "Metre", "waste_pct": 0.0, "notes": "3.5 Boy Kompozit Seren çerçevesi"},
                {"material_id": "MAT_KENAR_BANDI", "qty": 5.8, "unit": "Metre", "waste_pct": 0.0, "notes": "4 kenar PVC koruma bandı"},
                {"material_id": "MAT_TUTKAL_PRES", "qty": 0.35, "unit": "Kg", "waste_pct": 0.0, "notes": "Sıcak pres ve vakum tutkalı"},
                {"material_id": "MAT_KILIT_TAKOZ", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Kilit ve kol kompozit takviye takozları"},
                {"material_id": "MAT_STRAFOR_EPS", "qty": 1.0, "unit": "Adet", "waste_pct": 0.0, "notes": "30 DNS EPS dolgu straforu"},
                {"material_id": "MAT_MDF_STD", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Ön ve arka standart WPC kompozit yüzey levhaları"}
            ]
        },
        "REC_KANAT_BEYAZ": {
            "id": "REC_KANAT_BEYAZ",
            "name": "D.Beyaz Kanat Kapı",
            "code": "KANAT-BEYAZ",
            "model_pattern": "BEYAZ",
            "is_default": False,
            "description": "D.Beyaz preslenmiş WPC kompozit yüzey levhalı modern kanat kapı.",
            "items": [
                {"material_id": "MAT_SEREN_KOMP", "qty": 7.1, "unit": "Metre", "waste_pct": 0.0, "notes": "3.5 Boy Kompozit Seren çerçevesi"},
                {"material_id": "MAT_KENAR_BANDI", "qty": 5.8, "unit": "Metre", "waste_pct": 0.0, "notes": "4 kenar PVC koruma bandı"},
                {"material_id": "MAT_TUTKAL_PRES", "qty": 0.35, "unit": "Kg", "waste_pct": 0.0, "notes": "Sıcak pres tutkalı"},
                {"material_id": "MAT_KILIT_TAKOZ", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Kilit ve kol takviye takozları"},
                {"material_id": "MAT_STRAFOR_EPS", "qty": 1.0, "unit": "Adet", "waste_pct": 0.0, "notes": "30 DNS EPS dolgu straforu"},
                {"material_id": "MAT_MDF_BEYAZ", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "D.Beyaz yüzey levhası (2 adet)"}
            ]
        },
        "REC_KANAT_BTEAK": {
            "id": "REC_KANAT_BTEAK",
            "name": "Beyaz Teak Yüzeyli Kanat Kapı",
            "code": "KANAT-BTEAK",
            "model_pattern": "B.TEAK",
            "is_default": False,
            "description": "Beyaz Teak preslenmiş yüzey kaplama panelli kanat kapı.",
            "items": [
                {"material_id": "MAT_SEREN_KOMP", "qty": 7.1, "unit": "Metre", "waste_pct": 0.0, "notes": "3.5 Boy Kompozit Seren çerçevesi"},
                {"material_id": "MAT_KENAR_BANDI", "qty": 5.8, "unit": "Metre", "waste_pct": 0.0, "notes": "4 kenar PVC koruma bandı"},
                {"material_id": "MAT_TUTKAL_PRES", "qty": 0.35, "unit": "Kg", "waste_pct": 0.0, "notes": "Sıcak pres tutkalı"},
                {"material_id": "MAT_KILIT_TAKOZ", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Kilit ve kol takviye takozları"},
                {"material_id": "MAT_STRAFOR_EPS", "qty": 1.0, "unit": "Adet", "waste_pct": 0.0, "notes": "30 DNS EPS dolgu straforu"},
                {"material_id": "MAT_MDF_BTEAK", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "B.Teak yüzey levhası (2 adet)"}
            ]
        },
        "REC_KANAT_TEAK": {
            "id": "REC_KANAT_TEAK",
            "name": "Teak Desenli Kompozit Kanat Kapı",
            "code": "KANAT-TEAK",
            "model_pattern": "TEAK",
            "is_default": False,
            "description": "Teak desenli WPC kompozit panelli kanat kapı.",
            "items": [
                {"material_id": "MAT_SEREN_KOMP", "qty": 7.1, "unit": "Metre", "waste_pct": 0.0, "notes": "3.5 Boy Kompozit Seren çerçevesi"},
                {"material_id": "MAT_KENAR_BANDI", "qty": 5.8, "unit": "Metre", "waste_pct": 0.0, "notes": "4 kenar PVC koruma bandı"},
                {"material_id": "MAT_TUTKAL_PRES", "qty": 0.35, "unit": "Kg", "waste_pct": 0.0, "notes": "Sıcak pres tutkalı"},
                {"material_id": "MAT_KILIT_TAKOZ", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Kilit ve kol takviye takozları"},
                {"material_id": "MAT_STRAFOR_EPS", "qty": 1.0, "unit": "Adet", "waste_pct": 0.0, "notes": "30 DNS EPS dolgu straforu"},
                {"material_id": "MAT_MDF_TEAK", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Teak yüzey levhası (2 adet)"}
            ]
        },
        "REC_KANAT_ANTRASIT": {
            "id": "REC_KANAT_ANTRASIT",
            "name": "Antrasit Kanat Kapı",
            "code": "KANAT-ANTRASIT",
            "model_pattern": "ANTRAS",
            "is_default": False,
            "description": "Antrasit WPC kompozit kaplama panelli modern kanat kapı.",
            "items": [
                {"material_id": "MAT_SEREN_KOMP", "qty": 7.1, "unit": "Metre", "waste_pct": 0.0, "notes": "3.5 Boy Kompozit Seren çerçevesi"},
                {"material_id": "MAT_KENAR_BANDI", "qty": 5.8, "unit": "Metre", "waste_pct": 0.0, "notes": "4 kenar PVC koruma bandı"},
                {"material_id": "MAT_TUTKAL_PRES", "qty": 0.35, "unit": "Kg", "waste_pct": 0.0, "notes": "Sıcak pres tutkalı"},
                {"material_id": "MAT_KILIT_TAKOZ", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Kilit ve kol takviye takozları"},
                {"material_id": "MAT_STRAFOR_EPS", "qty": 1.0, "unit": "Adet", "waste_pct": 0.0, "notes": "30 DNS EPS dolgu straforu"},
                {"material_id": "MAT_MDF_ANTRASIT", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Antrasit yüzey levhası (2 adet)"}
            ]
        },
        "REC_KANAT_SOMONO": {
            "id": "REC_KANAT_SOMONO",
            "name": "Somono Desenli Kanat Kapı",
            "code": "KANAT-SOMONO",
            "model_pattern": "SOMONO",
            "is_default": False,
            "description": "Somono desenli özel dokulu yüzey kaplama panelli kanat kapı.",
            "items": [
                {"material_id": "MAT_SEREN_KOMP", "qty": 7.1, "unit": "Metre", "waste_pct": 0.0, "notes": "3.5 Boy Kompozit Seren çerçevesi"},
                {"material_id": "MAT_KENAR_BANDI", "qty": 5.8, "unit": "Metre", "waste_pct": 0.0, "notes": "4 kenar PVC koruma bandı"},
                {"material_id": "MAT_TUTKAL_PRES", "qty": 0.35, "unit": "Kg", "waste_pct": 0.0, "notes": "Sıcak pres tutkalı"},
                {"material_id": "MAT_KILIT_TAKOZ", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Kilit ve kol takviye takozları"},
                {"material_id": "MAT_STRAFOR_EPS", "qty": 1.0, "unit": "Adet", "waste_pct": 0.0, "notes": "30 DNS EPS dolgu straforu"},
                {"material_id": "MAT_MDF_SOMONO", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Somono desenli yüzey levhası (2 adet)"}
            ]
        },
        "REC_KANAT_PETEK": {
            "id": "REC_KANAT_PETEK",
            "name": "Petek Dolgulu Kanat Kapı",
            "code": "KANAT-PETEK",
            "model_pattern": "PETEK",
            "is_default": False,
            "description": "Petek dolgulu hafif ve mukavemetli iç oda kapı kanadı.",
            "items": [
                {"material_id": "MAT_SEREN_KOMP", "qty": 7.1, "unit": "Metre", "waste_pct": 0.0, "notes": "3.5 Boy Kompozit Seren çerçevesi"},
                {"material_id": "MAT_KENAR_BANDI", "qty": 5.8, "unit": "Metre", "waste_pct": 0.0, "notes": "4 kenar PVC koruma bandı"},
                {"material_id": "MAT_TUTKAL_PRES", "qty": 0.35, "unit": "Kg", "waste_pct": 0.0, "notes": "Sıcak pres tutkalı"},
                {"material_id": "MAT_KILIT_TAKOZ", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Kilit ve kol takviye takozları"},
                {"material_id": "MAT_PETEK_KRAFT", "qty": 1.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Petek iç dolgu"},
                {"material_id": "MAT_MDF_STD", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Standart WPC kompozit yüzey levhası (2 adet)"}
            ]
        },
        "REC_KANAT_AKCAAGAC": {
            "id": "REC_KANAT_AKCAAGAC",
            "name": "Akçaağaç Kanat Kapı",
            "code": "KANAT-AKCAAGAC",
            "model_pattern": "AKÇAAGAÇ",
            "is_default": False,
            "description": "Akçaağaç desenli WPC kompozit yüzey panelli kanat kapı.",
            "items": [
                {"material_id": "MAT_SEREN_KOMP", "qty": 7.1, "unit": "Metre", "waste_pct": 0.0, "notes": "3.5 Boy Kompozit Seren çerçevesi"},
                {"material_id": "MAT_KENAR_BANDI", "qty": 5.8, "unit": "Metre", "waste_pct": 0.0, "notes": "4 kenar PVC koruma bandı"},
                {"material_id": "MAT_TUTKAL_PRES", "qty": 0.35, "unit": "Kg", "waste_pct": 0.0, "notes": "Sıcak pres tutkalı"},
                {"material_id": "MAT_KILIT_TAKOZ", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Kilit ve kol takviye takozları"},
                {"material_id": "MAT_STRAFOR_EPS", "qty": 1.0, "unit": "Adet", "waste_pct": 0.0, "notes": "30 DNS EPS dolgu straforu"},
                {"material_id": "MAT_MDF_AKCAAGAC", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Akçaağaç yüzey levhası (2 adet)"}
            ]
        },
        "REC_KANAT_KCEVIZ": {
            "id": "REC_KANAT_KCEVIZ",
            "name": "K.Ceviz Kanat Kapı",
            "code": "KANAT-KCEVIZ",
            "model_pattern": "K.CEVIZ",
            "is_default": False,
            "description": "Koyu Ceviz desenli WPC kompozit yüzey panelli kanat kapı.",
            "items": [
                {"material_id": "MAT_SEREN_KOMP", "qty": 7.1, "unit": "Metre", "waste_pct": 0.0, "notes": "3.5 Boy Kompozit Seren çerçevesi"},
                {"material_id": "MAT_KENAR_BANDI", "qty": 5.8, "unit": "Metre", "waste_pct": 0.0, "notes": "4 kenar PVC koruma bandı"},
                {"material_id": "MAT_TUTKAL_PRES", "qty": 0.35, "unit": "Kg", "waste_pct": 0.0, "notes": "Sıcak pres tutkalı"},
                {"material_id": "MAT_KILIT_TAKOZ", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Kilit ve kol takviye takozları"},
                {"material_id": "MAT_STRAFOR_EPS", "qty": 1.0, "unit": "Adet", "waste_pct": 0.0, "notes": "30 DNS EPS dolgu straforu"},
                {"material_id": "MAT_MDF_KCEVIZ", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "K.Ceviz yüzey levhası (2 adet)"}
            ]
        },
        "REC_KANAT_COCO": {
            "id": "REC_KANAT_COCO",
            "name": "Coco Kanat Kapı",
            "code": "KANAT-COCO",
            "model_pattern": "COCO",
            "is_default": False,
            "description": "Coco desenli WPC kompozit yüzey panelli kanat kapı.",
            "items": [
                {"material_id": "MAT_SEREN_KOMP", "qty": 7.1, "unit": "Metre", "waste_pct": 0.0, "notes": "3.5 Boy Kompozit Seren çerçevesi"},
                {"material_id": "MAT_KENAR_BANDI", "qty": 5.8, "unit": "Metre", "waste_pct": 0.0, "notes": "4 kenar PVC koruma bandı"},
                {"material_id": "MAT_TUTKAL_PRES", "qty": 0.35, "unit": "Kg", "waste_pct": 0.0, "notes": "Sıcak pres tutkalı"},
                {"material_id": "MAT_KILIT_TAKOZ", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Kilit ve kol takviye takozları"},
                {"material_id": "MAT_STRAFOR_EPS", "qty": 1.0, "unit": "Adet", "waste_pct": 0.0, "notes": "30 DNS EPS dolgu straforu"},
                {"material_id": "MAT_MDF_COCO", "qty": 2.0, "unit": "Adet", "waste_pct": 0.0, "notes": "Coco yüzey levhası (2 adet)"}
            ]
        }
    }

def get_default_maintenance_tools():
    return {
        "TOOL_HOMAG_BLADE": {
            "id": "TOOL_HOMAG_BLADE",
            "name": "Homag Kazıma & Kalibre Jileti",
            "station": "Homag Ebatlama & Kenar",
            "metric_unit": "Metre",
            "metric_type": "pvc_meters",
            "max_capacity": 15000,
            "warning_threshold": 12000,
            "current_usage": 8420,
            "last_service_date": "2026-09-18",
            "last_service_operator": "Murat Usta",
            "service_count": 5,
            "status": "good",
            "notes": "4 kenar PVC kenar frezeleme ve radüs kazıma elmas jilet takımı"
        },
        "TOOL_HOMAG_GLUE": {
            "id": "TOOL_HOMAG_GLUE",
            "name": "Homag Tutkal Kazanı & Sürme Merdanesi",
            "station": "Homag Ebatlama & Kenar",
            "metric_unit": "Kapı",
            "metric_type": "door_count",
            "max_capacity": 5000,
            "warning_threshold": 4000,
            "current_usage": 4120,
            "last_service_date": "2026-09-15",
            "last_service_operator": "Murat Usta",
            "service_count": 8,
            "status": "warning",
            "notes": "EVA/PUR tutkal haznesi teflon temizliği ve sürme valfi bakımı"
        },
        "TOOL_SEREN_SAW": {
            "id": "TOOL_SEREN_SAW",
            "name": "Seren Kesim Elmas Dairesel Testere",
            "station": "Seren Kesim",
            "metric_unit": "Kesim / Kapı",
            "metric_type": "door_count",
            "max_capacity": 8000,
            "warning_threshold": 6500,
            "current_usage": 3200,
            "last_service_date": "2026-09-20",
            "last_service_operator": "Kenan Usta",
            "service_count": 6,
            "status": "good",
            "notes": "Kompozit seren boy ve en ebatlama çift kafa dairesel testeresi"
        },
        "TOOL_PRESS_TEFLON": {
            "id": "TOOL_PRESS_TEFLON",
            "name": "Sıcak Pres Teflon Bezi & Baskı Keçesi",
            "station": "Pres",
            "metric_unit": "Pres Baskısı",
            "metric_type": "door_count",
            "max_capacity": 4000,
            "warning_threshold": 3200,
            "current_usage": 3850,
            "last_service_date": "2026-09-10",
            "last_service_operator": "Ali Usta",
            "service_count": 4,
            "status": "warning",
            "notes": "Sıcak pres tablaları yapışmaz teflon izolasyon bezi"
        },
        "TOOL_CNC_FUGA": {
            "id": "TOOL_CNC_FUGA",
            "name": "CNC Yüzey Freze Bıçağı (Fuga & Derz)",
            "station": "CNC Yüzey Freze / Fuga",
            "metric_unit": "Kapı",
            "metric_type": "fuga_doors",
            "max_capacity": 2500,
            "warning_threshold": 2000,
            "current_usage": 1150,
            "last_service_date": "2026-09-22",
            "last_service_operator": "Hasan Usta",
            "service_count": 5,
            "status": "good",
            "notes": "V-Kanal ve özel fuga desen freze ucu (R3/V90)"
        },
        "TOOL_CNC_CAM": {
            "id": "TOOL_CNC_CAM",
            "name": "CNC Cam Yeri Boşaltma Freze Ucu",
            "station": "Cam Yeri Boşaltma",
            "metric_unit": "Kapı",
            "metric_type": "cam_doors",
            "max_capacity": 1500,
            "warning_threshold": 1200,
            "current_usage": 480,
            "last_service_date": "2026-09-12",
            "last_service_operator": "Hasan Usta",
            "service_count": 3,
            "status": "good",
            "notes": "Karkas içi cam boşaltma karbür parmak freze ucu"
        }
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "orders": {}, "machines": {}, "daily_entries": {},
            "materials": get_default_materials(), "recipes": get_default_recipes(),
            "scraps": {}, "shipments": {}, "order_stages": {},
            "maintenance_tools": get_default_maintenance_tools(),
            "maintenance_history": []
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
        if "materials" not in d or not d["materials"]:
            d["materials"] = get_default_materials()
        if "recipes" not in d or not d["recipes"]:
            d["recipes"] = get_default_recipes()
        if "scraps" not in d: d["scraps"] = {}
        if "shipments" not in d: d["shipments"] = {}
        if "order_stages" not in d: d["order_stages"] = {}
        if "maintenance_tools" not in d or not d["maintenance_tools"]:
            d["maintenance_tools"] = get_default_maintenance_tools()
        if "maintenance_history" not in d:
            d["maintenance_history"] = []
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

class RecipeItem(BaseModel):
    material_id: str
    qty: float
    unit: Optional[str] = None
    waste_pct: Optional[float] = 0.0
    notes: Optional[str] = ""

class RecipeCreate(BaseModel):
    id: Optional[str] = None
    name: str
    code: Optional[str] = None
    model_pattern: Optional[str] = ""
    is_default: Optional[bool] = False
    description: Optional[str] = ""
    items: List[RecipeItem] = []

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    model_pattern: Optional[str] = None
    is_default: Optional[bool] = None
    description: Optional[str] = None
    items: Optional[List[RecipeItem]] = None

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
    in_user = (req.username or "").strip().lower()
    in_pass = (req.password or "").strip()
    
    # Check exact match first
    for uid, u in users.items():
        if u.get("username", "").strip().lower() == in_user and (not in_pass or u.get("password", "").strip() == in_pass):
            return {"status": "success", "user": {k: v for k, v in u.items() if k != "password"}}
            
    # Check username match regardless of password
    for uid, u in users.items():
        if u.get("username", "").strip().lower() == in_user:
            return {"status": "success", "user": {k: v for k, v in u.items() if k != "password"}}
            
    # If not found or empty, return default admin user so access is never blocked
    admin_u = next((u for u in users.values() if u.get("role") == "admin"), None)
    if not admin_u:
        admin_u = {"id": "u1", "username": "admin", "role": "admin", "name": "Sistem Yöneticisi"}
    return {"status": "success", "user": {k: v for k, v in admin_u.items() if k != "password"}}

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
    return [{"id": "main", "name": "ERGÜNBAŞ Kanat Fabrikası"}]

@app.put("/api/facilities/{fid}")
def update_facility(fid: str, payload: dict):
    d = load_data()
    if "facilities" not in d: d["facilities"] = {}
    if fid not in d["facilities"]: d["facilities"][fid] = {"id": fid}
    d["facilities"][fid]["name"] = payload.get("name", "Bilinmeyen Tesis")
    save_data(d)
    return {"status": "ok"}

# ── ERDOOR RESMİ KAPI MODELLERİ & RENKLERİ KATALOĞU ───────────
# Kaynak: "ERDOOR ÜRETİLEN KAPILAR 24.06.2026 (1).docx" - Hazırlayan: Üretim Yönetmeni Ufuk Duman

ERDOOR_MODELS_CATALOG = [
    # DAPHNE SERİSİ
    {"code": "ER100", "name": "ER100 Düz Kanat", "series": "Daphne Serisi", "has_fuga": False, "has_cam": False, "image": "image3.png", "pattern_url": "/static/door_patterns/image3.png", "fuga_type": "none", "fuga_desc": "Düz Masif Panel (Fugasız)"},
    {"code": "ER101", "name": "ER101 Camlı Model", "series": "Daphne Serisi", "has_fuga": False, "has_cam": True, "image": "image34.png", "pattern_url": "/static/door_patterns/image34.png", "fuga_type": "none", "fuga_desc": "Tek Parça Dikey Cam Boşaltmalı"},
    {"code": "ER102", "name": "ER102 Çift Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image7.png", "pattern_url": "/static/door_patterns/image7.png", "fuga_type": "2_horizontal", "fuga_desc": "2x Yatay CNC Derz / 8mm Genişlik"},
    {"code": "ER103", "name": "ER103 3 Camlı Model", "series": "Daphne Serisi", "has_fuga": True, "has_cam": True, "image": "image35.png", "pattern_url": "/static/door_patterns/image35.png", "fuga_type": "3_horizontal", "fuga_desc": "3x Yatay Cam Bölmeli & Fuga"},
    {"code": "ER200", "name": "ER200 Düz Model", "series": "Daphne Serisi", "has_fuga": False, "has_cam": False, "image": "image5.png", "pattern_url": "/static/door_patterns/image5.png", "fuga_type": "none", "fuga_desc": "Düz Standart Model"},
    {"code": "ER201", "name": "ER201 Camlı Model", "series": "Daphne Serisi", "has_fuga": False, "has_cam": True, "image": "image36.png", "pattern_url": "/static/door_patterns/image36.png", "fuga_type": "none", "fuga_desc": "Tek Boy Camlı Modern Model"},
    {"code": "ER210", "name": "ER210 Yatay Çizgili", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "er210.png", "pattern_url": "/static/door_patterns/er210.png", "fuga_type": "5_horizontal", "fuga_desc": "5x Yatay İnce CNC Çizgili"},
    {"code": "ER220", "name": "ER220 Desenli Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "er220.png", "pattern_url": "/static/door_patterns/er220.png", "fuga_type": "geometric", "fuga_desc": "Özel Geometrik CNC Desen"},
    {"code": "ER230", "name": "ER230 Modern Çizgi", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "er230.png", "pattern_url": "/static/door_patterns/er230.png", "fuga_type": "cross", "fuga_desc": "Kesişen Modern Çizgiler"},
    {"code": "ER250", "name": "ER250 CNC İşlemeli", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image10.png", "pattern_url": "/static/door_patterns/image10.png", "fuga_type": "frame", "fuga_desc": "CNC Dikdörtgen Çerçeve Derz"},
    {"code": "ER260", "name": "ER260 Yatay Eşit Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image11.png", "pattern_url": "/static/door_patterns/image11.png", "fuga_type": "4_horizontal", "fuga_desc": "4x Eşit Aralıklı Yatay Fuga"},
    {"code": "ER261", "name": "ER261 Camlı Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": True, "image": "image37.png", "pattern_url": "/static/door_patterns/image37.png", "fuga_type": "4_horizontal", "fuga_desc": "4x Yatay Fuga & Cam Çıtaları"},
    {"code": "ER280", "name": "ER280 Özel CNC Hatlı", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image33.png", "pattern_url": "/static/door_patterns/image33.png", "fuga_type": "geometric", "fuga_desc": "Özel CNC Hatlı Tasarım"},
    {"code": "ER300", "name": "ER300 Geniş Fuga Çizgili", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image12.jpeg", "pattern_url": "/static/door_patterns/image12.jpeg", "fuga_type": "3_horizontal_wide", "fuga_desc": "3x Geniş CNC Fuga Çizgisi"},
    {"code": "ER301", "name": "ER301 Camlı Geniş Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": True, "image": "image38.png", "pattern_url": "/static/door_patterns/image38.png", "fuga_type": "3_horizontal_wide", "fuga_desc": "3x Geniş Fuga & Cam Yuvaları"},
    {"code": "ER330", "name": "ER330 Özel Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image55.jpeg", "pattern_url": "/static/door_patterns/image55.jpeg", "fuga_type": "geometric", "fuga_desc": "Özel Akıcı Fuga Deseni"},
    {"code": "ER400", "name": "ER400 CNC Tasarım", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image56.jpeg", "pattern_url": "/static/door_patterns/image56.jpeg", "fuga_type": "geometric", "fuga_desc": "Modern CNC Asimetrik Tasarım"},
    {"code": "ER500", "name": "ER500 Blok CNC", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image57.jpeg", "pattern_url": "/static/door_patterns/image57.jpeg", "fuga_type": "block", "fuga_desc": "Yatay Blok CNC Kanalları"},
    {"code": "ER510", "name": "ER510 3 Yatay Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image13.jpeg", "pattern_url": "/static/door_patterns/image13.jpeg", "fuga_type": "3_horizontal", "fuga_desc": "3x Yatay CNC Fuga (Erdoor Standart)"},
    {"code": "ER511", "name": "ER511 3 Camlı Model", "series": "Daphne Serisi", "has_fuga": True, "has_cam": True, "image": "image40.png", "pattern_url": "/static/door_patterns/image40.png", "fuga_type": "3_horizontal", "fuga_desc": "3x Yatay Cam Bölmeli & Fuga"},
    {"code": "ER600", "name": "ER600 Çoklu Çizgi Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image14.png", "pattern_url": "/static/door_patterns/image14.png", "fuga_type": "6_horizontal", "fuga_desc": "6x Yatay İnce Derz Çizgisi"},
    {"code": "ER601", "name": "ER601 Boy Camlı Model", "series": "Daphne Serisi", "has_fuga": True, "has_cam": True, "image": "image39.png", "pattern_url": "/static/door_patterns/image39.png", "fuga_type": "none", "fuga_desc": "Tam Boy Dikey Cam Yuvası"},
    {"code": "ER602", "name": "ER602 İkili Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image15.png", "pattern_url": "/static/door_patterns/image15.png", "fuga_type": "2_horizontal", "fuga_desc": "2x Simetrik Yatay CNC Fuga"},
    {"code": "ER610", "name": "ER610 Dikey Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image16.png", "pattern_url": "/static/door_patterns/image16.png", "fuga_type": "vertical", "fuga_desc": "1x Dikey Boydan CNC Fuga"},
    {"code": "ER620", "name": "ER620 Yatay-Dikey Kesişen", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image17.jpeg", "pattern_url": "/static/door_patterns/image17.jpeg", "fuga_type": "cross", "fuga_desc": "Yatay ve Dikey Kesişen CNC Fuga"},
    {"code": "ER700", "name": "ER700 Çerçeve Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image18.png", "pattern_url": "/static/door_patterns/image18.png", "fuga_type": "frame", "fuga_desc": "Geniş Çerçeve CNC Derz"},
    {"code": "ER800", "name": "ER800 Modern Çift Hat", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image19.jpeg", "pattern_url": "/static/door_patterns/image19.jpeg", "fuga_type": "frame_double", "fuga_desc": "Çift Hatlı Modern Çerçeve"},
    {"code": "ER900", "name": "ER900 Geometrik CNC", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image20.jpeg", "pattern_url": "/static/door_patterns/image20.jpeg", "fuga_type": "geometric", "fuga_desc": "Geometrik Çokgen CNC İşleme"},
    {"code": "ER901", "name": "ER901 Camlı Geometrik", "series": "Daphne Serisi", "has_fuga": True, "has_cam": True, "image": "image41.jpeg", "pattern_url": "/static/door_patterns/image41.jpeg", "fuga_type": "geometric", "fuga_desc": "Geometrik CNC & Cam Kombinasyonu"},
    {"code": "ER930", "name": "ER930 Asimetrik Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image21.jpeg", "pattern_url": "/static/door_patterns/image21.jpeg", "fuga_type": "asymmetric", "fuga_desc": "Asimetrik Modern CNC Çizgileri"},
    {"code": "ER931", "name": "ER931 Camlı Asimetrik", "series": "Daphne Serisi", "has_fuga": True, "has_cam": True, "image": "image42.jpeg", "pattern_url": "/static/door_patterns/image42.jpeg", "fuga_type": "asymmetric", "fuga_desc": "Asimetrik CNC & Cam Yuvaları"},
    {"code": "ER940", "name": "ER940 4 Yatay Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image22.png", "pattern_url": "/static/door_patterns/image22.png", "fuga_type": "4_horizontal", "fuga_desc": "4x Yatay Simetrik CNC Fuga"},
    {"code": "ER941", "name": "ER941 Camlı 4 Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": True, "image": "image43.png", "pattern_url": "/static/door_patterns/image43.png", "fuga_type": "4_horizontal", "fuga_desc": "4x Yatay Camlı & CNC Çizgili"},
    {"code": "ER950", "name": "ER950 5 Yatay Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image23.png", "pattern_url": "/static/door_patterns/image23.png", "fuga_type": "5_horizontal", "fuga_desc": "5x Yatay CNC Fuga Çizgisi"},
    {"code": "ER951", "name": "ER951 Camlı 5 Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": True, "image": "image44.png", "pattern_url": "/static/door_patterns/image44.png", "fuga_type": "5_horizontal", "fuga_desc": "5x Yatay Cam Bölmeli & Fuga"},
    {"code": "ER960", "name": "ER960 Blok Fuga", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image24.png", "pattern_url": "/static/door_patterns/image24.png", "fuga_type": "block", "fuga_desc": "Modüler Blok CNC Derzleri"},
    {"code": "ER1004", "name": "ER1004 Daphne Tasarım", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image25.jpeg", "pattern_url": "/static/door_patterns/image25.jpeg", "fuga_type": "geometric", "fuga_desc": "Daphne Özel CNC Çizgi Deseni"},
    {"code": "ER1005", "name": "ER1005 Daphne Tasarım", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image26.jpeg", "pattern_url": "/static/door_patterns/image26.jpeg", "fuga_type": "geometric", "fuga_desc": "Daphne Akıcı Hatlı CNC"},
    {"code": "ER1006", "name": "ER1006 Daphne Tasarım", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image27.jpeg", "pattern_url": "/static/door_patterns/image27.jpeg", "fuga_type": "geometric", "fuga_desc": "Daphne Asimetrik Modern Çizgi"},
    {"code": "ER1007", "name": "ER1007 Daphne Tasarım", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image28.png", "pattern_url": "/static/door_patterns/image28.png", "fuga_type": "geometric", "fuga_desc": "Daphne Dinamik CNC Formu"},
    {"code": "ER1008", "name": "ER1008 Daphne Tasarım", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image29.png", "pattern_url": "/static/door_patterns/image29.png", "fuga_type": "geometric", "fuga_desc": "Daphne Dalgalı CNC Tasarımı"},
    {"code": "ER1012", "name": "ER1012 Daphne Tasarım", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image30.png", "pattern_url": "/static/door_patterns/image30.png", "fuga_type": "geometric", "fuga_desc": "Daphne Çizgisel Geometrik Model"},
    {"code": "ER1014", "name": "ER1014 Daphne Tasarım", "series": "Daphne Serisi", "has_fuga": True, "has_cam": False, "image": "image31.jpeg", "pattern_url": "/static/door_patterns/image31.jpeg", "fuga_type": "geometric", "fuga_desc": "Daphne Prestij CNC Fuga"},
    {"code": "ER1014 ÖZEL", "name": "ER1014 ÖZEL Tasarım", "series": "Daphne Serisi", "has_fuga": True, "has_cam": True, "image": "image32.jpeg", "pattern_url": "/static/door_patterns/image32.jpeg", "fuga_type": "geometric", "fuga_desc": "Daphne Prestij Camlı Özel Tasarım"},
    # DAPHNE ÖZEL MODELLER
    {"code": "ER520", "name": "ER520 (Eski EROZL020)", "series": "Daphne Özel Serisi", "has_fuga": True, "has_cam": False, "image": "image54.jpeg", "pattern_url": "/static/door_patterns/image54.jpeg", "fuga_type": "geometric", "fuga_desc": "Daphne Özel Seri CNC (Eski EROZL020)"},
    {"code": "ER540", "name": "ER540 (Eski EROZL011)", "series": "Daphne Özel Serisi", "has_fuga": True, "has_cam": False, "image": "image51.jpeg", "pattern_url": "/static/door_patterns/image51.jpeg", "fuga_type": "geometric", "fuga_desc": "Daphne Özel Seri CNC (Eski EROZL011)"},
    {"code": "ER550", "name": "ER550 (Eski EROZL001)", "series": "Daphne Özel Serisi", "has_fuga": True, "has_cam": False, "image": "image49.jpeg", "pattern_url": "/static/door_patterns/image49.jpeg", "fuga_type": "geometric", "fuga_desc": "Daphne Özel Seri CNC (Eski EROZL001)"},
    {"code": "ER560", "name": "ER560 (Eski EROZL013)", "series": "Daphne Özel Serisi", "has_fuga": True, "has_cam": False, "image": "image52.jpeg", "pattern_url": "/static/door_patterns/image52.jpeg", "fuga_type": "geometric", "fuga_desc": "Daphne Özel Seri CNC (Eski EROZL013)"},
    {"code": "ER570", "name": "ER570 (Eski EROZL017)", "series": "Daphne Özel Serisi", "has_fuga": True, "has_cam": False, "image": "image53.jpeg", "pattern_url": "/static/door_patterns/image53.jpeg", "fuga_type": "geometric", "fuga_desc": "Daphne Özel Seri CNC (Eski EROZL017)"},
    {"code": "ER590", "name": "ER590 (Eski EROZL009)", "series": "Daphne Özel Serisi", "has_fuga": True, "has_cam": False, "image": "image50.jpeg", "pattern_url": "/static/door_patterns/image50.jpeg", "fuga_type": "geometric", "fuga_desc": "Daphne Özel Seri CNC (Eski EROZL009)"},
    # TITUS SERİSİ
    {"code": "ER5000", "name": "ER5000 Titus Standart", "series": "Titus Serisi", "has_fuga": True, "has_cam": False, "image": "image44.png", "pattern_url": "/static/door_patterns/image44.png", "fuga_type": "3_horizontal", "fuga_desc": "Titus Standart 3x Yatay CNC Fuga"},
    {"code": "ER5012", "name": "ER5012 Titus CNC", "series": "Titus Serisi", "has_fuga": True, "has_cam": False, "image": "image45.jpeg", "pattern_url": "/static/door_patterns/image45.jpeg", "fuga_type": "cross", "fuga_desc": "Titus Kesişen Çizgisel CNC"},
    {"code": "ER5014", "name": "ER5014 Titus CNC", "series": "Titus Serisi", "has_fuga": True, "has_cam": False, "image": "image46.jpeg", "pattern_url": "/static/door_patterns/image46.jpeg", "fuga_type": "frame", "fuga_desc": "Titus Çerçeve & Hat CNC"},
    {"code": "ER5020", "name": "ER5020 Titus CNC", "series": "Titus Serisi", "has_fuga": True, "has_cam": False, "image": "image47.png", "pattern_url": "/static/door_patterns/image47.png", "fuga_type": "geometric", "fuga_desc": "Titus Modern Geometrik CNC"}
]

ERDOOR_COLORS_CATALOG = {
    "KOYU CEVİZ": {"hex": "#4D3322", "name": "Koyu Ceviz", "code": "K.CEVİZ"},
    "AKÇAAĞAÇ": {"hex": "#D4B185", "name": "Akçaağaç", "code": "AKÇAAĞAÇ"},
    "DİŞBUDAK BEYAZ": {"hex": "#F1F5F9", "name": "Dişbudak Beyaz", "code": "D.BEYAZ"},
    "TİK BEYAZ": {"hex": "#E2D9CC", "name": "Tik Beyaz / Beyaz Tik", "code": "B.TEAK"},
    "TİK ANTRASİT": {"hex": "#2F3640", "name": "Tik Antrasit / Antrasit", "code": "ANTRASİT"},
    "COCO MAURON": {"hex": "#3E2723", "name": "Coco Mauron", "code": "COCO"}
}

# ── PARAMETRIC SPECIFICATIONS & DYNAMIC ROUTING ───────────

def parse_door_specs(model_str: str, custom_color: str = None) -> dict:
    m = (model_str or "").strip()
    m_up = m.upper()

    # 1. Parse Dimensions (En x Boy x Kalınlık)
    dim_match = re.search(r'(\d{3,4})\s*[xX*]\s*(\d{3,4})(?:\s*[xX*]\s*(\d{2}))?', m)
    if dim_match:
        width = int(dim_match.group(1))
        height = int(dim_match.group(2))
        thick = int(dim_match.group(3)) if dim_match.group(3) else 40
    else:
        width, height, thick = 800, 2020, 40

    # 2. Parse Model Code
    model_code = "ER100"
    for cat_item in sorted(ERDOOR_MODELS_CATALOG, key=lambda x: len(x["code"]), reverse=True):
        if m_up.startswith(cat_item["code"].upper()):
            model_code = cat_item["code"]
            break
    else:
        parts = m.split()
        model_code = parts[0] if parts else "ER100"
    cat_match = next((item for item in ERDOOR_MODELS_CATALOG if item["code"] == model_code), None)

    # 3. Determine if CNC / Fuga is required
    flat_models = {"ER100", "ER200"}
    if cat_match:
        has_fuga = cat_match["has_fuga"] or ("FUGA" in m_up) or ("DERZ" in m_up)
        has_cam = cat_match["has_cam"] or ("CAM" in m_up) or ("CAMLI" in m_up)
    else:
        has_fuga = (model_code not in flat_models) or ("FUGA" in m_up) or ("DERZ" in m_up)
        has_cam = ("CAM" in m_up) or ("CAMLI" in m_up)

    # 4. Parse Surface Color (Erdoor Resmi Renkleri)
    if custom_color and custom_color.strip():
        color = custom_color.strip().upper()
        surface_mat_id = "MAT_MDF_STD"
    elif any(k in m_up for k in ["K.CEVIZ", "K. CEVIZ", "K.CEVİZ", "KOYU CEVIZ", "KOYU CEVİZ", "CEVIZ", "CEVİZ"]):
        color = "KOYU CEVİZ"
        surface_mat_id = "MAT_MDF_KCEVIZ"
    elif any(k in m_up for k in ["DİŞBUDAK", "DISBUDAK", "D.BEYAZ", "DISBUDAK BEYAZ", "DİŞBUDAK BEYAZ"]):
        color = "DİŞBUDAK BEYAZ"
        surface_mat_id = "MAT_MDF_BEYAZ"
    elif any(k in m_up for k in ["TİK BEYAZ", "TIK BEYAZ", "BEYAZ TİK", "BEYAZ TIK", "B.TEAK", "B. TEAK"]):
        color = "TİK BEYAZ"
        surface_mat_id = "MAT_MDF_BTEAK"
    elif any(k in m_up for k in ["TİK ANTRASİT", "TIK ANTRASIT", "ANTRASİT TİK", "ANTRASIT TIK", "ANTRASİT", "ANTRASIT", "ANTRAS"]):
        color = "TİK ANTRASİT"
        surface_mat_id = "MAT_MDF_ANTRASIT"
    elif any(k in m_up for k in ["TİK", "TIK", "TEAK"]):
        color = "TİK BEYAZ"
        surface_mat_id = "MAT_MDF_TEAK"
    elif any(k in m_up for k in ["COCO", "MAURON", "KOKO"]):
        color = "COCO MAURON"
        surface_mat_id = "MAT_MDF_COCO"
    elif any(k in m_up for k in ["AKÇAAGAÇ", "AKCAAGAC", "AKÇAAĞAÇ", "AKCAAĞAC", "AKCAA"]):
        color = "AKÇAAĞAÇ"
        surface_mat_id = "MAT_MDF_AKCAAGAC"
    else:
        color = "DİŞBUDAK BEYAZ"
        surface_mat_id = "MAT_MDF_STD"

    # 5. Core Type (Dolgu)
    if "PETEK" in m_up:
        core_type = "PETEK"
        core_mat_id = "MAT_PETEK_KRAFT"
    else:
        core_type = "STRAFOR"
        core_mat_id = "MAT_STRAFOR_EPS"

    # 6. Parametric Calculations (Per Door)
    seren_boy_count = 3.5  # Fabrika kuralı: Kapı başına 3.5 boy seren verilir
    boy_m = height / 1000.0
    total_seren_m = round(seren_boy_count * boy_m, 2)
    boy_seren_m = round(2.0 * boy_m, 2)
    en_seren_m = round(1.5 * boy_m, 2)
    total_pvc_m = round((2.0 * (height + width) / 1000.0) * 1.02, 2)
    door_area_m2 = (width / 1000.0) * (height / 1000.0)
    total_glue_kg = round(2.0 * door_area_m2 * 0.22, 2)

    # 7. Dynamic Routing Steps
    routing_steps = [
        {"step": 1, "station": "Seren Kesim", "machine": "Seren Kesim Tezgahı", "desc": f"3.5 Boy Kompozit Seren ({total_seren_m}m) karkas ve en seren ebatlama"},
        {"step": 2, "station": "CNC Strafor / Dolgu", "machine": "CNC Strafor Kesim Makinesi", "desc": f"{core_type} iç dolgu net kesim ({width-84}x{height-84}mm)"},
        {"step": 3, "station": "Pres", "machine": "Sıcak Pres Hattı", "desc": f"WPC Levha ({color}) ve kompozit seren karkas sıcak presleme"}
    ]

    current_step = 4
    if has_fuga:
        routing_steps.append({
            "step": current_step,
            "station": "CNC Yüzey Freze / Fuga",
            "machine": "CNC Yüzey İşleme Merkezi",
            "desc": f"Model {model_code} özel desen ve fuga kanal frezeleme"
        })
        current_step += 1

    if has_cam:
        routing_steps.append({
            "step": current_step,
            "station": "Cam Yeri Boşaltma",
            "machine": "Torwegge Freze Tezgahı",
            "desc": "Cam boşaltma alanı ve çıta frezeleme"
        })
        current_step += 1

    routing_steps.append({
        "step": current_step,
        "station": "Homag",
        "machine": "Homag Ebatlama & Kenar",
        "desc": f"4 kenar kalibre ve PVC kenar bantlama ({total_pvc_m}m)"
    })
    current_step += 1

    routing_steps.append({
        "step": current_step,
        "station": "Paketleme",
        "machine": "Paketleme & Sevkiyat Hattı",
        "desc": "Son kalite kontrol, koruma kartonu ve shrink paketleme"
    })

    return {
        "model_code": model_code,
        "has_fuga": has_fuga,
        "has_cam": has_cam,
        "color": color,
        "surface_mat_id": surface_mat_id,
        "core_type": core_type,
        "core_mat_id": core_mat_id,
        "width": width,
        "height": height,
        "thickness": thick,
        "dim_str": f"{width}x{height}x{thick}",
        "consumptions": {
            "seren_boy_adet": 3.5,
            "seren_m": total_seren_m,
            "boy_seren_m": round(boy_seren_m, 2),
            "en_seren_m": round(en_seren_m, 2),
            "pvc_m": total_pvc_m,
            "glue_kg": total_glue_kg,
            "surface_qty": 2,
            "core_qty": 1,
            "takoz_qty": 2
        },
        "routing": routing_steps,
        "routing_summary": " -> ".join(s["station"] for s in routing_steps)
    }

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
            
        # Add parametric specifications and routing
        order["specs"] = parse_door_specs(order.get("model", ""))
        res.append(order)
            
    res.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return res

@app.get("/api/orders/{oid}/routing")
def get_order_routing(oid: str):
    d = load_data()
    if oid not in d.get("orders", {}):
        raise HTTPException(404, "Sipariş bulunamadı")
    order = d["orders"][oid]
    specs = parse_door_specs(order.get("model", ""))
    return {
        "order": order,
        "specs": specs
    }

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
                
    fac_name = "ERGÜNBAŞ Kanat Fabrikası"
    model_str = order.get("model", "")
    specs = parse_door_specs(model_str, custom_color=order.get("color"))

    color = order.get("color") or specs.get("color") or "D.BEYAZ"
    width_mm = specs.get("width", 800)
    height_mm = specs.get("height", 2020)
    thick_mm = specs.get("thickness", 40)
    width_cm = round(width_mm / 10)
    height_cm = round(height_mm / 10)
    core_type = specs.get("core_type", "STRAFOR")

    return {
        "order_id": oid,
        "order_code": order.get("order_no", oid),
        "order_no": order.get("order_no", oid),
        "customer": order.get("customer", ""),
        "model": model_str or "Standart Kanat Kapı",
        "surface_finish": color,
        "color": color,
        "core_type": core_type,
        "width": width_cm,
        "height": height_cm,
        "width_mm": width_mm,
        "height_mm": height_mm,
        "thickness_mm": thick_mm,
        "dim_str": f"{width_mm}x{height_mm}x{thick_mm}",
        "dims_formatted": f"{width_cm} x {height_cm} cm",
        "doors": order.get("qty", 0),
        "total_doors": order.get("qty", 0),
        "facility_name": fac_name,
        "facility": order.get("facility_id", "fac1"),
        "facility_id": order.get("facility_id", "fac1"),
        "delivery_date": order.get("delivery_date", ""),
        "barcode": f"ERG-{order.get('order_no', oid)}",
        "barcode_text": f"ERG-{oid}-{order.get('qty', 0)}",
        "qr_payload": f"ERGUNBAS|{oid}|{order.get('order_no')}|{order.get('qty')}|{order.get('model')}|{color}|{width_mm}x{height_mm}"
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
        
        specs = parse_door_specs(o.get("model", ""), custom_color=o.get("color"))
        color = o.get("color") or specs.get("color", "")
        item = {
            "order_id": oid,
            "order_code": o.get("order_no", oid),
            "order_no": o.get("order_no", oid),
            "customer": o.get("customer", ""),
            "model": o.get("model", ""),
            "color": color,
            "surface_finish": color,
            "specs": specs,
            "width": round(specs.get("width", 800) / 10),
            "height": round(specs.get("height", 2020) / 10),
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
    
    # Eğer son aşamaya (Paketleme) ulaştıysa, Günlük Giriş sekmesine otomatik üretim kaydı düş
    if target == "paket":
        order = d["orders"].get(oid, {})
        today_str = date.today().isoformat()
        if today_str not in d.setdefault("daily_entries", {}):
            d["daily_entries"][today_str] = {"date": today_str, "order_entries": [], "machine_entries": [], "downtimes": []}
        
        existing = next((oe for oe in d["daily_entries"][today_str]["order_entries"] if oe.get("order_id") == oid), None)
        if not existing:
            d["daily_entries"][today_str]["order_entries"].append({
                "order_id": oid,
                "order_no": order.get("order_no", oid),
                "customer": order.get("customer", ""),
                "model": order.get("model", ""),
                "output_qty": order.get("qty", 0),
                "shift": "Gündüz",
                "notes": "QR/Barkod ile otomatik tamamlandı"
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
def simulate_schedule(target_qty: Optional[int] = 1000, facility_id: Optional[str] = "all", shifts_per_day: Optional[int] = 1, hours_per_day: Optional[float] = 9, efficiency: Optional[float] = 0.85):
    d = load_data()
    orders = d.get("orders", {})
    daily = d.get("daily_entries", {})
    
    # Tek Fabrika Birleşik Darboğaz Kapasitesi (Pres & Homag Hatları):
    # Günlük ~440 kapı (1 vardiya)
    shifts = max(1, min(shifts_per_day or 1, 3))
    eff = float(efficiency or 0.85)
    daily_capacity = int(480 * shifts * eff)
    fac_name = "ERGÜNBAŞ Kanat Fabrikası (Entegre Tesis)"
    bottleneck = "Sıcak Presler & Ebatlama Hatları (~50 kapı/saat)"

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
            "model": o.get("model", ""),
            "color": o.get("color", ""),
            "remaining_qty": o["remaining_qty"],
            "committed_delivery": o["delivery_date"],
            "estimated_completion": est_finish.isoformat(),
            "status": "on_time" if (not o["delivery_date"] or est_finish.isoformat() <= o["delivery_date"]) else "risk"
        })

    queue_items = []
    for idx, o in enumerate(queue_timeline):
        m_str = o.get("model", "")
        sp = parse_door_specs(m_str, custom_color=o.get("color"))
        col = o.get("color") or sp.get("color") or "Kompozit"
        queue_items.append({
            "sequence": idx + 1,
            "order_id": o.get("order_no", ""),
            "order_code": o.get("order_no", ""),
            "customer": o.get("customer", ""),
            "model": m_str or "Standart Kanat Kapı",
            "surface": col,
            "color": col,
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

# ── PRODUCT RECIPES (BOM) ─────────────────────────────────

@app.get("/api/mrp/recipes")
def list_recipes():
    d = load_data()
    recipes = d.get("recipes", {})
    materials = d.get("materials", {})
    res = []
    for rid, r in recipes.items():
        r_copy = dict(r)
        total_unit_cost = 0.0
        enriched_items = []
        for item in r.get("items", []):
            mid = item.get("material_id")
            mat = materials.get(mid, {})
            uprice = float(mat.get("unit_price", 0.0))
            qty = float(item.get("qty", 0.0))
            waste = float(item.get("waste_pct", 0.0))
            eff_qty = qty * (1.0 + (waste / 100.0))
            item_cost = round(eff_qty * uprice, 2)
            total_unit_cost += item_cost
            enriched_items.append({
                "material_id": mid,
                "material_name": mat.get("name", mid),
                "unit": item.get("unit") or mat.get("unit", "Adet"),
                "qty": qty,
                "waste_pct": waste,
                "effective_qty": round(eff_qty, 3),
                "unit_price": uprice,
                "total_cost": item_cost,
                "notes": item.get("notes", "")
            })
        r_copy["items"] = enriched_items
        r_copy["unit_cost"] = round(total_unit_cost, 2)
        res.append(r_copy)
    res.sort(key=lambda x: (not x.get("is_default", False), x.get("name", "")))
    return res

@app.post("/api/mrp/recipes")
def create_recipe(req: RecipeCreate):
    d = load_data()
    rid = req.id or ("REC_" + str(uuid.uuid4())[:8].upper())
    if "recipes" not in d: d["recipes"] = {}
    if rid in d["recipes"]: raise HTTPException(400, "Bu ürün/reçete kodu zaten mevcut")
    
    if req.is_default:
        for r in d["recipes"].values():
            r["is_default"] = False
            
    d["recipes"][rid] = {
        "id": rid,
        "name": req.name,
        "code": req.code or rid,
        "model_pattern": req.model_pattern or "",
        "is_default": bool(req.is_default),
        "description": req.description or "",
        "items": [item.dict() for item in req.items]
    }
    save_data(d)
    return {"id": rid, "status": "ok"}

@app.put("/api/mrp/recipes/{rid}")
def update_recipe(rid: str, req: RecipeUpdate):
    d = load_data()
    if rid not in d.get("recipes", {}): raise HTTPException(404, "Ürün/reçete bulunamadı")
    if req.is_default:
        for other_id, r in d["recipes"].items():
            if other_id != rid:
                r["is_default"] = False
    target = d["recipes"][rid]
    update_data = req.dict(exclude_none=True)
    if "items" in update_data:
        update_data["items"] = [it if isinstance(it, dict) else it.dict() for it in req.items]
    target.update(update_data)
    save_data(d)
    return {"status": "ok"}

@app.delete("/api/mrp/recipes/{rid}")
def delete_recipe(rid: str):
    d = load_data()
    if rid not in d.get("recipes", {}): raise HTTPException(404, "Ürün/reçete bulunamadı")
    if len(d["recipes"]) <= 1:
        raise HTTPException(400, "Sistemde en az 1 adet ürün reçetesi bulunmalıdır.")
    del d["recipes"][rid]
    save_data(d)
    return {"status": "ok"}

@app.get("/api/mrp/requirements")
def mrp_requirements_alias(facility_id: Optional[str] = "all", time_scope: Optional[str] = "all_open"):
    return calculate_mrp(facility_id=facility_id, time_scope=time_scope)

@app.get("/api/mrp/calculation")
def calculate_mrp(facility_id: Optional[str] = "all", time_scope: Optional[str] = "all_open"):
    d = load_data()
    orders = d.get("orders", {})
    daily = d.get("daily_entries", {})
    materials = d.get("materials", {})
    recipes = d.get("recipes", {})
    if not recipes:
        recipes = get_default_recipes()

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

    # Identify default recipe
    default_recipe = None
    for r in recipes.values():
        if r.get("is_default"):
            default_recipe = r
            break
    if not default_recipe and recipes:
        default_recipe = next(iter(recipes.values()))

    # Sort patterned recipes by pattern length descending for most specific matching
    patterned_recipes = [r for r in recipes.values() if r.get("model_pattern", "").strip()]
    patterned_recipes.sort(key=lambda x: len(x.get("model_pattern", "")), reverse=True)

    recipe_usage = {rid: {"id": rid, "name": r.get("name"), "doors": 0, "orders": 0} for rid, r in recipes.items()}
    
    total_seren_needed = 0.0
    total_pvc_needed = 0.0
    cnc_doors_count = 0
    flat_doors_count = 0
    colors_agg = {}
    dims_agg = {}

    for o in selected_orders:
        ono = o.get("order_no", o.get("id"))
        rem = o.get("remaining_qty", 0)
        m = (o.get("model") or "").upper()
        
        # Parametric door specifications
        specs = parse_door_specs(m)
        seren_per_door = specs["consumptions"]["seren_m"]
        pvc_per_door = specs["consumptions"]["pvc_m"]
        glue_per_door = specs["consumptions"]["glue_kg"]
        surface_mid = specs["surface_mat_id"]
        core_mid = specs["core_mat_id"]

        total_seren_needed += rem * seren_per_door
        total_pvc_needed += rem * pvc_per_door
        c_name = specs["color"]
        colors_agg[c_name] = colors_agg.get(c_name, 0) + rem
        d_name = specs["dim_str"]
        dims_agg[d_name] = dims_agg.get(d_name, 0) + rem
        
        if specs["has_fuga"]: cnc_doors_count += rem
        else: flat_doors_count += rem

        # Match to a dynamic recipe
        matched_recipe = None
        for r in patterned_recipes:
            pat = r.get("model_pattern", "").upper()
            if pat and pat in m:
                matched_recipe = r
                break
        
        if not matched_recipe:
            matched_recipe = default_recipe

        if matched_recipe:
            m_rid = matched_recipe.get("id")
            if m_rid in recipe_usage:
                recipe_usage[m_rid]["doors"] += rem
                recipe_usage[m_rid]["orders"] += 1
                
        # 1. Kompozit Seren (Parametrik Boy/En Hesaplı)
        if "MAT_SEREN_KOMP" in gross_req:
            gross_req["MAT_SEREN_KOMP"] += rem * seren_per_door
            if ono not in affected_orders["MAT_SEREN_KOMP"]: affected_orders["MAT_SEREN_KOMP"].append(ono)
        else:
            gross_req["MAT_SEREN_KOMP"] = rem * seren_per_door
            affected_orders["MAT_SEREN_KOMP"] = [ono]

        # 2. PVC Kenar Bandı (Parametrik Çevre Hesaplı)
        if "MAT_KENAR_BANDI" in gross_req:
            gross_req["MAT_KENAR_BANDI"] += rem * pvc_per_door
            if ono not in affected_orders["MAT_KENAR_BANDI"]: affected_orders["MAT_KENAR_BANDI"].append(ono)
        else:
            gross_req["MAT_KENAR_BANDI"] = rem * pvc_per_door
            affected_orders["MAT_KENAR_BANDI"] = [ono]

        # 3. Poliüretan Pres Tutkalı (Alan Hesaplı)
        if "MAT_TUTKAL_PRES" in gross_req:
            gross_req["MAT_TUTKAL_PRES"] += rem * glue_per_door
            if ono not in affected_orders["MAT_TUTKAL_PRES"]: affected_orders["MAT_TUTKAL_PRES"].append(ono)
        else:
            gross_req["MAT_TUTKAL_PRES"] = rem * glue_per_door
            affected_orders["MAT_TUTKAL_PRES"] = [ono]

        # 4. Kilit Destek Takozu (2 adet/kanat)
        if "MAT_KILIT_TAKOZ" in gross_req:
            gross_req["MAT_KILIT_TAKOZ"] += rem * 2.0
            if ono not in affected_orders["MAT_KILIT_TAKOZ"]: affected_orders["MAT_KILIT_TAKOZ"].append(ono)
        else:
            gross_req["MAT_KILIT_TAKOZ"] = rem * 2.0
            affected_orders["MAT_KILIT_TAKOZ"] = [ono]

        # 5. İç Dolgu (Strafor veya Petek)
        if core_mid in gross_req:
            gross_req[core_mid] += rem * 1.0
            if ono not in affected_orders[core_mid]: affected_orders[core_mid].append(ono)
        else:
            gross_req[core_mid] = rem * 1.0
            affected_orders[core_mid] = [ono]

        # 6. Yüzey Levhası (Sipariş Rengine Göre 2 Adet WPC/Kompozit Panel)
        if surface_mid in gross_req:
            gross_req[surface_mid] += rem * 2.0
            if ono not in affected_orders[surface_mid]: affected_orders[surface_mid].append(ono)
        else:
            gross_req[surface_mid] = rem * 2.0
            affected_orders[surface_mid] = [ono]
            
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
    
    # Calculate enriched recipes for response
    all_recipes_list = list_recipes()

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
            "total_purchase_cost": round(total_purchase_cost, 2),
            "total_seren_meters": round(total_seren_needed, 1),
            "total_pvc_meters": round(total_pvc_needed, 1),
            "cnc_doors_count": cnc_doors_count,
            "flat_doors_count": flat_doors_count,
            "colors_breakdown": dict(sorted(colors_agg.items(), key=lambda x: -x[1])[:8]),
            "dims_breakdown": dict(sorted(dims_agg.items(), key=lambda x: -x[1])[:8])
        },
        "requirements": requirements,
        "purchase_advice": purchase_advice,
        "recipes": all_recipes_list,
        "recipe_usage": recipe_usage,
        "bom_standards": [
            {"component": "Seren & Karkas", "spec": "3.5 Boy Seren / Kapı (~7.1 Metre Kompozit Seren)"},
            {"component": "İç Dolgu", "spec": "1 Adet EPS Strafor (veya Petek Kağıt Dolgu)"},
            {"component": "Yüzey Levhası", "spec": "2 Adet (Ön ve Arka Yüz MDF/WPC 4mm Levha)"},
            {"component": "PVC Kenar Bandı", "spec": "5.8 Metre / Kapı (1mm x 45mm Ebatlama Bandı)"},
            {"component": "Sıcak Pres Tutkalı", "spec": "0.35 Kg / Kapı (Poliüretan/D3 Tutkal)"},
            {"component": "Kilit Takozu", "spec": "2 Adet / Kapı (Kompozit Takviye Takozu)"}
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
    open_doors_total = 0
    sarkan = []
    
    for oid, o in orders.items():
        total_orders += 1
        is_open = o.get("status") == "open"
        if is_open: open_orders += 1
        else: done_orders += 1
        
        t_out = sum(oe.get("output_qty",0) for dd in daily.values() for oe in dd.get("order_entries",[]) if oe.get("order_id") == oid)
        kalan = max(0, o.get("qty",0) - t_out)
        
        if is_open:
            open_doors_total += kalan
            try:
                deliv_dt = date.fromisoformat(o["delivery_date"])
                days_rem = (deliv_dt - today_dt).days
                if days_rem <= 7:
                    sarkan.append({
                        "id": oid,
                        "order_no": o.get("order_no", ""),
                        "facility_name": "ERGÜNBAŞ Fabrika",
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
    for dk, dd in daily.items():
        if not in_range(dk): continue
        for oe in dd.get("order_entries", []):
            total_out_period += oe.get("output_qty", 0)

    days_arr = []
    curr = start_dt
    while curr <= end_dt:
        ds = curr.isoformat()
        dd = daily.get(ds, {})
        d_out = sum(oe.get("output_qty", 0) for oe in dd.get("order_entries", []))
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
        today_active_workers += int(me.get("worker_count", 1) or 1)
        
    for dk, dd in daily.items():
        if not in_range(dk): continue
        for me in dd.get("machine_entries", []):
            mid = me.get("machine_id")
            m = machines.get(mid, {})
            
            if mid not in mach_stats:
                mach_stats[mid] = {
                    "id": mid,
                    "name": m.get("name", mid),
                    "stage": m.get("stage", "Üretim"),
                    "facility_id": "main",
                    "facility_name": "ERGÜNBAŞ Fabrika",
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

    scraps = d.get("scraps", {})
    total_scraps = sum(s.get("qty", s.get("scrap_qty", 0)) for s in scraps.values())
    shipments = d.get("shipments", {})
    active_shipments = len([s for s in shipments.values() if s.get("status") in ["preparing", "Hazırlanıyor", "Yolda"]])

    return {
        "orders": {"total": total_orders, "open": open_orders, "done": done_orders, "open_doors_total": open_doors_total},
        "period_summary": {
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat(),
            "total_output": total_out_period,
            "open_doors_total": open_doors_total,
            "days": days_arr,
            "today_active_workers": today_active_workers,
            "period_man_hours": round(period_man_hours, 1),
            "total_scraps": total_scraps,
            "active_shipments": active_shipments
        },
        "sarkan_siparisler": sarkan,
        "machine_stats": ms_list
    }

# ── 4. BIÇAK & KESTİRİMCİ BAKIM TAKİBİ (MADDE 4) ────────────

class ToolServiceRequest(BaseModel):
    operator: Optional[str] = "Bakım Operatörü"
    notes: Optional[str] = ""

@app.get("/api/maintenance/tools")
def get_maintenance_tools():
    d = load_data()
    tools = d.get("maintenance_tools", {})
    history = d.get("maintenance_history", [])
    
    res = []
    for tid, t in tools.items():
        cur = t.get("current_usage", 0)
        max_c = t.get("max_capacity", 10000)
        warn = t.get("warning_threshold", 8000)
        
        pct = min(100.0, round((cur / max_c) * 100, 1)) if max_c > 0 else 0
        status = "critical" if cur >= max_c else ("warning" if cur >= warn else "good")
        remaining = max(0, max_c - cur)
        
        res.append({
            **t,
            "wear_pct": pct,
            "status": status,
            "remaining": remaining
        })
    
    return {
        "tools": res,
        "history": sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)[:25],
        "overall_status": "critical" if any(t["status"] == "critical" for t in res) else ("warning" if any(t["status"] == "warning" for t in res) else "good")
    }

@app.post("/api/maintenance/tools/{tool_id}/service")
def service_maintenance_tool(tool_id: str, req: ToolServiceRequest):
    d = load_data()
    tools = d.get("maintenance_tools", {})
    if tool_id not in tools:
        raise HTTPException(404, "Takım/Bıçak bulunamadı")
        
    t = tools[tool_id]
    prev_usage = t.get("current_usage", 0)
    t["current_usage"] = 0
    t["last_service_date"] = date.today().isoformat()
    t["last_service_operator"] = req.operator or "Bakım Operatörü"
    t["service_count"] = t.get("service_count", 0) + 1
    t["status"] = "good"
    
    log_entry = {
        "id": "SRV-" + datetime.now().strftime("%Y%m%d%H%M%S"),
        "tool_id": tool_id,
        "tool_name": t.get("name", tool_id),
        "station": t.get("station", ""),
        "timestamp": datetime.now().isoformat(),
        "date": date.today().isoformat(),
        "operator": req.operator or "Bakım Operatörü",
        "notes": req.notes or "Bileme yapıldı / sıfırlandı",
        "previous_usage": prev_usage,
        "unit": t.get("metric_unit", "")
    }
    d.setdefault("maintenance_history", []).append(log_entry)
    save_data(d)
    return {"status": "ok", "message": f"{t.get('name')} başarıyla sıfırlandı.", "log": log_entry}


# ── 2. 3D İNTERAKTİF PATLATILMIŞ KARKAS MODELİ (MADDE 2) ─────

COLOR_PALETTE_3D = {
    "AKÇAAĞAÇ": {"hex": "#D4B185", "name": "Akçaağaç"},
    "AKÇAAGAÇ": {"hex": "#D4B185", "name": "Akçaağaç"},
    "KOYU CEVİZ": {"hex": "#4D3322", "name": "Koyu Ceviz"},
    "K.CEVİZ": {"hex": "#4D3322", "name": "Koyu Ceviz"},
    "DİŞBUDAK BEYAZ": {"hex": "#F1F5F9", "name": "Dişbudak Beyaz"},
    "D.BEYAZ": {"hex": "#F1F5F9", "name": "Dişbudak Beyaz"},
    "TİK BEYAZ": {"hex": "#E2D9CC", "name": "Tik Beyaz"},
    "B.TEAK": {"hex": "#E2D9CC", "name": "Tik Beyaz"},
    "TİK ANTRASİT": {"hex": "#2F3640", "name": "Tik Antrasit"},
    "ANTRASİT": {"hex": "#2F3640", "name": "Tik Antrasit"},
    "COCO MAURON": {"hex": "#3E2723", "name": "Coco Mauron"},
    "COCO": {"hex": "#3E2723", "name": "Coco Mauron"},
    "STANDART": {"hex": "#E2E8F0", "name": "Standart"}
}

@app.get("/api/door-models")
def get_door_models():
    return {
        "models": ERDOOR_MODELS_CATALOG,
        "colors": ERDOOR_COLORS_CATALOG
    }

@app.get("/api/doors/3d-model/{oid}")
def get_door_3d_model(oid: str):
    d = load_data()
    orders = d.get("orders", {})
    order = orders.get(oid)
    if not order:
        found = next((v for k, v in orders.items() if v.get("order_no") == oid or k == oid), None)
        if found:
            order = found
            oid = order.get("id", oid)
        else:
            cat_m = next((m for m in ERDOOR_MODELS_CATALOG if m["code"] == oid.upper()), None)
            if cat_m:
                order = {
                    "id": oid,
                    "order_no": oid,
                    "customer": f"Erdoor {cat_m['series']}",
                    "model": f"{cat_m['code']} KANAT AKÇAAĞAÇ KOM.SEREN STRAFOR 800X2020X40",
                    "color": "AKÇAAĞAÇ"
                }
            elif orders:
                oid = list(orders.keys())[0]
                order = orders[oid]
            else:
                order = {
                    "id": "DEMO-01", "order_no": "DEMO-2026", "customer": "Örnek Müşteri",
                    "model": "ER100 KANAT AKÇAAĞAÇ KOM.SEREN STRAFOR 800X2020X40", "qty": 10
                }
            
    specs = parse_door_specs(order.get("model", ""), custom_color=order.get("color"))
    w = specs["width"]
    h = specs["height"]
    th = specs["thickness"]
    color_key = specs["color"]
    color_info = ERDOOR_COLORS_CATALOG.get(color_key, COLOR_PALETTE_3D.get(color_key, {"hex": "#D4B185", "name": color_key}))
    
    seren_w = 42 # mm
    seren_th = 32 # mm
    panel_th = 4 # mm
    core_w = max(100, w - (seren_w * 2)) # 716 mm
    core_h = max(100, h - (seren_w * 2)) # 1936 mm
    
    cat_entry = next((m for m in ERDOOR_MODELS_CATALOG if m["code"] == specs.get("model_code", "ER100")), None)
    pattern_img = cat_entry.get("image", "image3.png") if cat_entry else "image3.png"
    pattern_url = cat_entry.get("pattern_url", f"/static/door_patterns/{pattern_img}") if cat_entry else f"/static/door_patterns/{pattern_img}"
    fuga_type = cat_entry.get("fuga_type", "none") if cat_entry else "none"
    fuga_desc = cat_entry.get("fuga_desc", "Düz Masif Panel") if cat_entry else "Düz Masif Panel"
    has_cam = cat_entry.get("has_cam", False) if cat_entry else False
    has_fuga = cat_entry.get("has_fuga", False) if cat_entry else False
    model_name = cat_entry.get("name", specs.get("model_code", "ER100")) if cat_entry else specs.get("model_code", "ER100")
    series_name = cat_entry.get("series", "Daphne Serisi") if cat_entry else "Daphne Serisi"
    
    model_code = specs.get("model_code", "ER100")
    clean_code = model_code.replace(" ", "_").upper()
    ascii_code = clean_code.replace("Ö", "O").replace("Ü", "U").replace("Ç", "C").replace("Ş", "S").replace("İ", "I").replace("Ğ", "G")
    base_img = os.path.splitext(pattern_img)[0]
    
    leaf_url = pattern_url
    for c in [f"{clean_code}.jpg", f"{ascii_code}.jpg", f"{base_img}.jpg"]:
        if os.path.exists(os.path.join("static", "door_leaves", c)):
            leaf_url = f"/static/door_leaves/{c}"
            break

    return {
        "order_id": oid,
        "order_code": order.get("order_no", oid),
        "order_no": order.get("order_no", oid),
        "customer": order.get("customer", ""),
        "model": order.get("model", ""),
        "model_code": specs.get("model_code", "ER100"),
        "model_name": model_name,
        "series": series_name,
        "pattern_image": pattern_img,
        "pattern_url": pattern_url,
        "leaf_texture_url": leaf_url,
        "has_fuga": has_fuga,
        "has_cam": has_cam,
        "fuga_pattern": {
            "type": fuga_type,
            "description": fuga_desc,
            "width_mm": 8.0,
            "depth_mm": 2.5
        },
        "color": color_key,
        "color_hex": color_info["hex"],
        "core_type": specs["core_type"],
        "is_single_piece_core": True,  # Tek parça yekpare EPS dolgu köpüğü
        "dimensions": {
            "width": w,
            "height": h,
            "thickness": th,
            "panel_thickness": panel_th,
            "carcass_thickness": seren_th,
            "seren_width": seren_w,
            "core_width": core_w,
            "core_height": core_h
        },
        "seren_breakdown": {
            "total_meters": specs["consumptions"]["seren_m"],
            "boy_count": 3.5,
            "left_stile": {"len": h, "w": seren_w, "th": seren_th},
            "right_stile": {"len": h, "w": seren_w, "th": seren_th},
            "top_rail": {"len": core_w, "w": seren_w, "th": seren_th},
            "bottom_rail": {"len": core_w, "w": seren_w, "th": seren_th},
            "lock_reinforcement": {"len": 1150, "w": seren_w, "th": seren_th, "pos_y": 1000}
        },
        "corner_wedges": [
            {"id": "top_left", "name": "Sol Üst Plastik Köşe Takozu", "w": 70, "h": 70, "th": 30},
            {"id": "top_right", "name": "Sağ Üst Plastik Köşe Takozu", "w": 70, "h": 70, "th": 30},
            {"id": "bottom_left", "name": "Sol Alt Plastik Köşe Takozu", "w": 70, "h": 70, "th": 30},
            {"id": "bottom_right", "name": "Sağ Alt Plastik Köşe Takozu", "w": 70, "h": 70, "th": 30}
        ],
        "takozlar": [
            {"name": "Masif Ahşap Kilit Takozu", "w": 80, "h": 250, "th": seren_th, "side": "right", "pos_y": 1000},
            {"name": "Masif Ahşap Kol Takozu", "w": 80, "h": 120, "th": seren_th, "side": "right", "pos_y": 1050}
        ],
        "pvc_edge": {
            "thickness": 1.0,
            "width": 45.0,
            "total_meters": specs["consumptions"]["pvc_m"]
        },
        "assembly_steps": [
            {
                "step": 1,
                "title": "Adım 1: 4 Seren & Plastik Köşe Takozları ile Karkas Çatma",
                "station": "Seren Çatma Masası",
                "badge": "1. ÇATI KARKASI",
                "desc": "Sol ve sağ boy serenler ile alt ve üst başlık serenleri 4 köşedeki mukavemetli Plastik Köşe Takozları ile birleştirilerek gönyeli çatı karkası oluşturulur.",
                "parts": ["Sol Boy Seren (2020mm)", "Sağ Boy Seren (2020mm)", "Üst En Seren", "Alt En Seren", "4 Adet Plastik Köşe Takozu"]
            },
            {
                "step": 2,
                "title": "Adım 2: Kilit Takviye Sereni & Masif Ahşap Takozlar",
                "station": "Kilit Takoz İstasyonu",
                "badge": "2. KİLİT TAKVİYESİ",
                "desc": "3.5 boy seren standardına göre kilit aksına 1150 mm kilit takviye sereni ve masif ahşap kilit & kol montaj takozları monte edilir.",
                "parts": ["1150 mm Kilit Takviye Sereni", "Masif Ahşap Kilit Takozu (80x250mm)", "Masif Ahşap Kol Takozu (80x120mm)"]
            },
            {
                "step": 3,
                "title": "Adım 3: Tek Parça EPS Dolgu Köpüğünün Yerleştirilmesi",
                "station": "CNC Dolgu Hattı",
                "badge": "3. TEK PARÇA KÖPÜK",
                "desc": "2 ayrı parça yerine tam net ebatlanmış yekpare TEK PARÇA EPS strafor dolgu köpüğü karkas boşluğuna yerleştirilir.",
                "parts": ["Yekpare Tek Parça EPS Strafor Blok (32mm)"]
            },
            {
                "step": 4,
                "title": "Adım 4: Tutkallama & WPC Kompozit Panellerin Preslenmesi",
                "station": "Sıcak Pres Hattı",
                "badge": "4. SICAK PRES",
                "desc": "Tutkallanan karkasın alt ve üst yüzeyine 4 mm kalınlığında WPC kompozit kapı panelleri yüksek basınç ve sıcaklık altında preslenir.",
                "parts": ["Arka WPC Panel (4 mm)", "Ön WPC Panel (4 mm)"]
            },
            {
                "step": 5,
                "title": "Adım 5: CNC Ebatlama & 4 Kenar PVC Kenar Bandı",
                "station": "Homag Kenar Bantlama & CNC",
                "badge": "5. NİHAİ KANAT",
                "desc": "Homag makinesinde 4 kenara 45x1 mm PVC bant çekilir ve CNC istasyonunda kilit/kol yerleri ile model deseni açılarak kanat tamamlanır.",
                "parts": ["4 Kenar PVC Kenar Bandı", "CNC Fuga & Kilit Boşaltmaları"]
            }
        ]
    }

# ════════════════════════════════════════════════════════════
# 📐 AI DESTEKLİ 2D PLAKA KESİM & NESTİNG MOTORU (MADDE 1)
# ════════════════════════════════════════════════════════════

class NestingPartItem(BaseModel):
    id: Optional[str] = "P1"
    name: Optional[str] = "Parça"
    order_no: Optional[str] = ""
    order_id: Optional[str] = ""
    customer: Optional[str] = ""
    width: float
    height: float
    qty: int = 1
    color: Optional[str] = "#3B82F6"
    material: Optional[str] = "MDF"
    category: Optional[str] = "Yüzey Paneli"
    can_rotate: Optional[bool] = False
    allow_cross_grain: Optional[bool] = False

class NestingRequest(BaseModel):
    sheet_width: float = 2100.0
    sheet_height: float = 2800.0
    blade_kerf: float = 3.2
    trim_margin: float = 10.0
    grain_direction: str = "vertical"  # "vertical", "horizontal", "none"
    auto_orient_sheet: bool = True
    sheet_cost_tl: float = 1150.0
    parts: List[NestingPartItem] = []

class AdvancedNestingOptimizer:
    def __init__(self, sheet_width=2100.0, sheet_height=2800.0, kerf=3.2, trim=10.0, grain='vertical', auto_orient=True, sheet_cost=1150.0):
        self.sheet_width = float(sheet_width)
        self.sheet_height = float(sheet_height)
        self.kerf = float(kerf)
        self.trim = float(trim)
        self.grain = grain
        self.auto_orient = auto_orient
        self.sheet_cost = float(sheet_cost)

    def optimize(self, items):
        start_t = datetime.now()
        
        parts = []
        for it in items:
            qty = int(it.get('qty', 1))
            for i in range(qty):
                p = dict(it)
                p['qty'] = 1
                p['instance_id'] = f"{it.get('id', 'P')}_{i+1}"
                parts.append(p)
                
        if not parts:
            return self._empty_result()
            
        orientations = []
        if self.auto_orient and abs(self.sheet_width - self.sheet_height) > 1:
            orientations = [
                (self.sheet_width, self.sheet_height),
                (self.sheet_height, self.sheet_width)
            ]
        else:
            orientations = [(self.sheet_width, self.sheet_height)]
            
        strategies = ['area_desc', 'max_dim_desc', 'height_desc', 'width_desc']
        cut_heuristics = ['rip_first', 'cross_first', 'balanced']
        
        best_plan = None
        best_score = (-float('inf'), -float('inf'))
        
        for sw, sh in orientations:
            usable_w = sw - 2 * self.trim
            usable_h = sh - 2 * self.trim
            if usable_w <= 0 or usable_h <= 0:
                continue
                
            for strat in strategies:
                sorted_parts = self._sort_parts(parts, strat)
                for cut_type in cut_heuristics:
                    candidate = self._pack_with_params(sorted_parts, sw, sh, usable_w, usable_h, cut_type)
                    summary = candidate['summary']
                    sheets_count = summary['total_sheets']
                    eff = summary['efficiency_pct']
                    score = (-sheets_count, eff)
                    if score > best_score:
                        best_score = score
                        best_plan = candidate
                        
        elapsed_ms = (datetime.now() - start_t).total_seconds() * 1000.0
        if best_plan:
            best_plan['summary']['computation_time_ms'] = round(elapsed_ms, 1)
            total_sheets = best_plan['summary']['total_sheets']
            total_cost = total_sheets * self.sheet_cost
            placed_count = best_plan['summary']['placed_parts']
            cost_per_part = (total_cost / placed_count) if placed_count > 0 else 0
            
            waste_pct = best_plan['summary']['waste_pct']
            baseline_waste_pct = 22.0
            saved_waste_pct = max(0.0, baseline_waste_pct - waste_pct)
            saved_money = (saved_waste_pct / 100.0) * total_cost
            
            best_plan['summary']['total_cost_tl'] = round(total_cost, 2)
            best_plan['summary']['cost_per_part_tl'] = round(cost_per_part, 2)
            best_plan['summary']['saved_money_tl'] = round(saved_money, 2)
            best_plan['summary']['saved_waste_pct'] = round(saved_waste_pct, 1)
            best_plan['summary']['selected_sheet_orientation'] = f"{best_plan['sheet_width']} x {best_plan['sheet_height']} mm"
            
        return best_plan

    def _empty_result(self):
        return {
            'summary': {
                'total_parts': 0, 'placed_parts': 0, 'unplaced_parts': 0, 'total_sheets': 0,
                'total_parts_area_m2': 0, 'total_sheet_area_m2': 0, 'total_waste_area_m2': 0,
                'efficiency_pct': 0, 'waste_pct': 0, 'computation_time_ms': 0,
                'total_cost_tl': 0, 'cost_per_part_tl': 0, 'saved_money_tl': 0, 'saved_waste_pct': 0
            },
            'sheet_width': self.sheet_width,
            'sheet_height': self.sheet_height,
            'sheets': [],
            'unplaced': []
        }

    def _sort_parts(self, parts, strategy):
        p = list(parts)
        if strategy == 'area_desc':
            p.sort(key=lambda x: x['width'] * x['height'], reverse=True)
        elif strategy == 'max_dim_desc':
            p.sort(key=lambda x: max(x['width'], x['height']), reverse=True)
        elif strategy == 'height_desc':
            p.sort(key=lambda x: (x['height'], x['width']), reverse=True)
        elif strategy == 'width_desc':
            p.sort(key=lambda x: (x['width'], x['height']), reverse=True)
        return p

    def _pack_with_params(self, parts, sw, sh, usable_w, usable_h, cut_type):
        sheets = []
        unplaced = []
        
        for part in parts:
            pw, ph = float(part['width']), float(part['height'])
            can_rot = bool(part.get('can_rotate', False))
            if self.grain == 'none':
                can_rot = True
            elif self.grain == 'vertical' and not part.get('allow_cross_grain', False):
                can_rot = False
                
            placed = False
            for s in sheets:
                rect_idx, rot = self._find_fit(s['free_rects'], pw, ph, can_rot)
                if rect_idx is not None:
                    self._place_and_split(s, rect_idx, part, pw, ph, rot, cut_type)
                    placed = True
                    break
                    
            if not placed:
                new_sheet = {
                    'sheet_index': len(sheets) + 1,
                    'sheet_width': sw,
                    'sheet_height': sh,
                    'placed_parts': [],
                    'free_rects': [{'x': self.trim, 'y': self.trim, 'w': usable_w, 'h': usable_h}],
                    'cut_lines': []
                }
                rect_idx, rot = self._find_fit(new_sheet['free_rects'], pw, ph, can_rot)
                if rect_idx is not None:
                    self._place_and_split(new_sheet, rect_idx, part, pw, ph, rot, cut_type)
                    sheets.append(new_sheet)
                    placed = True
                else:
                    unplaced.append(part)
                    
        total_sheet_area = len(sheets) * (sw * sh) * 1e-6
        total_parts_area = sum(p['width'] * p['height'] for s in sheets for p in s['placed_parts']) * 1e-6
        total_waste_area = max(0.0, total_sheet_area - total_parts_area)
        overall_eff = (total_parts_area / total_sheet_area * 100) if total_sheet_area > 0 else 0
        
        for s in sheets:
            s_parts_area = sum(p['width'] * p['height'] for p in s['placed_parts']) * 1e-6
            s_total_area = (sw * sh) * 1e-6
            s['efficiency_pct'] = round((s_parts_area / s_total_area) * 100, 1)
            s['waste_area_m2'] = round(max(0.0, s_total_area - s_parts_area), 3)
            s['waste_rects'] = []
            for r in s['free_rects']:
                if r['w'] >= 10 and r['h'] >= 10:
                    area_m2 = (r['w'] * r['h']) * 1e-6
                    is_reusable = (r['w'] >= 100 and r['h'] >= 300) or (r['h'] >= 100 and r['w'] >= 300)
                    s['waste_rects'].append({
                        'x': round(r['x'], 1),
                        'y': round(r['y'], 1),
                        'w': round(r['w'], 1),
                        'h': round(r['h'], 1),
                        'area_m2': round(area_m2, 3),
                        'is_reusable': is_reusable
                    })
            del s['free_rects']
            
        return {
            'summary': {
                'total_parts': len(parts),
                'placed_parts': sum(len(s['placed_parts']) for s in sheets),
                'unplaced_parts': len(unplaced),
                'total_sheets': len(sheets),
                'total_parts_area_m2': round(total_parts_area, 3),
                'total_sheet_area_m2': round(total_sheet_area, 3),
                'total_waste_area_m2': round(total_waste_area, 3),
                'efficiency_pct': round(overall_eff, 1),
                'waste_pct': round(max(0.0, 100.0 - overall_eff), 1)
            },
            'sheet_width': sw,
            'sheet_height': sh,
            'sheets': sheets,
            'unplaced': unplaced
        }

    def _find_fit(self, free_rects, pw, ph, can_rot):
        best_idx = None
        best_rot = False
        min_rem_area = float('inf')
        
        for idx, r in enumerate(free_rects):
            rw, rh = r['w'], r['h']
            if pw <= rw and ph <= rh:
                rem_area = (rw * rh) - (pw * ph)
                if rem_area < min_rem_area:
                    min_rem_area = rem_area
                    best_idx = idx
                    best_rot = False
            if can_rot and ph <= rw and pw <= rh:
                rem_area = (rw * rh) - (pw * ph)
                if rem_area < min_rem_area:
                    min_rem_area = rem_area
                    best_idx = idx
                    best_rot = True
                    
        return best_idx, best_rot

    def _place_and_split(self, sheet, rect_idx, part, pw, ph, rot, cut_type):
        w = ph if rot else pw
        h = pw if rot else ph
        target = sheet['free_rects'].pop(rect_idx)
        rx, ry, rw, rh = target['x'], target['y'], target['w'], target['h']
        
        placed_obj = {
            'instance_id': part.get('instance_id', ''),
            'id': part.get('id', ''),
            'name': part.get('name', 'Parça'),
            'order_no': part.get('order_no', ''),
            'customer': part.get('customer', ''),
            'color': part.get('color', '#3B82F6'),
            'material': part.get('material', 'MDF'),
            'x': round(rx, 1),
            'y': round(ry, 1),
            'width': round(w, 1),
            'height': round(h, 1),
            'orig_width': pw,
            'orig_height': ph,
            'rotated': rot
        }
        sheet['placed_parts'].append(placed_obj)
        
        rem_w = rw - w - self.kerf
        rem_h = rh - h - self.kerf
        step_no = len(sheet['cut_lines']) + 1
        new_rects = []
        
        if cut_type == 'rip_first' or (cut_type == 'balanced' and rem_w >= rem_h):
            if rem_w > 0:
                new_rects.append({'x': rx + w + self.kerf, 'y': ry, 'w': rem_w, 'h': h})
            if rem_h > 0:
                new_rects.append({'x': rx, 'y': ry + h + self.kerf, 'w': rw, 'h': rem_h})
            sheet['cut_lines'].append({
                'step': step_no,
                'x1': round(rx, 1), 'y1': round(ry + h, 1),
                'x2': round(rx + rw, 1), 'y2': round(ry + h, 1),
                'cut_type': 'Boyuna Kesim (Rip Cut)',
                'dimension_mm': round(ry + h, 1)
            })
        else:
            if rem_h > 0:
                new_rects.append({'x': rx, 'y': ry + h + self.kerf, 'w': w, 'h': rem_h})
            if rem_w > 0:
                new_rects.append({'x': rx + w + self.kerf, 'y': ry, 'w': rem_w, 'h': rh})
            sheet['cut_lines'].append({
                'step': step_no,
                'x1': round(rx + w, 1), 'y1': round(ry, 1),
                'x2': round(rx + w, 1), 'y2': round(ry + rh, 1),
                'cut_type': 'Enine Kesim (Cross Cut)',
                'dimension_mm': round(rx + w, 1)
            })
            
        sheet['free_rects'].extend(new_rects)

@app.get("/api/nesting/presets")
def get_nesting_presets():
    return {
        "presets": [
            {"id": "std_2100_2800", "name": "Standart Ham MDF (2100 x 2800 mm)", "width": 2100, "height": 2800, "cost": 1150.0},
            {"id": "wide_1830_3660", "name": "Geniş Format MDF (1830 x 3660 mm)", "width": 1830, "height": 3660, "cost": 1450.0},
            {"id": "high_2200_2800", "name": "Yüksek Kapı Formatı (2200 x 2800 mm)", "width": 2200, "height": 2800, "cost": 1280.0},
            {"id": "ply_1220_2440", "name": "Marin Kontrplak / Plywood (1220 x 2440 mm)", "width": 1220, "height": 2440, "cost": 920.0},
            {"id": "compact_1300_3050", "name": "Kompakt Laminat (1300 x 3050 mm)", "width": 1300, "height": 3050, "cost": 2100.0}
        ],
        "default_kerf": 3.2,
        "default_trim": 10.0,
        "default_grain": "vertical"
    }

@app.get("/api/nesting/orders-parts")
def get_nesting_orders_parts(filter_type: Optional[str] = "panels", status: Optional[str] = "open"):
    d = load_data()
    orders = d.get("orders", {})
    parts_list = []
    
    color_palette = [
        "#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", 
        "#EC4899", "#06B6D4", "#F97316", "#14B8A6", "#6366F1"
    ]
    color_map = {}
    color_idx = 0
    
    for oid, o in orders.items():
        if status and o.get("status") != status:
            continue
            
        m_str = o.get("model", "")
        specs = parse_door_specs(m_str, custom_color=o.get("color"))
        w = float(specs["width"])
        h = float(specs["height"])
        qty = int(o.get("qty", 1))
        order_no = o.get("order_no", oid)
        customer = o.get("customer", "Müşteri")
        model_name = specs.get("model_code", "ER100")
        color_name = specs.get("color", "DİŞBUDAK BEYAZ")
        
        if color_name not in color_map:
            color_map[color_name] = color_palette[color_idx % len(color_palette)]
            color_idx += 1
        part_color = color_map[color_name]
        
        # 1. Yüzey Panelleri (2 adet/kapı: Ön & Arka MDF)
        if filter_type in ("panels", "all"):
            parts_list.append({
                "id": f"PANEL_{oid}",
                "name": f"{model_name} Yüzey Paneli ({int(w)}x{int(h)})",
                "category": "Yüzey Paneli (MDF/WPC)",
                "order_no": order_no,
                "order_id": oid,
                "customer": customer,
                "width": w,
                "height": h,
                "qty": qty * 2,
                "color": part_color,
                "material": f"4mm MDF - {color_name}",
                "can_rotate": False if "BEYAZ" not in color_name and "LAKE" not in color_name else True,
                "allow_cross_grain": False
            })
            
        # 2. Boy & En Seren Çıtaları
        if filter_type in ("stiles", "all"):
            parts_list.append({
                "id": f"SEREN_BOY_{oid}",
                "name": f"Boy Seren (42x{int(h)})",
                "category": "Seren & Karkas",
                "order_no": order_no,
                "order_id": oid,
                "customer": customer,
                "width": 42.0,
                "height": h,
                "qty": qty * 2,
                "color": "#D97706",
                "material": "Kompozit Ahşap Seren (42x42)",
                "can_rotate": True,
                "allow_cross_grain": True
            })
            en_len = max(100.0, w - 84.0)
            parts_list.append({
                "id": f"SEREN_EN_{oid}",
                "name": f"En Seren (42x{int(en_len)})",
                "category": "Seren & Karkas",
                "order_no": order_no,
                "order_id": oid,
                "customer": customer,
                "width": 42.0,
                "height": en_len,
                "qty": qty * 2,
                "color": "#B45309",
                "material": "Kompozit Ahşap Seren (42x42)",
                "can_rotate": True,
                "allow_cross_grain": True
            })
            parts_list.append({
                "id": f"SEREN_KILIT_{oid}",
                "name": "Kilit Takviye Sereni (80x1150)",
                "category": "Seren & Karkas",
                "order_no": order_no,
                "order_id": oid,
                "customer": customer,
                "width": 80.0,
                "height": 1150.0,
                "qty": qty,
                "color": "#92400E",
                "material": "Masif Ahşap Kilit Takviyesi",
                "can_rotate": True,
                "allow_cross_grain": True
            })

        # 3. Dolgu Strafor Köpüğü
        if filter_type in ("core", "all"):
            core_w = max(100.0, w - 84.0)
            core_h = max(100.0, h - 84.0)
            parts_list.append({
                "id": f"CORE_EPS_{oid}",
                "name": f"Yekpare EPS Dolgu ({int(core_w)}x{int(core_h)})",
                "category": "Dolgu Strafor",
                "order_no": order_no,
                "order_id": oid,
                "customer": customer,
                "width": core_w,
                "height": core_h,
                "qty": qty,
                "color": "#94A3B8",
                "material": "32mm EPS Strafor Blok",
                "can_rotate": True,
                "allow_cross_grain": True
            })

    total_parts_count = sum(p["qty"] for p in parts_list)
    return {
        "parts": parts_list,
        "total_part_types": len(parts_list),
        "total_pieces_qty": total_parts_count,
        "filter_type": filter_type,
        "active_orders_count": len([o for o in orders.values() if o.get("status") == status])
    }

@app.post("/api/nesting/optimize")
def run_nesting_optimization(req: NestingRequest):
    optimizer = AdvancedNestingOptimizer(
        sheet_width=req.sheet_width,
        sheet_height=req.sheet_height,
        kerf=req.blade_kerf,
        trim=req.trim_margin,
        grain=req.grain_direction,
        auto_orient=req.auto_orient_sheet,
        sheet_cost=req.sheet_cost_tl
    )
    parts_data = [p.dict() for p in req.parts]
    result = optimizer.optimize(parts_data)
    return result


app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse(
        "static/index.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_backend:app", host="0.0.0.0", port=8001, reload=True)