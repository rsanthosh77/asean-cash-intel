import streamlit as st
import anthropic
import json
from pinecone import Pinecone
from dotenv import load_dotenv
import os
import time
import glob
from datetime import datetime, timedelta

load_dotenv()

anthropic_client = anthropic.Anthropic()
pinecone_client  = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

ASEAN_COUNTRIES = {
    "Singapore","Indonesia","Malaysia","Thailand",
    "Philippines","Vietnam","Myanmar","Cambodia","Laos","Brunei"
}
ASEAN_ALL   = ASEAN_COUNTRIES | {"ASEAN-Wide"}
GEO_OPTIONS = ["ASEAN-Wide","Singapore","Indonesia","Malaysia","Thailand",
               "Philippines","Vietnam","Myanmar","Cambodia","Laos","Brunei"]
PAGE_SIZE   = 10

st.set_page_config(
    page_title="MANTIS — ASEAN Cash Intelligence",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed"   # collapsed = no arrow shown
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=IBM+Plex+Mono:wght@300;400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

/* ── Reset ── */
* { box-sizing: border-box; }
:root {
    --bg:#08090e; --sf:#0f1218; --sf2:#161b26; --sf3:#1c2332;
    --bd:#1e2a3a; --bd2:#253348;
    --teal:#00c2a8; --blue:#2563eb; --ora:#f59e0b;
    --pur:#8b5cf6;  --red:#ef4444;
    --tx:#f1f5f9;   --dim:#94a3b8; --mu:#475569;
}
.stApp { background: var(--bg) !important; }
.stApp > header { display: none !important; }

/* Hide sidebar and its arrow completely — we use columns instead */
section[data-testid="stSidebar"]    { display: none !important; }
[data-testid="collapsedControl"]    { display: none !important; }

/* Remove Streamlit's default top padding */
.block-container {
    padding-top: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-bottom: 1rem !important;
    max-width: 100% !important;
}

/* ── Our custom sidebar panel ── */
.cust-sidebar {
    background: var(--sf);
    border-right: 1px solid var(--bd);
    min-height: 100vh;
    padding: 0;
}
.sb-head {
    background: var(--sf2);
    border-bottom: 1px solid var(--bd);
    padding: 14px 16px 12px;
}
.sb-badge {
    display: inline-block;
    background: var(--teal); color: #000;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 8px; font-weight: 700;
    letter-spacing: .2em; padding: 3px 7px;
    border-radius: 2px; text-transform: uppercase;
    margin-bottom: 7px;
}
.sb-title {
    font-family: 'Playfair Display', serif;
    font-size: 15px; font-weight: 700; color: var(--tx); margin: 0 0 2px;
}
.sb-title em { color: var(--teal); font-style: normal; }
.sb-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 7.5px; color: var(--mu);
    letter-spacing: .1em; text-transform: uppercase;
}
.sb-status {
    display: flex; align-items: center; gap: 7px;
    padding: 7px 16px; border-bottom: 1px solid var(--bd);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 8.5px; letter-spacing: .06em;
}
.sb-status.ok    { color: var(--teal); }
.sb-status.stale { color: var(--red);  }
.dot { width:5px; height:5px; border-radius:50%; flex-shrink:0; }
.dot.ok    { background: var(--teal); }
.dot.stale { background: var(--red); }
.sb-src {
    padding: 10px 16px 14px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 8.5px; color: var(--mu); line-height: 2;
}
.sb-src-hdr {
    font-size: 7.5px; letter-spacing: .13em;
    text-transform: uppercase; margin-bottom: 4px; display: block;
}

/* Filter labels */
.f-lbl {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 7.5px; letter-spacing: .14em;
    color: var(--mu); text-transform: uppercase;
    display: block; margin: 8px 0 3px;
}

/* Multiselect */
.stMultiSelect [data-baseweb="select"] > div {
    background: var(--sf2) !important;
    border: 1px solid var(--bd2) !important;
    border-radius: 5px !important; min-height: 32px !important;
}
.stMultiSelect [data-baseweb="select"] > div:focus-within {
    border-color: rgba(0,194,168,.5) !important;
    box-shadow: 0 0 0 2px rgba(0,194,168,.07) !important;
}
.stMultiSelect [data-baseweb="tag"] {
    background: rgba(0,194,168,.12) !important;
    border: 1px solid rgba(0,194,168,.25) !important;
    color: var(--teal) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 8px !important; border-radius: 3px !important;
}
.stMultiSelect [data-baseweb="tag"] span { color: var(--teal) !important; }
[data-baseweb="popover"] { background: var(--sf2) !important; border: 1px solid var(--bd2) !important; }
[data-baseweb="menu"] li { color: var(--dim) !important; font-family: 'IBM Plex Mono',monospace !important; font-size: 10px !important; }
[data-baseweb="menu"] li:hover { background: var(--sf3) !important; }
.stMultiSelect input { color: var(--dim) !important; font-size: 10px !important; }
div[data-baseweb="select"] span { color: var(--mu) !important; font-family: 'IBM Plex Mono',monospace !important; font-size: 9px !important; }
/* Style native Streamlit widget labels in our custom sidebar column */
[data-testid="stVerticalBlock"] .stMultiSelect label p,
[data-testid="stVerticalBlock"] .stSlider label p,
[data-testid="stVerticalBlock"] .stWidgetLabel p {
    font-family: "IBM Plex Mono", monospace !important;
    font-size: 8px !important;
    letter-spacing: 0.14em !important;
    color: #475569 !important;
    text-transform: uppercase !important;
    font-weight: 400 !important;
    margin-bottom: 2px !important;
}

/* Slider */
.stSlider > div > div > div > div { background: var(--teal) !important; }
.stSlider > div > div > div { background: var(--sf3) !important; }
.stSlider { padding: 0 !important; }

