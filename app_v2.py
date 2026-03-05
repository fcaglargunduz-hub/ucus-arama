import streamlit as st
import requests
import base64
import time
from datetime import date, timedelta

st.set_page_config(
    page_title="SAW Uçuş Arama",
    page_icon="✈️",
    layout="wide",
)

# ─── HAVALIMANL VERİTABANI ────────────────────────────────────────────────────

AIRPORT_REGIONS = {
    "🌊 Adalar & Akdeniz": [
        ("ECN", "Ercan, KKTC"),
        ("LCA", "Larnaka, Kıbrıs"),
        ("HER", "Heraklion, Girit"),
        ("CHQ", "Chania, Girit"),
        ("RHO", "Rodos"),
        ("KGS", "Kos"),
        ("CFU", "Korfu"),
        ("JTR", "Santorini"),
        ("MYK", "Midilli / Lesbos"),
        ("SMI", "Sisam / Samos"),
        ("MLA", "Malta"),
        ("NCE", "Nice, Fransa"),
        ("MRS", "Marsilya, Fransa"),
        ("PMI", "Palma de Mallorca"),
        ("IBZ", "İbiza"),
    ],
    "🇪🇺 Güney & Orta Avrupa": [
        ("ATH", "Atina, Yunanistan"),
        ("SKG", "Selanik, Yunanistan"),
        ("FCO", "Roma, İtalya"),
        ("MXP", "Milano Malpensa, İtalya"),
        ("LIN", "Milano Linate, İtalya"),
        ("VIE", "Viyana, Avusturya"),
        ("ZRH", "Zürih, İsviçre"),
        ("GVA", "Cenevre, İsviçre"),
        ("MUC", "Münih, Almanya"),
        ("NUE", "Nürnberg, Almanya"),
        ("STR", "Stuttgart, Almanya"),
        ("PRG", "Prag, Çek Cumhuriyeti"),
        ("BUD", "Budapeşte, Macaristan"),
        ("LJU", "Ljubljana, Slovenya"),
        ("ZAG", "Zagreb, Hırvatistan"),
        ("SPU", "Split, Hırvatistan"),
        ("DBV", "Dubrovnik, Hırvatistan"),
        ("BEG", "Belgrad, Sırbistan"),
        ("SKP", "Üsküp, Kuzey Makedonya"),
        ("TIA", "Tiran, Arnavutluk"),
        ("TGD", "Podgorica, Karadağ"),
    ],
    "🇪🇺 Batı & Kuzey Avrupa": [
        ("FRA", "Frankfurt, Almanya"),
        ("BER", "Berlin, Almanya"),
        ("HAM", "Hamburg, Almanya"),
        ("CGN", "Köln/Bonn, Almanya"),
        ("DUS", "Düsseldorf, Almanya"),
        ("BRU", "Brüksel, Belçika"),
        ("AMS", "Amsterdam, Hollanda"),
        ("CDG", "Paris CDG, Fransa"),
        ("ORY", "Paris Orly, Fransa"),
        ("CPH", "Kopenhag, Danimarka"),
        ("ARN", "Stockholm, İsveç"),
        ("HEL", "Helsinki, Finlandiya"),
        ("OSL", "Oslo, Norveç"),
        ("STN", "Londra Stansted, UK"),
        ("LGW", "Londra Gatwick, UK"),
        ("BCN", "Barselona, İspanya"),
        ("MAD", "Madrid, İspanya"),
        ("LIS", "Lizbon, Portekiz"),
    ],
    "🌍 Balkanlar & Doğu Avrupa": [
        ("OTP", "Bükreş, Romanya"),
        ("SOF", "Sofya, Bulgaristan"),
        ("VAR", "Varna, Bulgaristan"),
        ("BOJ", "Burgaz, Bulgaristan"),
        ("WAW", "Varşova, Polonya"),
        ("KRK", "Krakow, Polonya"),
        ("KTW", "Katowice, Polonya"),
        ("WRO", "Wrocław, Polonya"),
        ("GDN", "Gdansk, Polonya"),
        ("KBP", "Kyiv Boryspil, Ukrayna"),
        ("IEV", "Kyiv Zhuliany, Ukrayna"),
        ("LWO", "Lviv, Ukrayna"),
        ("ODS", "Odessa, Ukrayna"),
        ("HRK", "Harkiv, Ukrayna"),
    ],
    "🇷🇺 Rusya": [
        ("SVO", "Moskova Şeremetyevo"),
        ("DME", "Moskova Domodedovo"),
        ("VKO", "Moskova Vnukovo"),
        ("LED", "St. Petersburg"),
        ("KZN", "Kazan"),
        ("UFA", "Ufa"),
    ],
    "🍊 Kafkasya": [
        ("TBS", "Tiflis, Gürcistan"),
        ("EVN", "Erivan, Ermenistan"),
        ("LWN", "Gümrü, Ermenistan"),
        ("GYD", "Bakü, Azerbaycan"),
        ("GNJ", "Gence, Azerbaycan"),
    ],
    "🌍 Orta Doğu": [
        ("BEY", "Beyrut, Lübnan"),
        ("TLV", "Tel Aviv, İsrail"),
        ("AMM", "Amman, Ürdün"),
        ("BGW", "Bağdat, Irak"),
        ("BSR", "Basra, Irak"),
        ("NJF", "Necef, Irak"),
        ("EBL", "Erbil, Kuzey Irak"),
        ("ISU", "Süleymaniye, Kuzey Irak"),
        ("KWI", "Kuveyt"),
        ("BAH", "Bahreyn"),
        ("IKA", "Tahran İmam Humeyni, İran"),
        ("THR", "Tahran Mehrabad, İran"),
        ("TBZ", "Tebriz, İran"),
        ("IFN", "Isfahan, İran"),
        ("SYZ", "Şiraz, İran"),
        ("AWZ", "Ahvaz, İran"),
        ("ASB", "Aşkabat, Türkmenistan"),
    ],
    "🌍 Kuzey Afrika": [
        ("CAI", "Kahire, Mısır"),
        ("ALY", "İskenderiye, Mısır"),
        ("HRG", "Hurghada, Mısır"),
        ("SSH", "Sharm el-Sheikh, Mısır"),
        ("LXR", "Luksor, Mısır"),
        ("ASW", "Asvan, Mısır"),
        ("TUN", "Tunus"),
        ("MIR", "Monastir, Tunus"),
        ("DJE", "Cerbe, Tunus"),
        ("TIP", "Trablus, Libya"),
        ("BEN", "Bingazi, Libya"),
        ("ALG", "Cezayir"),
        ("ORN", "Oran, Cezayir"),
    ],
}

