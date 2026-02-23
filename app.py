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

    # ─── EN UCUZ GIT-GEL ──────────────────────────────────────────────────────

    month_tr = ["","Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"]

    best_weekend = None
    best_total   = None
    best_sat     = None
    best_sun     = None

    for sat, sun in weekends:
        out, ret = results[(sat, sun)]
        min_out  = out[0]["price"] if out else None
        min_ret  = ret[0]["price"] if ret else None
        if min_out and min_ret:
            total_price = min_out + min_ret
            if best_total is None or total_price < best_total:
                best_total   = total_price
                best_sat     = sat
                best_sun     = sun
                best_out_f   = out[0]
                best_ret_f   = ret[0]

    if best_weekend is not None or best_total is not None:
        st.divider()
        st.markdown("## 🏆 En Ucuz Gidiş-Dönüş")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(
                "📅 Tarih",
                f"{best_sat.day} {month_tr[best_sat.month]} – {best_sun.day} {month_tr[best_sun.month]}"
            )
        with c2:
            st.metric("🛫 Gidiş", fmt_price(best_out_f["price"]),
                      f"{best_out_f['dep']} → {best_out_f['arr']}  ·  {best_out_f['airline']}")
        with c3:
            st.metric("🛬 Dönüş", fmt_price(best_ret_f["price"]),
                      f"{best_ret_f['dep']} → {best_ret_f['arr']}  ·  {best_ret_f['airline']}")
        with c4:
            st.metric("💰 Toplam", fmt_price(best_total), "kişi başı gidiş-dönüş")

        st.link_button(
            f"🔗 Bu tarihi Google Flights'ta Aç — {fmt_price(best_total)}",
            build_gf_url(best_sat, best_sun),
            use_container_width=True,
            type="primary",
        )
        st.divider()

    # ─── SONUÇLAR ─────────────────────────────────────────────────────────────

    current_month = None
    card_idx = 0

    for sat, sun in weekends:
        if sat.month != current_month:
            current_month = sat.month
            st.header(MONTH_NAMES[sat.month])

        card_idx += 1
        out, ret = results[(sat, sun)]
        gf_url   = build_gf_url(sat, sun)

        sat_lbl = f"{sat.day} {month_tr[sat.month]} Cumartesi"
        sun_lbl = f"{sun.day} {month_tr[sun.month]} Pazar"

        min_out     = out[0]["price"] if out else None
        min_ret     = ret[0]["price"] if ret else None
        total_price = (min_out + min_ret) if (min_out and min_ret) else None

        # Expander başlığında fiyat
        is_best    = (best_total is not None and total_price == best_total)
        best_label = " 🏆 EN UCUZ" if is_best else ""
        price_label = f"  —  💰 {fmt_price(total_price)}" if total_price else "  —  fiyat bulunamadı"
        expander_title = f"**{card_idx}. Hafta Sonu** · {sat_lbl} → {sun_lbl}{price_label}{best_label}"

        with st.expander(expander_title, expanded=is_best):

            # Kart içi fiyat özeti
            if total_price:
                pc1, pc2, pc3 = st.columns(3)
                with pc1:
                    st.metric("🛫 Gidiş (en ucuz)", fmt_price(min_out))
                with pc2:
                    st.metric("🛬 Dönüş (en ucuz)", fmt_price(min_ret))
                with pc3:
                    st.metric("💰 Toplam", fmt_price(total_price),
                              "🏆 En ucuz hafta sonu!" if is_best else None)
                st.divider()

            st.markdown(f"#### 🔵 Gidiş &nbsp; `{sat_lbl}` &nbsp; 09:00 – 15:00")
            render_flights(out, "🛫", "SAW → ECN")

            st.markdown("---")

            st.markdown(f"#### 🔴 Dönüş &nbsp; `{sun_lbl}` &nbsp; 18:00 – 21:00")
            render_flights(ret, "🛬", "ECN → SAW")

            st.markdown("---")
            st.link_button("🔗 Google Flights'ta Aç →", gf_url, use_container_width=True)

else:
    st.info("👈 Sol menüden ayarlarını yap, ardından **Uçuşları Ara** butonuna bas.")
