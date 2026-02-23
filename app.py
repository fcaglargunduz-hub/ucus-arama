import streamlit as st
import requests
import base64
import time
from datetime import date, timedelta

st.set_page_config(
    page_title="SAW → ECN Uçuş Arama",
    page_icon="✈️",
    layout="wide",
)

# ─── AYARLAR ──────────────────────────────────────────────────────────────────

ORIGIN      = "SAW"
DESTINATION = "ECN"
YEAR        = 2026
MONTHS      = [4, 5, 6]
MONTH_NAMES = {4: "🌸 Nisan 2026", 5: "🌿 Mayıs 2026", 6: "☀️ Haziran 2026"}

OUTBOUND_MIN, OUTBOUND_MAX = 9, 15
RETURN_MIN,   RETURN_MAX   = 18, 21

# ─── YARDIMCI ─────────────────────────────────────────────────────────────────

def get_saturdays():
    saturdays = []
    for month in MONTHS:
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

def build_gf_url(dep_date, ret_date):
    def ap(code):
        return b'\x07\x08\x01\x12\x03' + code.encode()
    def leg(fr, to, d):
        body = b'\x12\x0a' + d.encode() + b'\x6a' + ap(fr) + b'\x72' + ap(to)
        return b'\x1a' + bytes([len(body)]) + body
    raw = (b'\x08\x1c\x10\x02'
           + leg(ORIGIN, DESTINATION, dep_date.isoformat())
           + leg(DESTINATION, ORIGIN, ret_date.isoformat())
           + b'\x42\x01\x01\x48\x01\x70\x01\x98\x01\x01\xc8\x01\x01')
    tfs = base64.b64encode(raw).decode()
    return f"https://www.google.com/travel/flights/search?tfs={tfs}&curr=TRY&hl=tr"

def fetch_flights(api_key, dep_date, ret_date):
    params = {
        "engine":        "google_flights",
        "departure_id":  ORIGIN,
        "arrival_id":    DESTINATION,
        "outbound_date": dep_date.isoformat(),
        "return_date":   ret_date.isoformat(),
        "adults":        1,
        "currency":      "TRY",
        "hl":            "tr",
        "type":          "1",
        "api_key":       api_key,
    }
    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=30)
        data = resp.json()
    except Exception as e:
        return [], [], str(e)

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
            if OUTBOUND_MIN <= h < OUTBOUND_MAX:
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
            if RETURN_MIN <= rh < RETURN_MAX:
                inbound.append({
                    "airline":   ret.get("airline", ""),
                    "flight_no": ret.get("flight_number", ""),
                    "dep": rdep_t, "arr": rarr_t,
                    "duration":  ret.get("duration", ""),
                    "price": price, "stops": len(legs) - 1,
                })

    outbound.sort(key=lambda x: x["price"] or 99999)
    inbound.sort( key=lambda x: x["price"] or 99999)
    return outbound, inbound, None

def render_flights(flights, direction_emoji, route_label):
    if not flights:
        st.caption(f"Bu saatte uygun uçuş bulunamadı")
        return

    for i, f in enumerate(flights[:3]):
        stops = "✅ Direkt" if f["stops"] == 0 else f"🔄 {f['stops']} aktarma"
        dur   = duration_fmt(f["duration"])
        price = fmt_price(f["price"])

        c1, c2, c3 = st.columns([4, 3, 2])
        with c1:
            st.markdown(f"### {direction_emoji} {f['dep']} → {f['arr']}")
            st.caption(f"{f['airline']} {f['flight_no']}  ·  {stops}" + (f"  ·  {dur}" if dur else ""))
        with c2:
            st.caption(route_label)
            if i == 0:
                st.caption("⭐ En iyi seçenek")
        with c3:
            st.metric(label="Fiyat", value=price, label_visibility="collapsed")
            st.caption("kişi başı")

        if i < min(len(flights), 3) - 1:
            st.markdown("---")

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("✈️ Uçuş Arama")
    st.caption("SAW → ECN  |  1 Yetişkin  |  G/D")
    st.divider()

    api_key = st.text_input(
        "🔑 SerpAPI Key",
        value="87b048c8075d9073589095c316797222275f6dc4b7cfa6c686c770055e0c6900",
        type="password",
    )

    st.divider()
    st.markdown("**📅 Ay Filtresi**")
    show = {
        4: st.checkbox("🌸 Nisan",   value=True),
        5: st.checkbox("🌿 Mayıs",   value=True),
        6: st.checkbox("☀️ Haziran", value=True),
    }

    st.divider()
    st.info("🛫 Gidiş: Cumartesi 09:00–15:00\n\n🛬 Dönüş: Pazar 18:00–21:00")
    st.caption("Fiyatlar anlık değişebilir.")