# Tüm havalimanları düz liste
ALL_AIRPORTS = {code: name for region_airports in AIRPORT_REGIONS.values()
                for code, name in region_airports}

# ─── KOORDİNATLAR ────────────────────────────────────────────────────────────

AIRPORT_COORDS = {
    # Adalar & Akdeniz
    "ECN": [35.154, 33.496], "LCA": [34.875, 33.625],
    "HER": [35.340, 25.180], "CHQ": [35.532, 24.150],
    "RHO": [36.405, 28.086], "KGS": [36.794, 27.092],
    "CFU": [39.602, 19.912], "JTR": [36.399, 25.479],
    "MYK": [39.056, 26.598], "SMI": [37.690, 26.912],
    "MLA": [35.857, 14.477], "NCE": [43.658,  7.215],
    "MRS": [43.436,  5.215], "PMI": [39.551,  2.739],
    "IBZ": [38.873,  1.373],
    # Güney & Orta Avrupa
    "ATH": [37.936, 23.944], "SKG": [40.520, 22.971],
    "FCO": [41.800, 12.239], "MXP": [45.630,  8.723],
    "LIN": [45.445,  9.277], "VIE": [48.110, 16.570],
    "ZRH": [47.458,  8.548], "GVA": [46.238,  6.109],
    "MUC": [48.354, 11.786], "NUE": [49.499, 11.078],
    "STR": [48.690,  9.222], "PRG": [50.101, 14.260],
    "BUD": [47.433, 19.261], "LJU": [46.224, 14.458],
    "ZAG": [45.742, 16.069], "SPU": [43.538, 16.298],
    "DBV": [42.561, 18.268], "BEG": [44.818, 20.309],
    "SKP": [41.961, 21.621], "TIA": [41.415, 19.721],
    "TGD": [42.360, 19.252],
    # Batı & Kuzey Avrupa
    "FRA": [50.033,  8.570], "BER": [52.366, 13.503],
    "HAM": [53.630,  9.988], "CGN": [50.866,  7.143],
    "DUS": [51.289,  6.767], "BRU": [50.901,  4.484],
    "AMS": [52.308,  4.764], "CDG": [49.009,  2.547],
    "ORY": [48.723,  2.379], "CPH": [55.618, 12.656],
    "ARN": [59.651, 17.919], "HEL": [60.317, 24.963],
    "OSL": [60.193, 11.100], "STN": [51.885,  0.235],
    "LGW": [51.148, -0.190], "BCN": [41.297,  2.078],
    "MAD": [40.472, -3.561], "LIS": [38.774, -9.134],
    # Balkanlar & Doğu Avrupa
    "OTP": [44.572, 26.102], "SOF": [42.696, 23.411],
    "VAR": [43.232, 27.825], "BOJ": [42.568, 27.515],
    "WAW": [52.165, 20.967], "KRK": [50.077, 19.785],
    "KTW": [50.474, 19.080], "WRO": [51.103, 16.886],
    "GDN": [54.377, 18.466], "KBP": [50.345, 30.894],
    "IEV": [50.402, 30.449], "LWO": [49.812, 23.956],
    "ODS": [46.427, 30.676], "HRK": [49.924, 36.290],
    # Rusya
    "SVO": [55.972, 37.415], "DME": [55.408, 37.906],
    "VKO": [55.591, 37.261], "LED": [59.800, 30.262],
    "KZN": [55.606, 49.279], "UFA": [54.557, 55.874],
    # Kafkasya
    "TBS": [41.669, 44.954], "EVN": [40.147, 44.396],
    "LWN": [40.750, 43.859], "GYD": [40.467, 50.047],
    "GNJ": [40.737, 46.317],
    # Orta Doğu
    "BEY": [33.821, 35.488], "TLV": [31.998, 34.878],
    "AMM": [31.722, 35.993], "BGW": [33.263, 44.234],
    "BSR": [30.549, 47.662], "NJF": [31.990, 44.404],
    "EBL": [36.237, 43.963], "ISU": [35.560, 45.317],
    "KWI": [29.227, 47.969], "BAH": [26.271, 50.634],
    "IKA": [35.416, 51.152], "THR": [35.689, 51.314],
    "TBZ": [38.133, 46.235], "IFN": [32.751, 51.861],
    "SYZ": [29.539, 52.590], "AWZ": [31.337, 48.762],
    "ASB": [37.987, 58.361],
    # Kuzey Afrika
    "CAI": [30.122, 31.406], "ALY": [31.184, 29.949],
    "HRG": [27.178, 33.799], "SSH": [27.977, 34.395],
    "LXR": [25.671, 32.707], "ASW": [23.964, 32.820],
    "TUN": [36.851, 10.227], "MIR": [35.758, 10.755],
    "DJE": [33.875, 10.776], "TIP": [32.663, 13.159],
    "BEN": [32.097, 20.269], "ALG": [36.691,  3.215],
    "ORN": [35.624, -0.622],
}