/* ── Main area ── */
.main-hdr {
    background: var(--sf2); border-bottom: 1px solid var(--bd);
    padding: 14px 20px 12px; margin-bottom: 16px;
}
.main-title {
    font-family: 'Playfair Display', serif;
    font-size: 20px; font-weight: 700; color: var(--tx);
    letter-spacing: -.02em; margin: 0;
}
.main-title em { color: var(--teal); font-style: normal; }
.main-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 8.5px; color: var(--mu);
    letter-spacing: .1em; text-transform: uppercase; margin-top: 3px;
}

/* ── Metric cards ── */
.mcard { background: var(--sf); border: 1px solid var(--bd); border-radius: 8px; padding: 13px 15px; position: relative; overflow: hidden; }
.mcard::after { content:''; position:absolute; top:0;left:0;right:0; height:2px; }
.mcard.teal::after   { background:var(--teal); }
.mcard.blue::after   { background:var(--blue); }
.mcard.purple::after { background:var(--pur); }
.mcard.orange::after { background:var(--ora); }
.mcard.active { border-color:rgba(0,194,168,.45); background:rgba(0,194,168,.03); }
.mlbl { font-family:'IBM Plex Mono',monospace; font-size:7.5px; letter-spacing:.14em; color:var(--mu); text-transform:uppercase; margin-bottom:7px; }
.mval { font-family:'Playfair Display',serif; font-size:28px; font-weight:700; color:var(--tx); line-height:1; margin-bottom:3px; }
.msub { font-family:'IBM Plex Mono',monospace; font-size:8px; color:var(--mu); }
.mhint { font-family:'IBM Plex Mono',monospace; font-size:6.5px; letter-spacing:.1em; color:var(--mu); margin-top:5px; opacity:.55; }

