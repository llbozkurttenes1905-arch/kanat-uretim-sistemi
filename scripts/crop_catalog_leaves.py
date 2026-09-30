"""
Erdoor Katalog Fotoğraflarından Temiz Kanat Yüzeyi (Door Leaf) Çıkarıcı
-------------------------------------------------------------------------
Erdoor resmi kataloğundaki ('ERDOOR ÜRETİLEN KAPILAR 24.06.2026 (1).docx')
54 kapı modelinin gerçek fotoğraflarını inceler; pervaz, kasa, zemin ve
çerçeveleri temizleyerek yalnızca kapı kanat yüzeyini çıkarır ve
'static/door_leaves/<MODEL_CODE>.jpg' olarak kaydeder.
"""

import os
from PIL import Image, ImageOps, ImageFilter
import numpy as np

import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
PATTERNS_DIR = os.path.join(BASE_DIR, "static", "door_patterns")
LEAVES_DIR = os.path.join(BASE_DIR, "static", "door_leaves")
os.makedirs(LEAVES_DIR, exist_ok=True)

# Manuel hassas kırpma kutuları (x1, y1, x2, y2)
# Bu kutular doğrudan kapı kanadının (leaf) 4 kenarını belirler.
EXPLICIT_CROPS = {
    # er210, er220, er230 (showroom 3'lü kapı panosu)
    "ER210": ("er210.png", (618, 165, 2048, 3280)),
    "ER220": ("er220.png", (315, 120, 1720, 3370)),
    "ER230": ("er230.png", (70, 120, 1620, 3370)),

    # Daphne Özel Serisi (Fabrika & Showroom gerçek fotoğrafları)
    "ER550": ("image49.jpeg", (173, 114, 508, 916)),  # 5 yatay kapsül oluk ve çizgiler
    "ER590": ("image50.jpeg", (167, 120, 497, 888)),  # 5 yamuk panel & dikey hat
    "ER540": ("image51.jpeg", (130, 72, 436, 908)),   # Kum saati & taç CNC oyma
    "ER560": ("image52.jpeg", (130, 48, 580, 1260)),  # Dikey boy ve 5 üçgen form
    "ER570": ("image53.jpeg", (140, 120, 610, 1290)), # Hilal / kavis ve 2 dikdörtgen
    "ER520": ("image54.jpeg", (82, 35, 412, 805)),    # Alev / kuğu akıcı dalga CNC
    "ER330": ("image55.jpeg", (180, 140, 670, 1420)), # 3 iç içe konsantrik çerçeve
    "ER400": ("image56.jpeg", (75, 80, 570, 1500)),   # Sivri oval / baklava CNC
    "ER500": ("image57.jpeg", (105, 70, 640, 1280)),  # Klasik kemerli 2 panel taçlı

    # Standart 685px Siyah Stüdyo Modelleri
    "ER17":  ("image17.jpeg", (124, 76, 558, 1102)), # ER620 dev elips
    "ER620": ("image17.jpeg", (124, 76, 558, 1102)),
    "ER20":  ("image20.jpeg", (122, 78, 554, 1102)), # ER900 geometrik
    "ER900": ("image20.jpeg", (122, 78, 554, 1102)),
    "ER901": ("image41.jpeg", (122, 80, 555, 1105)), # ER901 camlı geometrik
    "ER21":  ("image21.jpeg", (127, 75, 558, 1103)), # ER930 6 panel
    "ER930": ("image21.jpeg", (127, 75, 558, 1103)),
    "ER931": ("image42.jpeg", (127, 85, 557, 1103)), # ER931 6 panel camlı
    "ER25":  ("image25.jpeg", (124, 78, 558, 1100)), # ER1004 kademeli çift çizgiler
    "ER1004":("image25.jpeg", (124, 78, 558, 1100)),
    "ER27":  ("image27.jpeg", (121, 80, 558, 1098)), # ER1006 8 yatay yastık panel
    "ER1006":("image27.jpeg", (121, 80, 558, 1098)),
    "ER31":  ("image31.jpeg", (88, 54, 545, 1242)),  # ER1014 2 panel klasik
    "ER1014":("image31.jpeg", (88, 54, 545, 1242)),
    "ER32":  ("image32.jpeg", (90, 78, 566, 1243)),  # ER1014 ÖZEL sağ 3 dikey hat
    "ER1014 ÖZEL": ("image32.jpeg", (90, 78, 566, 1243)),

    # 288px Siyah Stüdyo Modelleri
    "ER300": ("image12.jpeg", (32, 33, 254, 607)),   # 4 yatay eşit panel
    "ER510": ("image13.jpeg", (22, 36, 259, 608)),   # Orta oval madalyon
    "ER800": ("image19.jpeg", (26, 34, 257, 608)),   # Sol boy + sağ 4 kare panel
    "ER1005":("image26.jpeg", (24, 36, 254, 606)),   # Labirent / mozaik ızgara
    "ER5012":("image45.jpeg", (35, 33, 265, 618)),   # Titus CNC kesişen
    "ER5014":("image46.jpeg", (30, 35, 255, 613)),   # Titus CNC çerçeve
}