# ─── AYARLAR ──────────────────────────────────────────────────────────────────

ORIGIN       = "SAW"
YEAR         = 2026
MONTHS       = [4, 5, 6]
MONTH_NAMES  = {4: "🌸 Nisan 2026", 5: "🌿 Mayıs 2026", 6: "☀️ Haziran 2026"}
MONTH_SHORT  = ["","Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"]

OUTBOUND_MIN, OUTBOUND_MAX = 9, 15
RETURN_MIN,   RETURN_MAX   = 18, 21

# ─── YARDIMCI ─────────────────────────────────────────────────────────────────

def get_saturdays(months):
    saturdays = []
    for month in months:
        d = date(YEAR, month, 1)
        while d.month == month:
            if d.weekday() == 5:
                saturdays.append(d)
            d += timedelta(days=1)
    return saturdays

def parse_time(t):
    return t.split(" ")[-1] if t else ""

def fmt_price(p):
    if not p:
        return "–"
    return f"₺{int(p):,}".replace(",", ".")

def duration_fmt(mins):
    if not mins:
        return ""
    h, m = divmod(int(mins), 60)
    return f"{h}s {m:02d}dk" if m else f"{h}s"

def build_gf_url(origin, destination, dep_date, ret_date):
    def ap(code):
        return bytes([0x07, 0x08, 0x01, 0x12, 0x03]) + code.encode()
    def leg(fr, to, d):
        body = b'\x12\x0a' + d.encode() + b'\x6a' + ap(fr) + b'\x72' + ap(to)
        return b'\x1a' + bytes([len(body)]) + body
    raw = (b'\x08\x1c\x10\x02'
           + leg(origin, destination, dep_date.isoformat())
           + leg(destination, origin, ret_date.isoformat())
           + b'\x42\x01\x01\x48\x01\x70\x01\x98\x01\x01\xc8\x01\x01')
    tfs = base64.b64encode(raw).decode()
    return f"https://www.google.com/travel/flights/search?tfs={tfs}&curr=TRY&hl=tr"

# ─── ÖNBELLEK (disk + memory) ─────────────────────────────────────────────────

import json, os, hashlib

CACHE_FILE = "flight_cache.json"