# ─── ANA SAYFA ────────────────────────────────────────────────────────────────

st.title("✈️ İstanbul → Kıbrıs")
st.subheader("Hafta Sonu Uçuş Arama — Nisan–Haziran 2026")
st.caption("Sabiha Gökçen (SAW) → Ercan (ECN)  |  Google Flights verisi (SerpAPI)")

saturdays = get_saturdays()
weekends  = [(s, s + timedelta(days=1)) for s in saturdays if show[s.month]]

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    search_btn = st.button("🔍 Uçuşları Ara", type="primary", use_container_width=True)
with col2:
    st.metric("Hafta Sonu", len(weekends))
with col3:
    st.metric("API Sorgusu", len(weekends))

st.divider()

# ─── ARAMA ────────────────────────────────────────────────────────────────────

if search_btn:
    if not api_key:
        st.error("Lütfen SerpAPI key girin.")
        st.stop()

    if not weekends:
        st.warning("En az bir ay seçin.")
        st.stop()

    results = {}
    bar = st.progress(0, text="Arama başlıyor...")

    for i, (sat, sun) in enumerate(weekends):
        bar.progress(
            (i + 1) / len(weekends),
            text=f"🔍 {sat.strftime('%d %B')} sorgulanıyor... ({i+1}/{len(weekends)})"
        )
        out, ret, err = fetch_flights(api_key, sat, sun)
        if err:
            st.warning(f"⚠️ {sat}: {err}")
        results[(sat, sun)] = (out, ret)
        time.sleep(0.6)

    bar.empty()

    total = sum(len(o) + len(r) for o, r in results.values())
    st.success(f"✅ {len(weekends)} hafta sonu tarandı — {total} uygun uçuş bulundu")

    # ─── SONUÇLAR ─────────────────────────────────────────────────────────────

    current_month = None
    card_idx = 0
    month_tr = ["","Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"]

    for sat, sun in weekends:
        if sat.month != current_month:
            current_month = sat.month
            st.header(MONTH_NAMES[sat.month])

        card_idx += 1
        out, ret = results[(sat, sun)]
        gf_url   = build_gf_url(sat, sun)

        sat_lbl = f"{sat.day} {month_tr[sat.month]} Cumartesi"
        sun_lbl = f"{sun.day} {month_tr[sun.month]} Pazar"

        min_out = out[0]["price"] if out else None
        min_ret = ret[0]["price"] if ret else None
        total_txt = f"  —  Toplam ~{fmt_price(min_out + min_ret)}" if min_out and min_ret else ""

        with st.expander(f"**{card_idx}. Hafta Sonu** · {sat_lbl} → {sun_lbl}{total_txt}", expanded=True):

            st.markdown(f"#### 🔵 Gidiş &nbsp; `{sat_lbl}` &nbsp; 09:00 – 15:00")
            render_flights(out, "🛫", "SAW → ECN")

            st.markdown("---")

            st.markdown(f"#### 🔴 Dönüş &nbsp; `{sun_lbl}` &nbsp; 18:00 – 21:00")
            render_flights(ret, "🛬", "ECN → SAW")

            st.markdown("---")
            st.link_button("🔗 Google Flights'ta Aç →", gf_url, use_container_width=True)

else:
    st.info("👈 Sol menüden ayarlarını yap, ardından **Uçuşları Ara** butonuna bas.")