def auto_crop_leaf(im):
    """
    Şeffaf (RGBA) veya siyah arka planlı kapı görselinden
    iç kapı kanadını (leaf) otomatik olarak tespit edip kırpar.
    """
    arr = np.array(im)
    is_rgba = (arr.shape[2] >= 4)
    
    if is_rgba:
        alpha = arr[:, :, 3]
        mask = (alpha > 80)
    else:
        gray = np.mean(arr[:, :, :3], axis=2)
        mask = (gray > 25)
        
    row_sum = np.sum(mask, axis=1)
    col_sum = np.sum(mask, axis=0)
    rows = np.where(row_sum > 60)[0]
    cols = np.where(col_sum > 60)[0]
    
    if len(rows) == 0 or len(cols) == 0:
        return im.crop((0, 0, im.size[0], im.size[1]))
        
    y1, y2 = int(rows[0]), int(rows[-1])
    x1, x2 = int(cols[0]), int(cols[-1])
    w = x2 - x1
    h = y2 - y1
    
    # Kapı pervaz genişliği genelde toplam genişliğin %8-15'idir
    # İç derz/birleşim çizgisini arayalım
    mid_y = int((y1 + y2) / 2)
    row_rgb = arr[mid_y, x1:x2, :3].astype(float)
    diff_x = np.abs(np.diff(row_rgb, axis=0)).sum(axis=1)
    
    l_min, l_max = int(w * 0.06), int(w * 0.26)
    r_min, r_max = int(w * 0.74), int(w * 0.94)
    
    seam_l = x1 + l_min + int(np.argmax(diff_x[l_min:l_max])) if l_max > l_min else x1 + int(w * 0.10)
    seam_r = x1 + r_min + int(np.argmax(diff_x[r_min:r_max])) if r_max > r_min else x2 - int(w * 0.10)
    
    mid_x = int((seam_l + seam_r) / 2)
    col_rgb = arr[y1:y2, mid_x, :3].astype(float)
    diff_y = np.abs(np.diff(col_rgb, axis=0)).sum(axis=1)
    t_min, t_max = int(h * 0.03), int(h * 0.12)
    seam_t = y1 + t_min + int(np.argmax(diff_y[t_min:t_max])) if t_max > t_min else y1 + int(h * 0.05)
    
    seam_b = y2 - int(h * 0.015)
    
    # Güvenlik kontrolü
    if (seam_r - seam_l) < w * 0.5:
        seam_l = x1 + int(w * 0.10)
        seam_r = x2 - int(w * 0.10)
    if (seam_b - seam_t) < h * 0.7:
        seam_t = y1 + int(h * 0.05)
        seam_b = y2
        
    return im.crop((seam_l, seam_t, seam_r, seam_b))


def process_all_models():
    import app_backend
    models = app_backend.ERDOOR_MODELS_CATALOG
    print(f"Toplam {len(models)} model işleniyor...")

    target_w, target_h = 512, 1292  # 800:2020 oranına birebir denk 1:2.525 UV dokusu

    results = {}
    for m in models:
        code = m["code"]
        img_name = m["image"]
        img_path = os.path.join(PATTERNS_DIR, img_name)

        if not os.path.exists(img_path):
            print(f"UYARI: {img_path} bulunamadı!")
            continue

        try:
            with Image.open(img_path) as im:
                if code in EXPLICIT_CROPS:
                    source_file, box = EXPLICIT_CROPS[code]
                    if source_file != img_name:
                        # Başka kaynak dosyadan (örnek er210.png)
                        source_path = os.path.join(PATTERNS_DIR, source_file)
                        with Image.open(source_path) as sim:
                            leaf = sim.crop(box)
                    else:
                        leaf = im.crop(box)
                else:
                    leaf = auto_crop_leaf(im)

                # Kanat yüzeyini RGB moduna çevir ve standart 512x1292 boyutuna yüksek kalitede ölçekle
                leaf_rgb = leaf.convert("RGB")
                leaf_resized = leaf_rgb.resize((target_w, target_h), Image.Resampling.LANCZOS)

                # 1. Kod adına göre kaydet: ER1004.jpg
                clean_code = code.replace(" ", "_").upper()
                out_path_code = os.path.join(LEAVES_DIR, f"{clean_code}.jpg")
                leaf_resized.save(out_path_code, "JPEG", quality=92)

                # ASCII uyumlu yedek kopya (ER1014_OZEL.jpg)
                ascii_code = clean_code.replace("Ö", "O").replace("Ü", "U").replace("Ç", "C").replace("Ş", "S").replace("İ", "I").replace("Ğ", "G")
                if ascii_code != clean_code:
                    out_path_ascii = os.path.join(LEAVES_DIR, f"{ascii_code}.jpg")
                    leaf_resized.save(out_path_ascii, "JPEG", quality=92)

                # 2. Resim adına göre de kaydet: image25.jpg
                base_img_name = os.path.splitext(img_name)[0]
                out_path_img = os.path.join(LEAVES_DIR, f"{base_img_name}.jpg")
                leaf_resized.save(out_path_img, "JPEG", quality=92)

                results[code] = f"/static/door_leaves/{clean_code}.jpg"
                print(f"OK: [{code:12s}] -> {out_path_code} (Kaynak: {img_name})")

        except Exception as e:
            print(f"HATA [{code}]: {e}")

    print(f"\nTamamlandı! Toplam {len(results)} kapı kanadı dokusu oluşturuldu.")
    return results

if __name__ == "__main__":
    process_all_models()