def _cache_key(origin, destination, dep_date, ret_date, out_min, out_max, ret_min, ret_max):
    raw = f"{origin}_{destination}_{dep_date}_{ret_date}_{out_min}_{out_max}_{ret_min}_{ret_max}"
    return hashlib.md5(raw.encode()).hexdigest()

def _load_disk_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save_disk_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    except:
        pass

# Memory cache (session boyunca)
if "flight_cache" not in st.session_state:
    st.session_state.flight_cache = _load_disk_cache()

@st.cache_data(ttl=3600, show_spinner=False)  # 1 saat memory cache
def _fetch_raw(api_key, origin, destination, dep_date_str, ret_date_str):
    """Ham SerpAPI çağrısı — sadece cache miss olunca çalışır."""
    params = {
        "engine":        "google_flights",
        "departure_id":  origin,
        "arrival_id":    destination,
        "outbound_date": dep_date_str,
        "return_date":   ret_date_str,
        "adults":        1,
        "currency":      "TRY",
        "hl":            "tr",
        "type":          "1",
        "api_key":       api_key,
    }
    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=30)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def fetch_flights(api_key, origin, destination, dep_date, ret_date,
                  out_min, out_max, ret_min, ret_max):

    key = _cache_key(origin, destination, dep_date, ret_date,
                     out_min, out_max, ret_min, ret_max)

    # 1. Disk cache'e bak
    if key in st.session_state.flight_cache:
        cached = st.session_state.flight_cache[key]
        return cached["outbound"], cached["inbound"], None

    # 2. API'ye git
    data = _fetch_raw(api_key, origin, destination,
                      dep_date.isoformat(), ret_date.isoformat())

    if "error" in data:
        return [], [], data["error"]

    all_flights = data.get("best_flights", []) + data.get("other_flights", [])
    outbound, inbound = [], []

    for bundle in all_flights:
        price = bundle.get("price")
        legs  = bundle.get("flights", [])
        if not legs:
            continue

        out   = legs[0]
        dep_t = parse_time(out.get("departure_airport", {}).get("time", ""))
        arr_t = parse_time(out.get("arrival_airport",   {}).get("time", ""))
        if dep_t:
            h = int(dep_t.split(":")[0])
            if out_min <= h < out_max:
                outbound.append({
                    "airline":   out.get("airline", ""),
                    "flight_no": out.get("flight_number", ""),
                    "dep": dep_t, "arr": arr_t,
                    "duration":  out.get("duration", ""),
                    "price": price, "stops": len(legs) - 1,
                })

        ret    = legs[-1]
        rdep_t = parse_time(ret.get("departure_airport", {}).get("time", ""))
        rarr_t = parse_time(ret.get("arrival_airport",   {}).get("time", ""))
        if rdep_t:
            rh = int(rdep_t.split(":")[0])
            if ret_min <= rh < ret_max:
                inbound.append({
                    "airline":   ret.get("airline", ""),
                    "flight_no": ret.get("flight_number", ""),
                    "dep": rdep_t, "arr": rarr_t,
                    "duration":  ret.get("duration", ""),
                    "price": price, "stops": len(legs) - 1,
                })

    outbound.sort(key=lambda x: x["price"] or 99999)
    inbound.sort( key=lambda x: x["price"] or 99999)

    # 3. Sonucu disk + memory cache'e yaz
    st.session_state.flight_cache[key] = {"outbound": outbound, "inbound": inbound}
    _save_disk_cache(st.session_state.flight_cache)

    return outbound, inbound, None

def render_flights(flights, emoji, route):
    if not flights:
        st.caption("Bu saatte uygun uçuş bulunamadı")
        return
    for i, f in enumerate(flights[:3]):
        stops = "✅ Direkt" if f["stops"] == 0 else f"🔄 {f['stops']} aktarma"
        dur   = duration_fmt(f["duration"])
        c1, c2, c3 = st.columns([4, 3, 2])
        with c1:
            st.markdown(f"**{emoji} {f['dep']} → {f['arr']}**")
            st.caption(f"{f['airline']} {f['flight_no']}  ·  {stops}" + (f"  ·  {dur}" if dur else ""))
        with c2:
            st.caption(route)
            if i == 0:
                st.caption("⭐ En iyi seçenek")
        with c3:
            st.metric("", fmt_price(f["price"]))
            st.caption("kişi başı")
        if i < min(len(flights), 3) - 1:
            st.markdown("---")

# ─── _render_card (tek destinasyon modu için) ─────────────────────────────────