/* ── Signal cards ── */
.signal-card { background:var(--sf); border:1px solid var(--bd); border-radius:8px; padding:13px 15px; margin-bottom:8px; transition:border-color .15s,transform .12s; }
.signal-card:hover { border-color:var(--bd2); transform:translateX(2px); }
.sc-row { display:flex; align-items:flex-start; gap:11px; margin-bottom:7px; }
.sc-score { width:28px; height:28px; border-radius:5px; display:flex; align-items:center; justify-content:center; font-family:'IBM Plex Mono',monospace; font-size:12px; font-weight:700; flex-shrink:0; }
.s5{background:rgba(0,194,168,.12);color:var(--teal);}
.s4{background:rgba(37,99,235,.12);color:#60a5fa;}
.s3{background:rgba(245,158,11,.1);color:var(--ora);}
.s2{background:rgba(239,68,68,.1);color:var(--red);}
.s1{background:rgba(100,116,139,.1);color:var(--mu);}
.sc-tags{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:5px;}
.tag{font-family:'IBM Plex Mono',monospace;font-size:7.5px;letter-spacing:.05em;padding:2px 6px;border-radius:2px;text-transform:uppercase;}
.tag-entity{background:rgba(0,194,168,.1);color:var(--teal);border:1px solid rgba(0,194,168,.18);}
.tag-geo{background:rgba(37,99,235,.1);color:#93c5fd;border:1px solid rgba(37,99,235,.18);}
.tag-geo-wide{background:rgba(37,99,235,.16);color:#bfdbfe;border:1px solid rgba(37,99,235,.3);}
.tag-geo-global{background:rgba(100,116,139,.1);color:#94a3b8;border:1px solid rgba(100,116,139,.2);}
.tag-impact{background:rgba(0,194,168,.06);color:#5eead4;border:1px solid rgba(0,194,168,.12);font-size:7px;}
.tag-product{background:rgba(100,116,139,.08);color:#8a9ab2;border:1px solid rgba(100,116,139,.14);}
.tag-signal{background:rgba(245,158,11,.08);color:var(--ora);border:1px solid rgba(245,158,11,.18);}
.tag-pdf{background:rgba(139,92,246,.1);color:#c4b5fd;border:1px solid rgba(139,92,246,.2);}
.tag-consultant{background:rgba(20,184,166,.1);color:#2dd4bf;border:1px solid rgba(20,184,166,.18);}
.tag-regulatory{background:rgba(239,68,68,.1);color:#fca5a5;border:1px solid rgba(239,68,68,.18);}
.sc-hl{font-size:13px;font-weight:500;color:var(--tx);line-height:1.45;margin-bottom:5px;font-family:'IBM Plex Sans',sans-serif;}
.sc-sw{font-size:11px;color:var(--dim);line-height:1.55;font-family:'IBM Plex Sans',sans-serif;}
.sc-sw strong{color:var(--teal);font-weight:500;}
.sc-ft{display:flex;align-items:center;justify-content:space-between;margin-top:8px;padding-top:7px;border-top:1px solid var(--bd);}
.sc-dt{font-family:'IBM Plex Mono',monospace;font-size:8.5px;color:var(--mu);}
.sc-src-lnk{font-family:'IBM Plex Mono',monospace;font-size:8.5px;color:var(--blue);text-decoration:none;}

/* ── Bar chart ── */
.bar-chart{display:flex;flex-direction:column;gap:6px;}
.bar-row{display:flex;align-items:center;gap:7px;}
.bar-lbl{font-family:'IBM Plex Mono',monospace;font-size:8.5px;color:var(--dim);width:76px;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.bar-bg{flex:1;height:4px;background:var(--sf3);border-radius:3px;overflow:hidden;}
.bar-fill{height:100%;border-radius:3px;background:linear-gradient(90deg,var(--teal),var(--blue));}
.bar-n{font-family:'IBM Plex Mono',monospace;font-size:8.5px;color:var(--mu);width:16px;text-align:right;}

/* ── Misc ── */
.sec-hdr{font-family:'IBM Plex Mono',monospace;font-size:7.5px;letter-spacing:.16em;color:var(--mu);text-transform:uppercase;padding:5px 0;border-bottom:1px solid var(--bd);margin-bottom:11px;}
.geo-note{background:rgba(37,99,235,.05);border:1px solid rgba(37,99,235,.15);border-radius:5px;padding:6px 11px;font-family:'IBM Plex Mono',monospace;font-size:8.5px;color:#93c5fd;letter-spacing:.04em;margin-bottom:11px;}
.drill-panel{background:var(--sf);border:1px solid rgba(0,194,168,.28);border-radius:8px;padding:14px;margin:10px 0 14px;}
.drill-title{font-family:'IBM Plex Mono',monospace;font-size:8px;letter-spacing:.14em;text-transform:uppercase;color:var(--teal);margin-bottom:11px;}
.page-info{text-align:center;font-family:'IBM Plex Mono',monospace;font-size:8.5px;color:var(--mu);padding:5px;}
.chat-user{background:var(--sf2);border:1px solid var(--bd2);border-radius:8px 8px 2px 8px;padding:10px 14px;margin:7px 0;font-size:13px;color:var(--tx);font-family:'IBM Plex Sans',sans-serif;margin-left:15%;}
.chat-bot{background:var(--sf);border:1px solid var(--bd);border-radius:2px 8px 8px 8px;padding:12px 15px;margin:3px 0 13px;font-size:13px;color:#cbd5e1;font-family:'IBM Plex Sans',sans-serif;}
.chat-bot strong{color:var(--teal);}
.chat-err{background:rgba(239,68,68,.05);border:1px solid rgba(239,68,68,.2);border-radius:6px;padding:9px 13px;font-size:11.5px;color:#fca5a5;font-family:'IBM Plex Mono',monospace;margin-bottom:11px;}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{background:transparent !important;border-bottom:1px solid var(--bd) !important;gap:0 !important;}
.stTabs [data-baseweb="tab"]{background:transparent !important;color:var(--mu) !important;font-family:'IBM Plex Mono',monospace !important;font-size:9.5px !important;letter-spacing:.1em !important;text-transform:uppercase !important;padding:10px 16px !important;border-bottom:2px solid transparent !important;}
.stTabs [aria-selected="true"]{color:var(--teal) !important;border-bottom-color:var(--teal) !important;}

/* Buttons */
.stButton button{font-family:'IBM Plex Mono',monospace !important;font-size:10px !important;letter-spacing:.07em !important;border-radius:5px !important;transition:all .18s !important;}
.stButton button[kind="primary"]{background:var(--teal) !important;color:#000 !important;border:none !important;font-weight:700 !important;}
.stButton button[kind="primary"]:hover{background:#00d9bb !important;transform:translateY(-1px) !important;}
.stButton button[kind="secondary"]{
    background:var(--sf2) !important;color:var(--dim) !important;
    border:1px solid var(--bd2) !important;
    text-align:left !important;
    justify-content:flex-start !important;
    white-space:normal !important;
    height:auto !important;
    line-height:1.4 !important;
}
.stButton button[kind="secondary"]:hover{border-color:var(--teal) !important;color:var(--teal) !important;}

/* Expander */
div[data-testid="stExpander"]{background:var(--sf) !important;border:1px solid var(--bd) !important;border-radius:6px !important;margin-bottom:6px !important;}
div[data-testid="stExpander"] summary{font-family:'IBM Plex Mono',monospace !important;font-size:9.5px !important;color:var(--dim) !important;}

/* Text input */
.stTextInput input{background:var(--sf2) !important;border:1px solid var(--bd2) !important;color:var(--tx) !important;font-family:'IBM Plex Sans',sans-serif !important;font-size:13px !important;border-radius:6px !important;}
.stTextInput input:focus{border-color:rgba(0,194,168,.45) !important;box-shadow:0 0 0 2px rgba(0,194,168,.07) !important;}

/* Typography */
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3{font-family:'Playfair Display',serif !important;color:var(--tx) !important;}
p,li,.stMarkdown p{color:#cbd5e1 !important;font-family:'IBM Plex Sans',sans-serif !important;}
hr{border-color:var(--bd) !important;margin:13px 0 !important;}
#MainMenu,footer,header{visibility:hidden;}
.stDeployButton{display:none;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# DATA
# ─────────────────────────────────────────
@st.cache_data
def _dedup_key(s):
    """
    Two-pronged dedup key:
    1. If the signal has a URL, same entity + same URL = duplicate
    2. Regardless, same entity + normalised first 60 chars of key_signal = duplicate
    We return BOTH keys; a signal is a duplicate if either matches a seen key.
    """
    import re
    entity = (s.get("entity") or "").lower().strip()
    url    = (s.get("url") or "").strip().rstrip("/")
    raw_signal = (s.get("key_signal") or "").lower()
    # Normalise: remove punctuation, collapse spaces, take first 60 chars
    norm = re.sub(r"[^a-z0-9 ]", " ", raw_signal)
    norm = re.sub(r"\s+", " ", norm).strip()[:60]
    key_text = f"{entity}||{norm}"
    key_url  = f"{entity}||url:{url}" if url and not url.startswith("local://") else None
    return key_text, key_url


def load_signals():
    try:
        with open("extracted_signals.json") as f:
            raw = json.load(f)
        seen, out = set(), []
        for s in raw:
            k_text, k_url = _dedup_key(s)
            if k_text in seen: continue
            if k_url and k_url in seen: continue
            seen.add(k_text)
            if k_url: seen.add(k_url)
            out.append(s)
        return out
    except FileNotFoundError:
        return []

signals = load_signals()

def parse_date(ds):
    if not ds: return None
    for fmt in ("%Y-%m-%dT%H:%M:%S","%Y-%m-%d",
                "%a, %d %b %Y %H:%M:%S %Z","%a, %d %b %Y %H:%M:%S %z",
                "%d %b %Y","%B %d, %Y","%Y-%m-%d %H:%M:%S.%f"):
        try: return datetime.strptime(ds[:25].strip(), fmt)
        except: pass
    return None

def freshness(sigs):
    dates = [parse_date(s.get("date","")) for s in sigs]
    dates = [d for d in dates if d]
    if not dates: return None, None, False
    n = max(dates)
    return n, min(dates), n < datetime.now() - timedelta(days=7)

def src_tag(s):
    src = s.get("source_type",""); t = s.get("type","")
    if "consultant" in src or "consultant" in t: return "consultant"
    if "pdf" in t or "pdf" in src: return "pdf"
    if "regulatory" in src or s.get("signal_type","").lower() == "regulatory update": return "regulatory"
    return "news"

def geo_ok(signal, sel):
    """
    Strict geography filtering:
    - No filter selected → show everything
    - "ASEAN-Wide" selected → show ASEAN-Wide signals + all individual
      country signals + non-ASEAN signals with asean_impact=True
    - Specific country selected (e.g. "Vietnam") → show ONLY signals
      tagged exactly for that country. ASEAN-Wide signals are NOT
      included unless the user explicitly selects ASEAN-Wide.
    - Multiple countries selected → union of above rules per country
    """
    if not sel: return True
    g  = signal.get("geography", "")
    ai = signal.get("asean_impact", g in ASEAN_ALL)
    for s in sel:
        if s == "ASEAN-Wide":
            # ASEAN-Wide: show everything with any ASEAN relevance
            if g == "ASEAN-Wide": return True
            if g in ASEAN_COUNTRIES: return True
            if ai: return True
        else:
            # Specific country: ONLY exact match — no ASEAN-Wide bleed
            if g == s: return True
    return False

def geo_cls(geo):
    if geo == "ASEAN-Wide": return "tag-geo-wide"
    if geo in ASEAN_COUNTRIES: return "tag-geo"
    return "tag-geo-global"

def render_card(s):
    score = s.get("relevance_score", 0)
    scls  = f"s{max(1, min(int(score), 5))}"
    dt    = s.get("date","")[:10]
    stag  = src_tag(s)
    geo   = s.get("geography","")
    ai    = s.get("asean_impact", geo in ASEAN_ALL)
    tags  = ""
    if s.get("entity"):       tags += f'<span class="tag tag-entity">{s["entity"]}</span>'
    if geo:                   tags += f'<span class="tag {geo_cls(geo)}">{geo}</span>'
    if geo not in ASEAN_ALL and ai: tags += '<span class="tag tag-impact">ASEAN impact</span>'
    if s.get("product_area"): tags += f'<span class="tag tag-product">{s["product_area"]}</span>'
    if s.get("signal_type"):  tags += f'<span class="tag tag-signal">{s["signal_type"]}</span>'
    if stag == "pdf":          tags += '<span class="tag tag-pdf">PDF</span>'
    elif stag == "consultant": tags += '<span class="tag tag-consultant">Consultant</span>'
    elif stag == "regulatory": tags += '<span class="tag tag-regulatory">Regulatory</span>'
    url = s.get("url","")
    src_html = (f'<a class="sc-src-lnk" href="{url}" target="_blank">↗ Source</a>'
                if url and not url.startswith("local://") else "")
    st.markdown(f"""<div class="signal-card">
        <div class="sc-row">
            <div class="sc-score {scls}">{int(score)}</div>
            <div style="flex:1;min-width:0">
                <div class="sc-tags">{tags}</div>
                <div class="sc-hl">{s.get('key_signal','')}</div>
            </div>
        </div>
        <div class="sc-sw"><strong>So what:</strong> {s.get('so_what','')}</div>
        <div class="sc-ft"><span class="sc-dt">🗓 {dt or '—'}</span>{src_html}</div>
    </div>""", unsafe_allow_html=True)

def paginated(items, pkey, label="signals"):
    items = sorted(items, key=lambda x: x.get("relevance_score",0), reverse=True)
    n = len(items)
    if n == 0: st.info(f"No {label} found."); return
    pages = max(1,(n+PAGE_SIZE-1)//PAGE_SIZE)
    if pkey not in st.session_state: st.session_state[pkey] = 1
    p = max(1, min(st.session_state[pkey], pages))
    st.session_state[pkey] = p
    s, e = (p-1)*PAGE_SIZE, min(p*PAGE_SIZE, n)
    st.caption(f"{s+1}–{e} of {n} {label} · sorted by relevance")
    for sig in items[s:e]: render_card(sig)
    if pages > 1:
        c1,c2,c3 = st.columns([1,4,1])
        with c1:
            if st.button("← Prev", key=f"{pkey}_p", disabled=(p<=1)):
                st.session_state[pkey] -= 1; st.rerun()
        with c2:
            st.markdown(f'<div class="page-info">Page {p} of {pages}</div>', unsafe_allow_html=True)
        with c3:
            if st.button("Next →", key=f"{pkey}_n", disabled=(p>=pages)):
                st.session_state[pkey] += 1; st.rerun()

def bar_html(items, mx):
    rows = "".join(
        f'<div class="bar-row"><div class="bar-lbl">{l[:12]}</div>'
        f'<div class="bar-bg"><div class="bar-fill" style="width:{int(c/mx*100) if mx else 0}%">'
        f'</div></div><div class="bar-n">{c}</div></div>'
        for l,c in items)
    return f'<div class="bar-chart">{rows}</div>'

# ─────────────────────────────────────────
# FULL-WIDTH HEADER — spans entire page
# ─────────────────────────────────────────
st.markdown("""
<div class="main-hdr">
    <div style="display:flex;align-items:center;justify-content:space-between">
        <div>
            <div class="main-title">ASEAN Cash <em>Intelligence</em></div>
            <div class="main-sub">Market &amp; Transaction Intelligence System · ASEAN Cash Management</div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
            <div style="background:#00c2a8;color:#000;font-family:'IBM Plex Mono',monospace;
                 font-size:10px;font-weight:700;letter-spacing:.2em;padding:4px 12px;
                 border-radius:3px;text-transform:uppercase;letter-spacing:.22em">MANTIS</div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:7.5px;
                 color:#475569;letter-spacing:.1em;text-transform:uppercase">
                 Intelligence Platform</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# LAYOUT: custom sidebar via columns
# ─────────────────────────────────────────
sidebar_col, main_col = st.columns([1.2, 3.6], gap="small")

# ═══════════════════════════════════════════
# CUSTOM SIDEBAR COLUMN
# ═══════════════════════════════════════════
with sidebar_col:
    # Freshness
    newest, _, is_stale = freshness(signals)
    dot_col = "#ef4444" if is_stale else "#00c2a8"
    icon    = "⚠" if is_stale else "✓"
    info    = ("Stale — run pipeline" if is_stale
               else f"Fresh · {newest.strftime('%d %b %Y') if newest else 'today'} · {len(signals)} signals")
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:7px;padding:7px 4px 10px;
         font-family:'IBM Plex Mono',monospace;font-size:8.5px;
         letter-spacing:.06em;color:{dot_col};border-bottom:1px solid #1e2a3a;
         margin-bottom:8px">
        <div style="width:5px;height:5px;border-radius:50%;
             background:{dot_col};flex-shrink:0"></div>
        <span>{icon} {info}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Filters — use visible labels so widgets render reliably ──
    geo_filter = st.multiselect(
        "Geography", options=GEO_OPTIONS, key="f_geo", placeholder="All markets"
    )
    prod_opts = sorted(set(
        s.get("product_area","").strip() for s in signals
        if s.get("product_area","").strip()
    ))
    product_filter = st.multiselect(
        "Product Area", options=prod_opts, key="f_prod", placeholder="All areas"
    )
    type_opts = sorted(set(
        s.get("signal_type","").strip() for s in signals
        if s.get("signal_type","").strip()
    ))
    type_filter = st.multiselect(
        "Signal Type", options=type_opts, key="f_type", placeholder="All types"
    )
    source_filter = st.multiselect(
        "Source Type", options=["news","pdf","consultant","regulatory"],
        key="f_src", placeholder="All sources"
    )
    comp_opts = sorted(set(
        s.get("entity","").strip() for s in signals
        if s.get("entity","").strip()
    ))
    competitor_filter = st.multiselect(
        "Competitor", options=comp_opts, key="f_comp", placeholder="All competitors"
    )
    min_score = st.slider("Min Score", min_value=1, max_value=5, value=1, key="f_score")

    st.divider()

    st.markdown("""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:8.5px;
         color:#475569;line-height:2">
        <div style="font-size:7.5px;letter-spacing:.13em;text-transform:uppercase;
             margin-bottom:4px;color:#475569">Sources active</div>
        <span style="color:#00c2a8">✓</span> TFG · Finextra · Paypers<br>
        <span style="color:#00c2a8">✓</span> Fintech News SG/ID/MY/PH<br>
        <span style="color:#00c2a8">✓</span> Asian Banker · TechInAsia<br>
        <span style="color:#00c2a8">✓</span> MAS · BNM · BSP<br>
        <span style="color:#00c2a8">✓</span> DBS · OCBC · HSBC · JPM<br>
        <span style="color:#00c2a8">✓</span> McKinsey · KPMG · EY · OW<br>
        <span style="color:#00c2a8">✓</span> BIS · ADB · IMF · SWIFT
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────
# FILTER
# ─────────────────────────────────────────
cutoff = datetime.now() - timedelta(days=30)

def apply_filters(sigs):
    out  = []
    seen = set()   # second dedup pass — catches anything load_signals missed
    for s in sigs:
        d = parse_date(s.get("date",""))
        if d and d < cutoff: continue
        if not geo_ok(s, geo_filter): continue
        if product_filter    and s.get("product_area","").strip() not in product_filter:    continue
        if type_filter       and s.get("signal_type","").strip()  not in type_filter:       continue
        if source_filter     and src_tag(s) not in source_filter:                           continue
        if competitor_filter and s.get("entity","").strip() not in competitor_filter:       continue
        if s.get("relevance_score",0) < min_score:                                          continue
        # Dedup check — use same logic as load_signals
        k_text, k_url = _dedup_key(s)
        if k_text in seen: continue
        if k_url and k_url in seen: continue
        seen.add(k_text)
        if k_url: seen.add(k_url)
        out.append(s)
    return sorted(out, key=lambda x: x.get("relevance_score",0), reverse=True)

fs = apply_filters(signals)

# ═══════════════════════════════════════════
# MAIN CONTENT COLUMN
# ═══════════════════════════════════════════
with main_col:

    tab1, tab2, tab3, tab4 = st.tabs([
        "◈  Overview", "⚡  Signals", "◎  Ask Intelligence", "▤  Weekly Digest"
    ])

    # ═══════════════════
    # TAB 1 — OVERVIEW
    # ═══════════════════
    with tab1:
        total   = len(fs)
        hi_list = [s for s in fs if s.get("relevance_score",0) >= 4]
        pd_list = [s for s in fs if "pdf" in s.get("type","")]
        rg_list = [s for s in fs if s.get("signal_type") == "Regulatory Update"]
        active_drill = st.session_state.get("drill_mode")

        c1,c2,c3,c4 = st.columns(4)
        with c1:
            st.markdown(f"""<div class="mcard teal">
                <div class="mlbl">Total Signals</div>
                <div class="mval">{total}</div>
                <div class="msub">Last 30 days</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            is_hi = active_drill == "high"
            st.markdown(f"""<div class="mcard blue {'active' if is_hi else ''}">
                <div class="mlbl">High Priority</div>
                <div class="mval" style="color:#60a5fa">{len(hi_list)}</div>
                <div class="msub">Score 4–5</div>
                <div class="mhint">{'▲ SHOWING BELOW' if is_hi else '▼ CLICK TO EXPAND'}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("▼ High Priority" if not is_hi else "▲ Close",
                         key="btn_hi", use_container_width=True, type="secondary"):
                st.session_state["drill_mode"] = None if is_hi else "high"
                st.session_state["dp_high"] = 1; st.rerun()
        with c3:
            is_pd = active_drill == "pdf"
            st.markdown(f"""<div class="mcard purple {'active' if is_pd else ''}">
                <div class="mlbl">PDF Reports</div>
                <div class="mval" style="color:#c4b5fd">{len(pd_list)}</div>
                <div class="msub">Consultant &amp; research</div>
                <div class="mhint">{'▲ SHOWING BELOW' if is_pd else '▼ CLICK TO EXPAND'}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("▼ PDF Reports" if not is_pd else "▲ Close",
                         key="btn_pd", use_container_width=True, type="secondary"):
                st.session_state["drill_mode"] = None if is_pd else "pdf"
                st.session_state["dp_pdf"] = 1; st.rerun()
        with c4:
            is_rg = active_drill == "reg"
            st.markdown(f"""<div class="mcard orange {'active' if is_rg else ''}">
                <div class="mlbl">Regulatory</div>
                <div class="mval" style="color:var(--ora)">{len(rg_list)}</div>
                <div class="msub">Alerts this period</div>
                <div class="mhint">{'▲ SHOWING BELOW' if is_rg else '▼ CLICK TO EXPAND'}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("▼ Regulatory" if not is_rg else "▲ Close",
                         key="btn_rg", use_container_width=True, type="secondary"):
                st.session_state["drill_mode"] = None if is_rg else "reg"
                st.session_state["dp_reg"] = 1; st.rerun()

        if geo_filter:
            notes = [("ASEAN-Wide (all ASEAN markets + global with ASEAN impact)"
                      if g == "ASEAN-Wide" else f"{g} only") for g in geo_filter]
            st.markdown(f'<div class="geo-note" style="margin-top:10px">🌏 {" · ".join(notes)}</div>',
                unsafe_allow_html=True)

        dm = st.session_state.get("drill_mode")
        if dm:
            cfg = {"high":("High Priority Signals — Score 4–5", hi_list, "dp_high"),
                   "pdf": ("PDF & Consultant Reports",           pd_list, "dp_pdf"),
                   "reg": ("Regulatory Signals",                 rg_list, "dp_reg")}
            if dm in cfg:
                label, items, pkey = cfg[dm]
                st.markdown(f'<div class="drill-panel"><div class="drill-title">▸ {label}</div>',
                    unsafe_allow_html=True)
                paginated(items, pkey, label.lower())
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        lc, rc = st.columns([3,2])

        with lc:
            st.markdown('<div class="sec-hdr">🔥 Top Signals This Period</div>', unsafe_allow_html=True)
            if fs:
                for s in fs[:5]: render_card(s)
            else:
                st.info("No signals match your current filters.")

        with rc:
            st.markdown('<div class="sec-hdr">Competitor Activity</div>', unsafe_allow_html=True)
            ec = {}
            for s in fs:
                e = s.get("entity","")
                if e: ec[e] = ec.get(e,0) + 1
            top_e = sorted(ec.items(), key=lambda x:x[1], reverse=True)[:8]
            if top_e: st.markdown(bar_html(top_e, max(c for _,c in top_e)), unsafe_allow_html=True)

            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="sec-hdr">Signal Sources</div>', unsafe_allow_html=True)
            sc2 = {}
            for s in fs: t=src_tag(s); sc2[t]=sc2.get(t,0)+1
            if sc2: st.markdown(bar_html(sorted(sc2.items(),key=lambda x:x[1],reverse=True),
                                         max(sc2.values())), unsafe_allow_html=True)

            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="sec-hdr">Geography Breakdown</div>', unsafe_allow_html=True)
            gc = {}
            for s in fs:
                g = s.get("geography","")
                if g: gc[g] = gc.get(g,0) + 1
            if gc:
                top_g = sorted(gc.items(),key=lambda x:x[1],reverse=True)[:8]
                st.markdown(bar_html(top_g, max(c for _,c in top_g)), unsafe_allow_html=True)

    # ═══════════════════
    # TAB 2 — SIGNALS
    # ═══════════════════
    with tab2:
        h1, h2 = st.columns([4,1])
        with h1:
            st.markdown(f'<div class="sec-hdr">{len(fs)} signals · last 30 days · sorted by relevance</div>',
                unsafe_allow_html=True)
        with h2:
            sort_by = st.selectbox("sort_sig", options=["Relevance","Date","Entity","Geography"],
                label_visibility="collapsed")

        if geo_filter:
            gn = ["ASEAN-Wide (all markets + ASEAN impact)" if g=="ASEAN-Wide" else f"{g} only" for g in geo_filter]
            st.markdown(f'<div class="geo-note">🌏 {" · ".join(gn)}</div>', unsafe_allow_html=True)

        disp = fs
        if sort_by == "Date":        disp = sorted(fs, key=lambda x:x.get("date",""),reverse=True)
        elif sort_by == "Entity":    disp = sorted(fs, key=lambda x:x.get("entity",""))
        elif sort_by == "Geography": disp = sorted(fs, key=lambda x:x.get("geography",""))

        if not disp:
            st.markdown("""<div style="text-align:center;padding:60px 20px;color:#475569">
                <div style="font-size:26px;margin-bottom:8px">◎</div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.12em">
                    NO SIGNALS MATCH YOUR FILTERS</div></div>""", unsafe_allow_html=True)
        else:
            paginated(disp, "sig_page", "signals")

    # ═══════════════════════
    # TAB 3 — ASK INTELLIGENCE
    # ═══════════════════════
    with tab3:
        fresh_sigs = sorted([s for s in signals
            if (lambda d: d is None or d>=cutoff)(parse_date(s.get("date","")))],
            key=lambda x:x.get("relevance_score",0), reverse=True)

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        st.markdown("""
        <div style="margin-bottom:10px">
            <div style="font-family:'Playfair Display',serif;font-size:17px;font-weight:700;
                 color:#f1f5f9;margin-bottom:2px">Ask Intelligence</div>
            <div style="font-family:'IBM Plex Sans',sans-serif;font-size:10.5px;color:#475569">
                Grounded in the last 30 days of signals only.</div>
        </div>""", unsafe_allow_html=True)

        ci1, ci2, ci3 = st.columns([8,1,1])
        with ci1:
            user_input = st.text_input("chat_q",
                placeholder="Ask about ASEAN cash management intelligence…",
                label_visibility="collapsed", key="chat_input")
        with ci2:
            send = st.button("▶", type="primary", use_container_width=True, key="send_btn")
        with ci3:
            if st.button("⊘", use_container_width=True, key="clear_btn", help="Clear"):
                st.session_state.chat_history = []; st.rerun()

        if send and user_input.strip():
            st.session_state.chat_history.insert(0, {
                "role":"user","content":user_input.strip(),
                "answer":None,"sources":None,"error":None})
            st.rerun()

        # Blocked entities — never generate questions about these
        BLOCKED_ENTITIES = {"standard chartered", "stanchart", "sc", "standard chartered bank"}

        def build_presets(sigs):
            """
            Build 6 suggested queries that:
            1. Never reference Standard Chartered or blocked entities
            2. Are broad enough to always find matching signals
            3. Are grounded in what actually exists in the last 30 days
            """
            if not sigs:
                return []

            # Count entities and product areas
            ent, prod, geos = {}, {}, {}
            for s in sigs:
                e = s.get("entity","").strip()
                p = s.get("product_area","").strip()
                g = s.get("geography","").strip()
                # Skip blocked entities
                if e and e.lower() not in BLOCKED_ENTITIES:
                    ent[e] = ent.get(e,0) + 1
                if p: prod[p] = prod.get(p,0) + 1
                if g: geos[g] = geos.get(g,0) + 1

            cands = []

            # Q1 — top geography: always has signals
            top_geos = [g for g,_ in sorted(geos.items(),key=lambda x:x[1],reverse=True)
                        if g not in ("Global",) ][:1]
            if top_geos:
                g = top_geos[0]
                if g == "ASEAN-Wide":
                    cands.append("What are the biggest cash management developments across ASEAN this month?")
                else:
                    cands.append(f"What are the key cash management signals coming out of {g}?")

            # Q2 — top product area: always has signals
            top_prods = [p for p,_ in sorted(prod.items(),key=lambda x:x[1],reverse=True)][:1]
            if top_prods:
                cands.append(f"Summarise the latest signals on {top_prods[0]} in ASEAN.")

            # Q3 — second product area if different
            if len(top_prods) >= 2 or len(prod) >= 2:
                second = [p for p,_ in sorted(prod.items(),key=lambda x:x[1],reverse=True)
                          if p != (top_prods[0] if top_prods else "")][0:1]
                if second:
                    cands.append(f"What is happening in {second[0]} across ASEAN banks?")

            # Q4 — top non-blocked competitor
            top_ents = [e for e,_ in sorted(ent.items(),key=lambda x:x[1],reverse=True)
                        if e.lower() not in BLOCKED_ENTITIES][:1]
            if top_ents:
                cands.append(f"What is {top_ents[0]} doing in ASEAN cash management?")

            # Q5 — regulatory: always present in ASEAN signals
            has_reg = any(
                s.get("signal_type","").lower() == "regulatory update" or
                s.get("product_area","").lower() == "regulatory"
                for s in sigs
            )
            if has_reg:
                cands.append("What regulatory changes in ASEAN should transaction banks act on?")
            else:
                cands.append("What are the most important market trends in ASEAN cash management right now?")

            # Q6 — innovation/real-time payments: very common in signals
            has_innov = any(
                s.get("product_area","") in ("Innovation","Payments & Collections")
                for s in sigs
            )
            if has_innov:
                cands.append("What are the latest real-time payment and innovation signals in ASEAN?")
            else:
                cands.append("Which banks are most active in ASEAN cash management this month?")

            return cands[:6]

        presets = build_presets(fresh_sigs)
        if presets and not st.session_state.chat_history:
            st.markdown('''<div class="sec-hdr" style="margin-top:10px">Suggested queries
                — click any to ask</div>''', unsafe_allow_html=True)
            # Render as single-column left-aligned list for clean readability
            for i, p in enumerate(presets):
                col_btn, col_spacer = st.columns([4, 1])
                with col_btn:
                    if st.button(
                        f"› {p}", key=f"preset_{i}",
                        use_container_width=True, type="secondary"
                    ):
                        st.session_state.chat_history.insert(0, {
                            "role":"user","content":p,
                            "answer":None,"sources":None,"error":None})
                        st.rerun()

        for i, msg in enumerate(st.session_state.chat_history):
            if msg.get("role")=="user" and msg.get("answer") is None and msg.get("error") is None:
                with st.spinner("Searching signals…"):
                    ctx="".join(
                        f"Entity:{s.get('entity','')}\nGeo:{s.get('geography','')}\n"
                        f"ASEAN Impact:{s.get('asean_impact',True)}\nProduct:{s.get('product_area','')}\n"
                        f"Type:{s.get('signal_type','')}\nDate:{s.get('date','')[:10]}\n"
                        f"Signal:{s.get('key_signal','')}\nSoWhat:{s.get('so_what','')}\n---\n"
                        for s in fresh_sigs)
                    answer=None; err=None
                    for attempt in range(3):
                        try:
                            r=anthropic_client.messages.create(
                                model="claude-sonnet-4-5", max_tokens=800,
                                messages=[{"role":"user","content":(
                                    "You are a senior transaction banking analyst covering ASEAN Cash Management.\n"
                                    "Answer using only the intelligence signals below (last 30 days).\n"
                                    "Signals marked ASEAN Impact: True are relevant even if non-ASEAN origin.\n"
                                    "Be direct, cite entities, geographies, and dates.\n"
                                    "Weight consultant/PDF signals higher.\n"
                                    "End with: 'Implication for Transaction Banks:' on a new line.\n"
                                    "If insufficient signals, say so clearly.\n\n"
                                    f"Question: {msg['content']}\n\nSignals:\n{ctx[:6000]}"
                                )}])
                            answer=r.content[0].text.strip(); err=None; break
                        except Exception as ex:
                            if "overloaded" in str(ex).lower() and attempt<2:
                                time.sleep(3+attempt*2); continue
                            err=("Service temporarily busy — please try again."
                                 if "overloaded" in str(ex).lower() else f"Query failed: {ex}")
                            break
                    rel=[s for s in fresh_sigs if any(
                        w.lower() in (s.get('key_signal','')+s.get('entity','')).lower()
                        for w in msg['content'].split() if len(w)>4)][:4]
                    st.session_state.chat_history[i].update({"answer":answer,"sources":rel,"error":err})
                    st.rerun()

        for msg in st.session_state.chat_history:
            if msg.get("role") != "user": continue
            st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
            if msg.get("error"):
                st.markdown(f'<div class="chat-err">⚠ {msg["error"]}</div>', unsafe_allow_html=True)
            elif msg.get("answer"):
                st.markdown(f'<div class="chat-bot">{msg["answer"]}</div>', unsafe_allow_html=True)
                srcs = msg.get("sources") or []
                if srcs:
                    with st.expander("📎 Signals referenced", expanded=False):
                        for r in srcs:
                            icon = "📄" if "pdf" in src_tag(r) else "📰"
                            g = r.get("geography","")
                            ai_n = " ⟶ ASEAN" if g not in ASEAN_ALL and r.get("asean_impact") else ""
                            url = r.get("url","")
                            ul = f" · [source]({url})" if url and not url.startswith("local://") else ""
                            st.caption(f"{icon} [{r.get('date','')[:10]}] **{r.get('entity','')}** "
                                       f"({g}{ai_n}) — {r.get('key_signal','')[:80]}{ul}")
            elif msg.get("answer") is None and msg.get("error") is None:
                st.markdown('<div class="chat-bot" style="color:#475569">Thinking…</div>',
                    unsafe_allow_html=True)

        if not fresh_sigs:
            st.warning("No signals available. Run the pipeline first.")

    # ═══════════════════════
    # TAB 4 — WEEKLY DIGEST
    # ═══════════════════════
    with tab4:
        d1, d2 = st.columns([4,1])
        with d1:
            st.markdown("""
            <div style="font-family:'Playfair Display',serif;font-size:17px;font-weight:700;
                 color:#f1f5f9;margin-bottom:2px">Weekly Intelligence Digest</div>
            <div style="font-family:'IBM Plex Sans',sans-serif;font-size:10.5px;color:#475569">
                Auto-generated from the last 30 days · Includes consultant reports and PDFs</div>
            """, unsafe_allow_html=True)

        dfiles = sorted(glob.glob("digest_*.md"), reverse=True)
        if dfiles:
            try:
                dd   = datetime.strptime(dfiles[0].replace("digest_","").replace(".md",""),"%Y%m%d")
                dold = (datetime.now()-dd).days
            except: dd=None; dold=0
            with d2:
                if dold>7:
                    st.markdown(f'<div style="background:rgba(239,68,68,.07);border:1px solid '
                        f'rgba(239,68,68,.2);border-radius:5px;padding:7px 11px;'
                        f'font-family:IBM Plex Mono,monospace;font-size:8.5px;'
                        f'color:#ef4444;margin-top:4px">⚠ {dold}d old</div>', unsafe_allow_html=True)

            sf = (st.selectbox("dig_sel", options=dfiles,
                  format_func=lambda x:x.replace("digest_","").replace(".md",""),
                  label_visibility="collapsed") if len(dfiles)>1 else dfiles[0])
            with open(sf) as f: dt = f.read()
            st.caption(f"Generated {dd.strftime('%d %B %Y')} · {dold} days ago" if dd else sf)
            st.divider()

            scols={"competitor":"#00c2a8","regulatory":"#2563eb","consultant":"#8b5cf6",
                   "research":"#8b5cf6","innovation":"#f59e0b","transaction":"#00c2a8","watch":"#ef4444"}
            for sec in dt.split("###")[1:]:
                lines=sec.strip().split("\n")
                if not lines: continue
                title=lines[0].strip(); body="\n".join(lines[1:]).strip()
                color="#00c2a8"
                for k,v in scols.items():
                    if k.lower() in title.lower(): color=v; break
                st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:8px;'
                    f'letter-spacing:.14em;text-transform:uppercase;color:{color};'
                    f'margin-top:8px;margin-bottom:6px;padding-bottom:5px;'
                    f'border-bottom:1px solid #1e2a3a">{title}</div>', unsafe_allow_html=True)
                bullets=[l.lstrip("-•").strip() for l in body.split("\n") if l.strip().startswith(("-","•"))]
                if bullets:
                    for b in bullets: st.markdown(f"— {b}")
                else:
                    st.markdown(body)
                st.markdown("<div style='margin-bottom:13px'></div>", unsafe_allow_html=True)
            st.divider()
            st.download_button("⬇ Download Digest", data=dt, file_name=sf, mime="text/markdown")
        else:
            st.info("No digest found. Run digest.py to generate one.")
            if st.button("Generate now", type="primary"):
                if not signals: st.error("No signals. Run the pipeline first.")
                else:
                    with st.spinner("Generating…"):
                        try:
                            from digest import generate_digest; generate_digest(signals)
                            st.success("Done. Refresh to view.")
                        except Exception as e: st.error(f"Failed: {e}")