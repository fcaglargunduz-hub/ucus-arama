import streamlit as st
import requests
import base64
import time
from datetime import date, timedelta

# ─── SAYFA AYARLARI ───────────────────────────────────────────────────────────

st.set_page_config(
    page_title="SAW → ECN Uçuş Arama",
    page_icon="✈",
    layout="wide",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.main { background: #f5f2eb; }

.route-header {
    background: #0f0e0c; color: #f5f2eb;
    padding: 12px 24px; border-radius: 4px;
    font-family: 'DM Mono', monospace; font-size: 0.75rem;
    letter-spacing: 0.08em; margin-bottom: 8px;
    display: flex; gap: 20px; align-items: center;
}
.route-header span { color: #c84b2f; font-weight: 600; }

.big-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.4rem; line-height: 1.1;
    letter-spacing: -0.03em; margin-bottom: 6px;
}
.big-title em { color: #c84b2f; font-style: italic; }

.weekend-card {
    background: white; border: 1px solid #ddd8ce;
    border-radius: 6px; margin-bottom: 14px;
    overflow: hidden;
}
.card-header {
    background: #fafaf8; border-bottom: 1px solid #ddd8ce;
    padding: 10px 16px; display: flex;
    justify-content: space-between; align-items: center;
}
.card-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1rem; color: #8a8578;
}
.card-dates {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem; font-weight: 600;
    color: #0f0e0c; letter-spacing: 0.04em;
}
.total-badge {
    background: #e8f5eb; color: #2d7a3a;
    padding: 3px 10px; border-radius: 3px;
    font-family: 'DM Mono', monospace; font-size: 0.65rem;
    border: 1px solid #c3e0c8; letter-spacing: 0.04em;
}
.flight-row {
    padding: 12px 16px; border-bottom: 1px solid #f0ede6;
    display: flex; align-items: center; gap: 12px;
}
.flight-row:last-child { border-bottom: none; }
.flight-row.best { background: #fdfdf8; }
.day-tag {
    font-family: 'DM Mono', monospace; font-size: 0.58rem;
    letter-spacing: 0.1em; text-transform: uppercase;
    padding: 3px 7px; border-radius: 2px;
    min-width: 32px; text-align: center; flex-shrink: 0;
}
.day-tag.sat { background: #1a3a5c; color: white; }
.day-tag.sun { background: #7a1c1c; color: white; }
.flight-times {
    font-family: 'DM Mono', monospace;
    font-size: 0.9rem; font-weight: 500;
}
.flight-meta { font-size: 0.68rem; color: #8a8578; margin-top: 2px; }
.price-val {
    font-family: 'DM Serif Display', serif;
    font-size: 1.15rem; color: #c84b2f;
    margin-left: auto; white-space: nowrap;
}
.price-sub {
    font-family: 'DM Mono', monospace; font-size: 0.58rem;
    color: #8a8578; text-align: right;
}
.no-flight {
    padding: 12px 16px; border-bottom: 1px solid #f0ede6;
    display: flex; align-items: center; gap: 12px;
    color: #ccc; font-family: 'DM Mono', monospace;
    font-size: 0.68rem; font-style: italic;
}
.gf-btn {
    display: inline-block; margin-left: auto;
    font-family: 'DM Mono', monospace; font-size: 0.62rem;
    letter-spacing: 0.06em; padding: 4px 10px;
    border: 1px solid #ddd8ce; border-radius: 2px;
    color: #0f0e0c; text-decoration: none;
    background: #f5f2eb;
}
.month-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.5rem; margin-top: 32px; margin-bottom: 12px;
    padding-bottom: 8px; border-bottom: 1px solid #ddd8ce;
    letter-spacing: -0.02em;
}
.month-tag {
    font-family: 'DM Mono', monospace; font-size: 0.62rem;
    color: #8a8578; letter-spacing: 0.1em; margin-left: 8px;
}
.stat-box {
    background: white; border: 1px solid #ddd8ce;
    border-radius: 4px; padding: 14px 20px; text-align: center;
}
.stat-num {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem; color: #c84b2f; line-height: 1;
}
.stat-lbl {
    font-family: 'DM Mono', monospace; font-size: 0.62rem;
    color: #8a8578; letter-spacing: 0.08em; text-transform: uppercase;
}
.legend-row {
    display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap;
}
.legend-item {
    display: flex; align-items: center; gap: 7px;
    font-family: 'DM Mono', monospace; font-size: 0.68rem; color: #8a8578;
}
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.dot-sat { background: #1a3a5c; }
.dot-sun { background: #7a1c1c; }
</style>
""", unsafe_allow_html=True)

# ─── AYARLAR ──────────────────────────────────────────────────────────────────

ORIGIN      = "SAW"
DESTINATION = "ECN"
YEAR        = 2026
MONTHS      = [4, 5, 6]
MONTH_NAMES = {4: "Nisan", 5: "Mayıs", 6: "Haziran"}
MONTH_TAGS  = {4: "APR", 5: "MAY", 6: "JUN"}

OUTBOUND_MIN, OUTBOUND_MAX = 9, 15
RETURN_MIN,   RETURN_MAX   = 18, 21

# ─── YARDIMCI FONKSİYONLAR ───────────────────────────────────────────────────

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

        # Gidiş
        out = legs[0]
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

        # Dönüş
        ret = legs[-1]
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

# ─── HTML PARÇALARI ───────────────────────────────────────────────────────────

def flight_rows_html(flights, day_label, day_class):
    if not flights:
        return f"""
        <div class="no-flight">
          <span class="day-tag {day_class}">{day_label}</span>
          Bu saatte uygun uçuş bulunamadı
        </div>"""
    rows = []
    for i, f in enumerate(flights[:3]):
        cls = "flight-row best" if i == 0 else "flight-row"
        stops = "Direkt" if f["stops"] == 0 else f"{f['stops']} aktarma"
        dur   = duration_fmt(f["duration"])
        meta  = f"{f['airline']} {f['flight_no']} · {stops}" + (f" · {dur}" if dur else "")
        rows.append(f"""
        <div class="{cls}">
          <span class="day-tag {day_class}">{day_label}</span>
          <div style="flex:1">
            <div class="flight-times">{f['dep']} → {f['arr']}</div>
            <div class="flight-meta">{meta}</div>
          </div>
          <div>
            <div class="price-val">{fmt_price(f['price'])}</div>
            <div class="price-sub">kişi başı</div>
          </div>
        </div>""")
    return "\n".join(rows)

def render_card(idx, sat, sun, outbound, inbound):
    month_tr = ["","Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"]
    sat_lbl = f"{sat.day} {month_tr[sat.month]}"
    sun_lbl = f"{sun.day} {month_tr[sun.month]}"

    min_out = outbound[0]["price"] if outbound else None
    min_ret = inbound[0]["price"]  if inbound  else None
    badge   = f'<span class="total-badge">Toplam ~{fmt_price(min_out + min_ret)}</span>' \
              if min_out and min_ret else ""

    gf_url    = build_gf_url(sat, sun)
    out_rows  = flight_rows_html(outbound, "CTS", "sat")
    ret_rows  = flight_rows_html(inbound,  "PAZ", "sun")

    return f"""
    <div class="weekend-card">
      <div class="card-header">
        <div style="display:flex;align-items:center;gap:12px">
          <span class="card-title">{idx}. Hafta Sonu</span>
          <span class="card-dates">{sat_lbl} → {sun_lbl}</span>
        </div>
        <div style="display:flex;align-items:center;gap:10px">
          {badge}
          <a class="gf-btn" href="{gf_url}" target="_blank">Google Flights ↗</a>
        </div>
      </div>
      {out_rows}
      {ret_rows}
    </div>"""

# ─── ARAYÜZ ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class="route-header">
  <span>SAW</span> İstanbul Sabiha Gökçen &nbsp;→&nbsp; <span>ECN</span> Ercan, KKTC
  &nbsp;|&nbsp; <span>1</span> Yetişkin, Gidiş-Dönüş
  &nbsp;|&nbsp; <span>NİSAN – HAZİRAN 2026</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">İstanbul\'dan <em>Kıbrıs\'a</em><br>hafta sonu uçuşları</div>', unsafe_allow_html=True)

st.markdown("""
<div class="legend-row">
  <div class="legend-item"><span class="dot dot-sat"></span> GİDİŞ — Cumartesi 09:00–15:00</div>
  <div class="legend-item"><span class="dot dot-sun"></span> DÖNÜŞ — Pazar 18:00–21:00</div>
</div>
""", unsafe_allow_html=True)

# API Key girişi — sidebar
with st.sidebar:
    st.markdown("### ⚙️ Ayarlar")
    api_key = st.text_input(
        "SerpAPI Key",
        value="87b048c8075d9073589095c316797222275f6dc4b7cfa6c686c770055e0c6900",
        type="password",
        help="serpapi.com adresinden alabilirsiniz"
    )
    st.markdown("---")
    st.markdown("**Filtrele:**")
    show_april = st.checkbox("Nisan", value=True)
    show_may   = st.checkbox("Mayıs", value=True)
    show_june  = st.checkbox("Haziran", value=True)
    st.markdown("---")
    st.caption("Veri: Google Flights (SerpAPI)\nFiyatlar anlık değişebilir.")

# Ara butonu
col1, col2 = st.columns([2, 1])
with col1:
    search_btn = st.button("✈ Uçuşları Ara", type="primary", use_container_width=True)

saturdays = get_saturdays()
weekends  = [(s, s + timedelta(days=1)) for s in saturdays]

# Filtrele
month_filter = {4: show_april, 5: show_may, 6: show_june}
weekends_filtered = [w for w in weekends if month_filter[w[0].month]]

with col2:
    st.markdown(f"""
    <div class="stat-box">
      <div class="stat-num">{len(weekends_filtered)}</div>
      <div class="stat-lbl">Hafta Sonu</div>
    </div>""", unsafe_allow_html=True)

# ─── ARAMA ────────────────────────────────────────────────────────────────────

if search_btn:
    if not api_key:
        st.error("Lütfen SerpAPI key girin.")
        st.stop()

    results = {}  # (sat, sun) -> (outbound, inbound)

    progress = st.progress(0, text="Uçuşlar aranıyor...")
    status   = st.empty()

    for i, (sat, sun) in enumerate(weekends_filtered):
        status.markdown(f"**{i+1}/{len(weekends_filtered)}** — {sat.strftime('%d %B')} sorgulanıyor...")
        outbound, inbound, err = fetch_flights(api_key, sat, sun)
        if err:
            st.warning(f"{sat}: {err}")
        results[(sat, sun)] = (outbound, inbound)
        progress.progress((i + 1) / len(weekends_filtered),
                          text=f"{i+1}/{len(weekends_filtered)} tamamlandı")
        time.sleep(0.6)

    progress.empty()
    status.empty()

    # ─── SONUÇLARI GÖSTER ─────────────────────────────────────────────────────

    total_flights = sum(len(o) + len(r) for o, r in results.values())
    st.success(f"✓ {len(weekends_filtered)} hafta sonu tarandı — {total_flights} uygun uçuş bulundu")

    current_month = None
    card_idx = 0

    for sat, sun in weekends_filtered:
        # Ay başlığı
        if sat.month != current_month:
            current_month = sat.month
            st.markdown(
                f'<div class="month-title">{MONTH_NAMES[sat.month]} 2026'
                f'<span class="month-tag">{MONTH_TAGS[sat.month]} 2026</span></div>',
                unsafe_allow_html=True
            )

        card_idx += 1
        outbound, inbound = results[(sat, sun)]
        st.markdown(render_card(card_idx, sat, sun, outbound, inbound), unsafe_allow_html=True)

elif not search_btn:
    st.info("👈 Sidebar'dan filtreni seç, ardından **Uçuşları Ara** butonuna bas.")