def _render_card(idx, r, best):
    sat_lbl   = f"{r['sat'].day} {MONTH_SHORT[r['sat'].month]} Cumartesi"
    sun_lbl   = f"{r['sun'].day} {MONTH_SHORT[r['sun'].month]} Pazar"
    total_p   = r["total"]
    is_best   = best and total_p and total_p == best["total"]
    best_lbl  = " 🏆 EN UCUZ" if is_best else ""
    price_lbl = f"  —  💰 {fmt_price(total_p)}" if total_p else "  —  fiyat bulunamadı"

    with st.expander(
        f"**{idx}. Hafta Sonu** · {sat_lbl} → {sun_lbl}{price_lbl}{best_lbl}",
        expanded=is_best
    ):
        if total_p:
            pc1, pc2, pc3 = st.columns(3)
            pc1.metric("🛫 Gidiş (en ucuz)", fmt_price(r["min_out"]))
            pc2.metric("🛬 Dönüş (en ucuz)", fmt_price(r["min_ret"]))
            pc3.metric("💰 Toplam", fmt_price(total_p), "🏆 En ucuz!" if is_best else None)
            st.divider()

        st.markdown(f"**🔵 Gidiş** — {sat_lbl} · {out_min:02d}:00–{out_max:02d}:00")
        render_flights(r["outbound"], "🛫", f"SAW → {r['dest']}")
        st.markdown("---")
        st.markdown(f"**🔴 Dönüş** — {sun_lbl} · {ret_min:02d}:00–{ret_max:02d}:00")
        render_flights(r["inbound"], "🛬", f"{r['dest']} → SAW")
        st.markdown("---")
        st.link_button("🔗 Google Flights'ta Aç →",
                       build_gf_url(ORIGIN, r["dest"], r["sat"], r["sun"]),
                       use_container_width=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("✈️ Uçuş Arama")
    st.caption("SAW kalkışlı  |  1 Yetişkin  |  G/D")
    st.divider()

    api_key = st.text_input("🔑 SerpAPI Key", type="password",
                            value="87b048c8075d9073589095c316797222275f6dc4b7cfa6c686c770055e0c6900")

    st.divider()

    # ── MOD SEÇİMİ ──
    search_mode = st.radio(
        "🎯 Arama Modu",
        ["Tek Destinasyon", "Bölge Tara", "Tüm Dünya"],
        help="Tek: 1 havalimanı  |  Bölge: seçili bölgedeki tüm havalimanları  |  Tüm Dünya: hepsini tara"
    )

    st.divider()

    selected_airports = []

    if search_mode == "Tek Destinasyon":
        region_choice = st.selectbox("📍 Bölge", list(AIRPORT_REGIONS.keys()))
        airports_in_region = AIRPORT_REGIONS[region_choice]
        airport_labels = [f"{code} — {name}" for code, name in airports_in_region]
        selected_label = st.selectbox("✈️ Havalimanı", airport_labels)
        selected_airports = [selected_label.split(" — ")[0]]

    elif search_mode == "Bölge Tara":
        region_choice = st.selectbox("📍 Bölge", list(AIRPORT_REGIONS.keys()))
        airports_in_region = AIRPORT_REGIONS[region_choice]
        st.caption(f"{len(airports_in_region)} havalimanı taranacak")

        # İsteğe bağlı hariç tut
        exclude_labels = st.multiselect(
            "🚫 Hariç tut (opsiyonel)",
            [f"{c} — {n}" for c, n in airports_in_region]
        )
        excluded_codes = {l.split(" — ")[0] for l in exclude_labels}
        selected_airports = [c for c, _ in airports_in_region if c not in excluded_codes]
        st.info(f"**{len(selected_airports)}** havalimanı taranacak")

    else:  # Tüm Dünya
        all_list = [(c, n) for airports in AIRPORT_REGIONS.values() for c, n in airports]
        exclude_regions = st.multiselect("🚫 Hariç tut bölge", list(AIRPORT_REGIONS.keys()))
        excluded_region_codes = {c for r in exclude_regions for c, _ in AIRPORT_REGIONS[r]}
        selected_airports = [c for c, _ in all_list if c not in excluded_region_codes]
        st.warning(f"**{len(selected_airports)}** havalimanı — ~{len(selected_airports)} API sorgusu kullanılacak")

    st.divider()

    st.markdown("**📅 Ay Filtresi**")
    show = {
        4: st.checkbox("🌸 Nisan",   value=True),
        5: st.checkbox("🌿 Mayıs",   value=True),
        6: st.checkbox("☀️ Haziran", value=True),
    }

    st.divider()

    st.markdown("**⏰ Saat Penceresi**")
    col_a, col_b = st.columns(2)
    with col_a:
        out_min = st.number_input("Gidiş (min)", 0, 23, 9)
        ret_min = st.number_input("Dönüş (min)", 0, 23, 18)
    with col_b:
        out_max = st.number_input("Gidiş (max)", 0, 23, 15)
        ret_max = st.number_input("Dönüş (max)", 0, 23, 21)

    st.divider()
    st.caption(f"🛫 Gidiş: Cmt {out_min:02d}:00–{out_max:02d}:00\n🛬 Dönüş: Paz {ret_min:02d}:00–{ret_max:02d}:00")

    st.divider()
    cache_count = len(st.session_state.flight_cache)
    st.markdown("**💾 Önbellek**")
    st.caption(f"{cache_count} sorgu önbellekte")
    if cache_count > 0:
        if st.button("🗑 Önbelleği Temizle", use_container_width=True):
            st.session_state.flight_cache = {}
            _save_disk_cache({})
            st.rerun()

# ─── ANA SAYFA ────────────────────────────────────────────────────────────────

st.title("✈️ SAW Kalkışlı Hafta Sonu Uçuşları")
st.caption(f"İstanbul Sabiha Gökçen (SAW)  |  Nisan–Haziran 2026  |  Google Flights (SerpAPI)")

active_months = [m for m in MONTHS if show[m]]
saturdays = get_saturdays(active_months)
weekends  = [(s, s + timedelta(days=1)) for s in saturdays]

total_queries = len(weekends) * len(selected_airports)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Destinasyon", len(selected_airports))
c2.metric("Hafta Sonu",  len(weekends))
c3.metric("Toplam Sorgu", total_queries)
c4.metric("Tahmini Süre", f"~{total_queries * 0.8 / 60:.1f} dk")

if total_queries > 100:
    st.warning(f"⚠️ {total_queries} sorgu SerpAPI kotanı hızlı tüketir. Bölge filtresi veya ay filtresi kullanmayı düşün.")

search_btn = st.button("🔍 Uçuşları Ara", type="primary", use_container_width=True, disabled=not selected_airports)
st.divider()

# ─── ARAMA ────────────────────────────────────────────────────────────────────

if search_btn:
    if not api_key:
        st.error("SerpAPI key girin.")
        st.stop()
    if not selected_airports:
        st.error("En az bir destinasyon seçin.")
        st.stop()
    if not weekends:
        st.error("En az bir ay seçin.")
        st.stop()

    # Tüm kombinasyonlar: (destination, sat, sun)
    tasks = [(dest, sat, sun)
             for dest in selected_airports
             for sat, sun in weekends]

    all_results = []   # {dest, dest_name, sat, sun, outbound, inbound, total}
    bar   = st.progress(0, text="Başlıyor...")
    done  = 0
    api_calls  = 0
    cache_hits = 0

    for dest, sat, sun in tasks:
        dest_name = ALL_AIRPORTS.get(dest, dest)
        key = _cache_key(ORIGIN, dest, sat, sun, out_min, out_max, ret_min, ret_max)
        from_cache = key in st.session_state.flight_cache
        cache_hits += 1 if from_cache else 0
        api_calls  += 0 if from_cache else 1
        icon = "💾" if from_cache else "🔍"

        bar.progress(
            (done + 1) / len(tasks),
            text=f"{icon} SAW→{dest} · {sat.strftime('%d %b')} ({done+1}/{len(tasks)}) — 🔍 API: {api_calls}  💾 Önbellek: {cache_hits}"
        )

        out, ret, err = fetch_flights(
            api_key, ORIGIN, dest, sat, sun,
            out_min, out_max, ret_min, ret_max
        )

        if not err and (out or ret):
            min_out = out[0]["price"] if out else None
            min_ret = ret[0]["price"] if ret else None
            total_p = (min_out + min_ret) if (min_out and min_ret) else None
            all_results.append({
                "dest": dest, "dest_name": dest_name,
                "sat": sat, "sun": sun,
                "outbound": out, "inbound": ret,
                "total": total_p,
                "min_out": min_out, "min_ret": min_ret,
            })

        done += 1
        if not from_cache:
            time.sleep(0.6)  # Sadece gerçek API çağrısında bekle

    bar.empty()
    st.caption(f"✅ Tamamlandı — 🔍 {api_calls} API sorgusu · 💾 {cache_hits} önbellekten")

    if not all_results:
        st.error("Hiç uygun uçuş bulunamadı. Saat pencerelerini genişletmeyi dene.")
        st.stop()

    # Toplam fiyata göre sırala
    priced   = [r for r in all_results if r["total"]]
    unpriced = [r for r in all_results if not r["total"]]
    priced.sort(key=lambda x: x["total"])
    all_results = priced + unpriced

    st.success(f"✅ {done} sorgu tamamlandı — {len(priced)} kombinasyonda fiyat bulundu")

    # ─── EN UCUZ BANNER ───────────────────────────────────────────────────────

    if priced:
        best = priced[0]
        st.divider()
        st.markdown("## 🏆 En Ucuz Gidiş-Dönüş")
        bc1, bc2, bc3, bc4, bc5 = st.columns(5)
        bc1.metric("📍 Destinasyon", f"{best['dest']} — {best['dest_name']}")
        bc2.metric("📅 Tarih",
                   f"{best['sat'].day} {MONTH_SHORT[best['sat'].month]} – "
                   f"{best['sun'].day} {MONTH_SHORT[best['sun'].month]}")
        bc3.metric("🛫 Gidiş",  fmt_price(best["min_out"]))
        bc4.metric("🛬 Dönüş",  fmt_price(best["min_ret"]))
        bc5.metric("💰 Toplam", fmt_price(best["total"]))
        st.link_button(
            f"🔗 {best['dest']} — {fmt_price(best['total'])} — Google Flights'ta Aç",
            build_gf_url(ORIGIN, best["dest"], best["sat"], best["sun"]),
            use_container_width=True, type="primary"
        )
        st.divider()

        # ─── TOP 10 ÖZET TABLOSU ──────────────────────────────────────────────
        st.markdown("### 📊 En Ucuz 10 Kombinasyon")
        import pandas as pd
        top10 = priced[:10]
        df = pd.DataFrame([{
            "Destinasyon": f"{r['dest']} — {r['dest_name']}",
            "Tarih": f"{r['sat'].day} {MONTH_SHORT[r['sat'].month]} – {r['sun'].day} {MONTH_SHORT[r['sun'].month]}",
            "Gidiş": fmt_price(r["min_out"]),
            "Dönüş": fmt_price(r["min_ret"]),
            "Toplam": fmt_price(r["total"]),
        } for r in top10])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.divider()

    # ─── HARİTA ───────────────────────────────────────────────────────────────

    try:
        import folium
        from streamlit_folium import st_folium

        st.markdown("### 🗺 Fiyat Haritası")
        st.caption("Her pin bir destinasyon — renk ucuzdan pahalıya: 🟢 → 🟡 → 🔴. Tıklayınca detay görünür.")

        # Her destinasyon için en ucuz toplam fiyatı al
        dest_best = {}
        for r in priced:
            if r["dest"] not in dest_best or r["total"] < dest_best[r["dest"]]["total"]:
                dest_best[r["dest"]] = r

        prices = [v["total"] for v in dest_best.values()]
        min_p, max_p = min(prices), max(prices)

        def price_color(p):
            if max_p == min_p:
                return "green"
            ratio = (p - min_p) / (max_p - min_p)
            if ratio < 0.33:   return "green"
            elif ratio < 0.66: return "orange"
            else:              return "red"

        def price_icon(p):
            if max_p == min_p:
                return "star"
            ratio = (p - min_p) / (max_p - min_p)
            if ratio < 0.33:   return "star"
            elif ratio < 0.66: return "info-sign"
            else:              return "remove"

        m = folium.Map(
            location=[41.0, 20.0],
            zoom_start=4,
            tiles="CartoDB dark_matter",
        )

        # SAW pin
        folium.Marker(
            location=[40.8986, 29.3092],
            popup=folium.Popup("<b>SAW</b><br>İstanbul Sabiha Gökçen<br>Kalkış noktası", max_width=200),
            tooltip="✈ SAW — Kalkış",
            icon=folium.Icon(color="blue", icon="plane", prefix="fa"),
        ).add_to(m)

        for dest, r in dest_best.items():
            coords = AIRPORT_COORDS.get(dest)
            if not coords:
                continue
            color = price_color(r["total"])
            icon  = price_icon(r["total"])
            sat_lbl = f"{r['sat'].day} {MONTH_SHORT[r['sat'].month]}"
            sun_lbl = f"{r['sun'].day} {MONTH_SHORT[r['sun'].month]}"
            gf_url  = build_gf_url(ORIGIN, dest, r["sat"], r["sun"])
            out_f   = r["outbound"][0] if r["outbound"] else None
            ret_f   = r["inbound"][0]  if r["inbound"]  else None

            popup_html = f"""
            <div style="font-family:sans-serif;min-width:200px">
              <b style="font-size:1.1em">{dest} — {r['dest_name']}</b><br>
              <hr style="margin:4px 0">
              📅 <b>{sat_lbl} → {sun_lbl}</b><br>
              🛫 Gidiş: <b>{fmt_price(r['min_out'])}</b>
              {"  " + out_f['dep'] + "→" + out_f['arr'] + "  " + out_f['airline'] if out_f else ""}<br>
              🛬 Dönüş: <b>{fmt_price(r['min_ret'])}</b>
              {"  " + ret_f['dep'] + "→" + ret_f['arr'] + "  " + ret_f['airline'] if ret_f else ""}<br>
              <hr style="margin:4px 0">
              💰 <b style="font-size:1.2em">{fmt_price(r['total'])}</b> toplam<br>
              <a href="{gf_url}" target="_blank">🔗 Google Flights'ta Aç</a>
            </div>"""

            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"{dest} — {fmt_price(r['total'])}",
                icon=folium.Icon(color=color, icon=icon, prefix="glyphicon"),
            ).add_to(m)

            # SAW'dan çizgi
            folium.PolyLine(
                locations=[[40.8986, 29.3092], coords],
                color={"green": "#43c98a", "orange": "#e8a045", "red": "#e05c5c"}[color],
                weight=1.2,
                opacity=0.5,
            ).add_to(m)

        st_folium(m, use_container_width=True, height=520, returned_objects=[])
        st.divider()

    except ImportError:
        st.info("💡 Harita için: `pip install folium streamlit-folium` ve requirements.txt'e ekle.")

    # ─── TÜM KARTLAR ──────────────────────────────────────────────────────────

    st.markdown("### 🗂 Tüm Sonuçlar")

    # Destinasyona göre grupla
    if search_mode == "Tek Destinasyon":
        # Hafta sonlarına göre göster
        current_month = None
        card_idx = 0
        for r in all_results:
            if r["sat"].month != current_month:
                current_month = r["sat"].month
                st.header(MONTH_NAMES[current_month])
            card_idx += 1
            _render_card(card_idx, r, priced[0] if priced else None)
    else:
        # Destinasyona göre grupla, toplam fiyata göre sıralı
        dest_groups = {}
        for r in all_results:
            dest_groups.setdefault(r["dest"], []).append(r)

        for dest, rows in dest_groups.items():
            dest_name = ALL_AIRPORTS.get(dest, dest)
            min_total = min((r["total"] for r in rows if r["total"]), default=None)
            with st.expander(
                f"**{dest}** — {dest_name}  ·  "
                + (f"En ucuz: {fmt_price(min_total)}" if min_total else "fiyat yok"),
                expanded=(dest == priced[0]["dest"] if priced else False)
            ):
                for r in rows:
                    sat_lbl = f"{r['sat'].day} {MONTH_SHORT[r['sat'].month]} Cmt"
                    sun_lbl = f"{r['sun'].day} {MONTH_SHORT[r['sun'].month]} Paz"
                    total_p = r["total"]
                    is_best = priced and total_p == priced[0]["total"]
                    best_lbl = " 🏆 EN UCUZ" if is_best else ""
                    price_lbl = f"  —  💰 {fmt_price(total_p)}" if total_p else "  —  fiyat bulunamadı"

                    with st.expander(
                        f"{sat_lbl} → {sun_lbl}{price_lbl}{best_lbl}",
                        expanded=is_best
                    ):
                        if total_p:
                            pc1, pc2, pc3 = st.columns(3)
                            pc1.metric("🛫 Gidiş", fmt_price(r["min_out"]))
                            pc2.metric("🛬 Dönüş", fmt_price(r["min_ret"]))
                            pc3.metric("💰 Toplam", fmt_price(total_p),
                                       "🏆 En ucuz!" if is_best else None)
                            st.divider()

                        st.markdown(f"**🔵 Gidiş** — Cumartesi {sat_lbl} · {out_min:02d}:00–{out_max:02d}:00 · SAW→{dest}")
                        render_flights(r["outbound"], "🛫", f"SAW → {dest}")
                        st.markdown("---")
                        st.markdown(f"**🔴 Dönüş** — Pazar {sun_lbl} · {ret_min:02d}:00–{ret_max:02d}:00 · {dest}→SAW")
                        render_flights(r["inbound"], "🛬", f"{dest} → SAW")
                        st.markdown("---")
                        st.link_button(
                            "🔗 Google Flights'ta Aç →",
                            build_gf_url(ORIGIN, dest, r["sat"], r["sun"]),
                            use_container_width=True
                        )

else:
    st.info("👈 Sol menüden arama modunu ve destinasyonları seç, ardından **Uçuşları Ara** butonuna bas.")
