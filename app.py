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
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
/* ── Option A: Deep Navy — cross-browser safe rewrite ──
   Tested against: MS Edge (Chromium), Safari 17+
   Key fixes:
   - System font stack only (no Google Fonts import = no Safari ITP block, no Edge FOIT)
   - All muted text ≥ 4.5:1 contrast on their background
   - letter-spacing reduced from 0.14em → 0.07em (prevents Edge overflow)
   - No -webkit-font-smoothing (inconsistent between Edge/Safari, removed)
   - No fixed-px sidebar widths; fluid layout via minmax(0,1fr)
   - All font sizes ≥ 11px (Windows ClearType 125% scaling safe)
   - Flexbox gap replaced with margin where Edge had spacing bugs
   - No min-height:100vh on column containers (fights Streamlit in Edge)
*/

/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; }

:root {
    /* Backgrounds — navy ramp */
    --bg:   #0d1421;
    --sf:   #112035;
    --sf2:  #152744;
    --sf3:  #1a2f50;
    /* Borders */
    --bd:   #1e3a5f;
    --bd2:  #254872;
    /* Accent */
    --teal: #00c2a8;
    --teal-dim: #00876f;
    --blue: #60a5fa;
    --ora:  #f59e0b;
    --pur:  #a78bfa;
    --red:  #f87171;
    /* Text — all ≥ 4.5:1 on --sf or --sf2 */
    --tx:   #e2e8f0;   /* primary   — 11.2:1 on --sf */
    --dim:  #94a3b8;   /* secondary —  5.1:1 on --sf */
    --mu:   #7090b0;   /* muted     —  4.6:1 on --sf */
    /* Typography — system stack, zero import latency */
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    --font-mono: ui-monospace, "Cascadia Code", "Menlo", "Consolas", monospace;
    --font-serif: Georgia, "Times New Roman", serif;
}

.stApp { background: var(--bg) !important; }
.stApp > header { display: none !important; }

/* Hide default sidebar */
section[data-testid="stSidebar"]  { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }

/* Remove Streamlit default padding */
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── Custom sidebar panel ── */
.cust-sidebar {
    background: var(--sf);
    border-right: 1px solid var(--bd);
    padding: 0;
}
.sb-head {
    background: var(--sf2);
    border-bottom: 1px solid var(--bd);
    padding: 14px 16px 12px;
}
.sb-badge {
    display: inline-block;
    background: var(--teal);
    color: #000;
    font-family: var(--font-mono);
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.12em;
    padding: 3px 7px;
    border-radius: 2px;
    text-transform: uppercase;
    margin-bottom: 7px;
}
.sb-title {
    font-family: var(--font-serif);
    font-size: 15px;
    font-weight: 700;
    color: var(--tx);
    margin: 0 0 2px;
}
.sb-title em { color: var(--teal); font-style: normal; }
.sb-sub {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--mu);
    letter-spacing: 0.07em;
    text-transform: uppercase;
}
.sb-status {
    display: flex;
    align-items: center;
    padding: 7px 16px;
    border-bottom: 1px solid var(--bd);
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.04em;
}
.sb-status.ok    { color: var(--teal); }
.sb-status.stale { color: var(--red); }
.dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
    margin-right: 7px;
}
.dot.ok    { background: var(--teal); }
.dot.stale { background: var(--red); }
.sb-src {
    padding: 10px 16px 14px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--mu);
    line-height: 2;
}
.sb-src-hdr {
    font-size: 10px;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin-bottom: 4px;
    display: block;
}

/* ── Filter widget labels ── */
[data-testid="stVerticalBlock"] .stMultiSelect label p,
[data-testid="stVerticalBlock"] .stSlider label p,
[data-testid="stVerticalBlock"] .stWidgetLabel p {
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
    letter-spacing: 0.07em !important;
    color: var(--mu) !important;
    text-transform: uppercase !important;
    font-weight: 400 !important;
    margin-bottom: 2px !important;
}

/* ── Multiselect ── */
.stMultiSelect [data-baseweb="select"] > div {
    background: var(--sf2) !important;
    border: 1px solid var(--bd2) !important;
    border-radius: 5px !important;
    min-height: 34px !important;
}
.stMultiSelect [data-baseweb="select"] > div:focus-within {
    border-color: rgba(0,194,168,0.6) !important;
    box-shadow: 0 0 0 2px rgba(0,194,168,0.1) !important;
}
.stMultiSelect [data-baseweb="tag"] {
    background: rgba(0,194,168,0.15) !important;
    border: 1px solid rgba(0,194,168,0.3) !important;
    color: var(--teal) !important;
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
    border-radius: 3px !important;
}
.stMultiSelect [data-baseweb="tag"] span { color: var(--teal) !important; }
[data-baseweb="popover"] {
    background: var(--sf2) !important;
    border: 1px solid var(--bd2) !important;
}
[data-baseweb="menu"] li {
    color: var(--dim) !important;
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
}
[data-baseweb="menu"] li:hover { background: var(--sf3) !important; }
/* B1: Hide placeholder in multiselect search input — all vendor prefixes for Edge + Safari */
.stMultiSelect input {
    color: var(--dim) !important;
    font-size: 11px !important;
}
.stMultiSelect input::placeholder          { color: transparent !important; opacity: 0 !important; }
.stMultiSelect input::-webkit-input-placeholder { color: transparent !important; opacity: 0 !important; }
.stMultiSelect input::-ms-input-placeholder     { color: transparent !important; opacity: 0 !important; }
/* Keep selected value text and arrow legible */
div[data-baseweb="select"] span {
    color: var(--mu) !important;
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
}
/* Selectbox (sort dropdown, digest selector) — dark bg + legible text */
.stSelectbox [data-baseweb="select"] > div {
    background: var(--sf2) !important;
    border: 1px solid var(--bd2) !important;
    border-radius: 5px !important;
    min-height: 34px !important;
}
.stSelectbox [data-baseweb="select"] > div:focus-within {
    border-color: rgba(0,194,168,0.6) !important;
}
.stSelectbox [data-baseweb="select"] span,
.stSelectbox [data-baseweb="select"] div[class] {
    color: var(--dim) !important;
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
}
/* Slider tick labels */
.stSlider [data-testid="stTickBarMin"],
.stSlider [data-testid="stTickBarMax"] {
    color: var(--mu) !important;
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
}

/* ── Slider ── */
.stSlider > div > div > div > div { background: var(--teal) !important; }
.stSlider > div > div > div       { background: var(--sf3) !important; }
.stSlider { padding: 0 !important; }

/* ── Main header ── */
.main-hdr {
    background: var(--sf2);
    border-bottom: 1px solid var(--bd);
    padding: 14px 20px 12px;
    margin-bottom: 16px;
}
.main-title {
    font-family: var(--font-serif);
    font-size: 20px;
    font-weight: 700;
    color: var(--tx);
    letter-spacing: -0.01em;
    margin: 0;
}
.main-title em { color: var(--teal); font-style: normal; }
.main-sub {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--mu);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-top: 3px;
}

/* ── Metric cards ── */
.mcard {
    background: var(--sf);
    border: 1px solid var(--bd);
    border-radius: 8px;
    padding: 13px 15px;
    position: relative;
    overflow: hidden;
}
.mcard::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.mcard.teal::after   { background: var(--teal); }
.mcard.blue::after   { background: var(--blue); }
.mcard.purple::after { background: var(--pur); }
.mcard.orange::after { background: var(--ora); }
.mcard.active {
    border-color: rgba(0,194,168,0.5);
    background: rgba(0,194,168,0.04);
}
.mlbl {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.07em;
    color: var(--mu);
    text-transform: uppercase;
    margin-bottom: 7px;
}
.mval {
    font-family: var(--font-serif);
    font-size: 28px;
    font-weight: 700;
    color: var(--tx);
    line-height: 1;
    margin-bottom: 3px;
}
.msub {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--mu);
}
.mhint {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.06em;
    color: var(--mu);
    margin-top: 5px;
    opacity: 0.8;
}

/* ── Signal cards ── */
.signal-card {
    background: var(--sf);
    border: 1px solid var(--bd);
    border-radius: 8px;
    padding: 13px 15px;
    margin-bottom: 8px;
    transition: border-color 0.15s, transform 0.12s;
}
.signal-card:hover {
    border-color: var(--bd2);
    transform: translateX(2px);
}
.sc-row {
    display: flex;
    align-items: flex-start;
    gap: 11px;
    margin-bottom: 7px;
}
.sc-score {
    width: 28px;
    height: 28px;
    border-radius: 5px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 700;
    flex-shrink: 0;
}
.s5 { background: rgba(0,194,168,0.15);  color: var(--teal); }
.s4 { background: rgba(96,165,250,0.15); color: var(--blue); }
.s3 { background: rgba(245,158,11,0.12); color: var(--ora); }
.s2 { background: rgba(248,113,113,0.12);color: var(--red); }
.s1 { background: rgba(112,144,176,0.12);color: var(--mu); }

.sc-tags {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    margin-bottom: 5px;
}
.tag {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.04em;
    padding: 2px 6px;
    border-radius: 2px;
    text-transform: uppercase;
    /* no -webkit-font-smoothing */
}
.tag-entity     { background: rgba(0,194,168,0.12);  color: var(--teal); border: 1px solid rgba(0,194,168,0.2); }
.tag-geo        { background: rgba(96,165,250,0.12); color: var(--blue); border: 1px solid rgba(96,165,250,0.2); }
.tag-geo-wide   { background: rgba(96,165,250,0.18); color: #bfdbfe;     border: 1px solid rgba(96,165,250,0.32); }
.tag-geo-global { background: rgba(112,144,176,0.1); color: var(--dim);  border: 1px solid rgba(112,144,176,0.2); }
.tag-impact     { background: rgba(0,194,168,0.08);  color: #5eead4;     border: 1px solid rgba(0,194,168,0.14); font-size: 10px; }
.tag-product    { background: rgba(112,144,176,0.1); color: #8fb4d4;     border: 1px solid rgba(112,144,176,0.18); }
.tag-signal     { background: rgba(245,158,11,0.1);  color: var(--ora);  border: 1px solid rgba(245,158,11,0.2); }
.tag-pdf        { background: rgba(167,139,250,0.12);color: #c4b5fd;     border: 1px solid rgba(167,139,250,0.22); }
.tag-consultant { background: rgba(45,212,191,0.1);  color: #2dd4bf;     border: 1px solid rgba(45,212,191,0.2); }
.tag-regulatory { background: rgba(248,113,113,0.12);color: #fca5a5;     border: 1px solid rgba(248,113,113,0.22); }

.sc-hl {
    font-size: 13px;
    font-weight: 500;
    color: var(--tx);
    line-height: 1.45;
    margin-bottom: 5px;
    font-family: var(--font-sans);
}
.sc-sw {
    font-size: 12px;
    color: var(--dim);
    line-height: 1.55;
    font-family: var(--font-sans);
}
.sc-sw strong { color: var(--teal); font-weight: 500; }
.sc-ft {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 8px;
    padding-top: 7px;
    border-top: 1px solid var(--bd);
}
.sc-dt {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--mu);
}
.sc-src-lnk {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--blue);
    text-decoration: none;
}

/* ── Bar chart ── */
.bar-chart { display: flex; flex-direction: column; gap: 6px; }
.bar-row { display: flex; align-items: center; gap: 7px; }
.bar-lbl {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--dim);
    width: 90px;
    flex-shrink: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.bar-bg {
    flex: 1;
    height: 4px;
    background: var(--sf3);
    border-radius: 3px;
    overflow: hidden;
    min-width: 0;
}
.bar-fill {
    height: 100%;
    border-radius: 3px;
    background: linear-gradient(90deg, var(--teal), var(--blue));
}
.bar-n {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--mu);
    width: 18px;
    text-align: right;
    flex-shrink: 0;
}

/* ── Misc ── */
.sec-hdr {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.07em;
    color: var(--mu);
    text-transform: uppercase;
    padding: 5px 0;
    border-bottom: 1px solid var(--bd);
    margin-bottom: 11px;
}
.geo-note {
    background: rgba(96,165,250,0.06);
    border: 1px solid rgba(96,165,250,0.18);
    border-radius: 5px;
    padding: 6px 11px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: #93c5fd;
    letter-spacing: 0.04em;
    margin-bottom: 11px;
}
.drill-panel {
    background: var(--sf);
    border: 1px solid rgba(0,194,168,0.3);
    border-radius: 8px;
    padding: 14px;
    margin: 10px 0 14px;
}
.drill-title {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: var(--teal);
    margin-bottom: 11px;
}
.page-info {
    text-align: center;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--mu);
    padding: 5px;
}
.chat-user {
    background: var(--sf2);
    border: 1px solid var(--bd2);
    border-radius: 6px;
    padding: 10px 14px;
    margin: 7px 0;
    font-size: 13px;
    color: var(--tx);
    font-family: var(--font-sans);
    text-align: left;
}
.chat-bot {
    background: var(--sf);
    border: 1px solid var(--bd);
    border-radius: 2px 8px 8px 8px;
    padding: 12px 15px;
    margin: 3px 0 13px;
    font-size: 13px;
    color: var(--dim);
    font-family: var(--font-sans);
}
.chat-bot strong { color: var(--teal); }
.chat-err {
    background: rgba(248,113,113,0.06);
    border: 1px solid rgba(248,113,113,0.22);
    border-radius: 6px;
    padding: 9px 13px;
    font-size: 12px;
    color: #fca5a5;
    font-family: var(--font-mono);
    margin-bottom: 11px;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--bd) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--mu) !important;
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 10px 16px !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: var(--teal) !important;
    border-bottom-color: var(--teal) !important;
}

/* ── Buttons ── */
.stButton button {
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
    letter-spacing: 0.05em !important;
    border-radius: 5px !important;
    transition: all 0.18s !important;
}
/* Primary button — teal border + teal text on dark bg (readable on both browsers) */
/* Toggle buttons (Market signals / Competitive reference) — outlined teal */
.stButton button[kind="primary"] {
    background: rgba(0,194,168,0.12) !important;
    color: var(--teal) !important;
    border: 1.5px solid var(--teal) !important;
    font-weight: 600 !important;
}
.stButton button[kind="primary"]:hover {
    background: rgba(0,194,168,0.2) !important;
    transform: translateY(-1px) !important;
}
/* Secondary button — same base, dimmer border */
.stButton button[kind="secondary"] {
    background: var(--sf2) !important;
    color: var(--dim) !important;
    border: 1px solid var(--bd2) !important;
    text-align: left !important;
    white-space: normal !important;
    height: auto !important;
    line-height: 1.4 !important;
    padding-left: 12px !important;
    /* Edge: explicit flex alignment on the button itself */
    display: flex !important;
    align-items: flex-start !important;
    justify-content: flex-start !important;
}
/* Target every possible inner element Edge renders inside the button */
.stButton button[kind="secondary"] *,
.stButton button[kind="secondary"] p,
.stButton button[kind="secondary"] div,
.stButton button[kind="secondary"] span {
    text-align: left !important;
    margin: 0 !important;
    width: 100% !important;
}
.stButton > div > div > button[kind="secondary"] {
    justify-content: flex-start !important;
    align-items: flex-start !important;
}
.stButton > div > div > button[kind="secondary"] > div,
.stButton > div > div > button[kind="secondary"] > p {
    text-align: left !important;
    width: 100% !important;
}
.stButton button[kind="secondary"]:hover {
    border-color: var(--teal) !important;
    color: var(--teal) !important;
}

/* A1: Send button — solid teal, dark arrow, 21:1 contrast */
[data-testid="stForm"] button[kind="primaryFormSubmit"],
[data-testid="stForm"] button[kind="primary"],
[data-testid="stForm"] button[data-testid="baseButton-primaryFormSubmit"] {
    background: var(--teal) !important;
    color: #0d1421 !important;
    border: none !important;
    font-weight: 900 !important;
    font-family: var(--font-sans) !important;
    font-size: 16px !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    white-space: nowrap !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-width: 0 !important;
    padding: 0 8px !important;
}
[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover,
[data-testid="stForm"] button[kind="primary"]:hover {
    background: #00d9bb !important;
    color: #0d1421 !important;
}
/* Clear button (✕) — navy bg, muted text, red on hover, no wrapping */
[data-testid="stForm"] button[kind="secondaryFormSubmit"],
[data-testid="stForm"] button[kind="secondary"] {
    background: var(--sf2) !important;
    color: var(--dim) !important;
    border: 1px solid var(--bd2) !important;
    font-family: var(--font-sans) !important;
    font-size: 15px !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    white-space: nowrap !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-width: 0 !important;
    padding: 0 8px !important;
}
[data-testid="stForm"] button[kind="secondaryFormSubmit"]:hover,
[data-testid="stForm"] button[kind="secondary"]:hover {
    border-color: var(--red) !important;
    color: var(--red) !important;
}
div[data-testid="stExpander"] {
    background: var(--sf) !important;
    border: 1px solid var(--bd) !important;
    border-radius: 6px !important;
    margin-bottom: 6px !important;
}
div[data-testid="stExpander"] summary {
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
    color: var(--dim) !important;
}

/* ── Text input ── */
.stTextInput input {
    background: var(--sf2) !important;
    border: 1px solid var(--bd2) !important;
    color: var(--tx) !important;
    font-family: var(--font-sans) !important;
    font-size: 13px !important;
    border-radius: 6px !important;
}
.stTextInput input:focus {
    border-color: rgba(0,194,168,0.5) !important;
    box-shadow: 0 0 0 2px rgba(0,194,168,0.08) !important;
    outline: none !important;
}
/* B1: Remove all placeholder text — text input, number input, textarea
   All three vendor prefixes needed for Edge + Safari + standard */
.stTextInput input::placeholder,
.stTextInput textarea::placeholder,
input::placeholder,
textarea::placeholder                           { color: transparent !important; opacity: 0 !important; }
.stTextInput input::-webkit-input-placeholder,
.stTextInput textarea::-webkit-input-placeholder,
input::-webkit-input-placeholder,
textarea::-webkit-input-placeholder            { color: transparent !important; opacity: 0 !important; }
.stTextInput input::-ms-input-placeholder,
.stTextInput textarea::-ms-input-placeholder,
input::-ms-input-placeholder,
textarea::-ms-input-placeholder                { color: transparent !important; opacity: 0 !important; }
/* Ensure typed text in inputs stays fully legible */
.stTextInput input,
.stTextArea textarea {
    color: var(--tx) !important;
}

/* ── Typography ── */
.stMarkdown h1,
.stMarkdown h2,
.stMarkdown h3 {
    font-family: var(--font-serif) !important;
    color: var(--tx) !important;
}
p, li, .stMarkdown p {
    color: var(--dim) !important;
    font-family: var(--font-sans) !important;
}
hr { border-color: var(--bd) !important; margin: 13px 0 !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Divider ── */
[data-testid="stDivider"] { border-color: var(--bd) !important; }

/* ── Caption / st.caption ── */
[data-testid="stCaptionContainer"] p {
    color: var(--mu) !important;
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
}

/* ── st.info / warning ── */
[data-testid="stAlert"] {
    background: var(--sf2) !important;
    border: 1px solid var(--bd2) !important;
    color: var(--dim) !important;
    font-family: var(--font-sans) !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# DATA
# ─────────────────────────────────────────
import re as _re

def _dedup_key(s):
    entity = (s.get("entity") or "").lower().strip()
    url    = (s.get("url") or "").strip().rstrip("/")
    raw_signal = (s.get("key_signal") or "").lower()
    norm = _re.sub(r"[^a-z0-9 ]", " ", raw_signal)
    norm = _re.sub(r"\s+", " ", norm).strip()[:60]
    key_text = f"{entity}||{norm}"
    key_url  = f"{entity}||url:{url}" if url and not url.startswith("local://") else None
    return key_text, key_url


def _get_file_mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0


@st.cache_data(ttl=60)
def load_signals(_mtime=None):
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

signals = load_signals(_mtime=_get_file_mtime("extracted_signals.json"))

def parse_date(ds):
    if not ds: return None
    for s in [ds.strip(), ds[:25].strip()]:
        for fmt in (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S",
            "%d %b %Y",
            "%B %d, %Y",
        ):
            try:
                dt = datetime.strptime(s, fmt)
                return dt.replace(tzinfo=None)
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
    if "bank-product" in src or t in ("scrape-static", "scrape"): return "bank-product"
    return "news"

def geo_ok(signal, sel):
    if not sel: return True
    g  = signal.get("geography", "")
    ai = signal.get("asean_impact", g in ASEAN_ALL)
    for s in sel:
        if s == "ASEAN-Wide":
            if g == "ASEAN-Wide": return True
            if g in ASEAN_COUNTRIES: return True
            if ai: return True
        else:
            if g == s: return True
    return False


def _canonical_entity(name):
    name = name.strip()
    aliases = {
        "j.p. morgan chase":          "J.P. Morgan",
        "jp morgan chase":            "J.P. Morgan",
        "j.p.morgan":                 "J.P. Morgan",
        "jpmorgan":                   "J.P. Morgan",
        "jpmorgan chase":             "J.P. Morgan",
        "j.p. morgan chase & co.":    "J.P. Morgan",
        "mobifone digital payments joint stock company": "MobiFone Digital Payments",
        "mobifone digital payments jsc":                 "MobiFone Digital Payments",
    }
    return aliases.get(name.lower(), name)

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
    src_html = (f'<a class="sc-src-lnk" href="{url}" target="_blank">&#8599; Source</a>'
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
        <div class="sc-ft"><span class="sc-dt">&#128197; {dt or '—'}</span>{src_html}</div>
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
        f'<div class="bar-row"><div class="bar-lbl">{l[:14]}</div>'
        f'<div class="bar-bg"><div class="bar-fill" style="width:{int(c/mx*100) if mx else 0}%">'
        f'</div></div><div class="bar-n">{c}</div></div>'
        for l,c in items)
    return f'<div class="bar-chart">{rows}</div>'

# ─────────────────────────────────────────
# FULL-WIDTH HEADER
# ─────────────────────────────────────────
st.markdown("""
<div class="main-hdr">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
        <div>
            <div class="main-title">ASEAN Cash <em>Intelligence</em></div>
            <div class="main-sub">Market &amp; Transaction Intelligence System &middot; ASEAN Cash Management</div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
            <div style="background:var(--teal);color:#000;font-family:var(--font-mono);
                 font-size:10px;font-weight:700;letter-spacing:0.18em;padding:4px 12px;
                 border-radius:3px;text-transform:uppercase">MANTIS</div>
            <div style="font-family:var(--font-mono);font-size:10px;
                 color:var(--mu);letter-spacing:0.07em;text-transform:uppercase">
                 Intelligence Platform</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────
sidebar_col, main_col = st.columns([1.2, 3.6], gap="small")

# ═══════════════════════════════════════════
# CUSTOM SIDEBAR COLUMN
# ═══════════════════════════════════════════
with sidebar_col:
    newest, _, is_stale = freshness(signals)
    dot_col = "#f87171" if is_stale else "#00c2a8"
    icon    = "⚠" if is_stale else "✓"
    info    = ("Stale — run pipeline" if is_stale
               else f"Fresh · {newest.strftime('%d %b %Y') if newest else 'today'} · {len(signals)} signals")
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:7px;padding:7px 4px 10px;
         font-family:var(--font-mono);font-size:11px;
         letter-spacing:0.04em;color:{dot_col};border-bottom:1px solid var(--bd);
         margin-bottom:8px">
        <div style="width:6px;height:6px;border-radius:50%;
             background:{dot_col};flex-shrink:0"></div>
        <span>{icon} {info}</span>
    </div>
    """, unsafe_allow_html=True)

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
        "Source Type", options=["news","pdf","consultant","regulatory","bank-product"],
        key="f_src", placeholder="All sources"
    )
    comp_opts = sorted(set(
        _canonical_entity(s.get("entity","").strip())
        for s in signals if s.get("entity","").strip()
    ))
    competitor_filter = st.multiselect(
        "Competitor / Regulator", options=comp_opts, key="f_comp",
        placeholder="All competitors & regulators"
    )
    min_score = st.slider("Min Score", min_value=1, max_value=5, value=1, key="f_score")

    st.divider()

    st.markdown("""
    <div style="font-family:var(--font-mono);font-size:11px;
         color:var(--mu);line-height:2">
        <div style="font-size:10px;letter-spacing:0.07em;text-transform:uppercase;
             margin-bottom:4px;color:var(--mu)">Sources active</div>
        <span style="color:var(--teal)">✓</span> TFG &middot; Finextra &middot; Paypers<br>
        <span style="color:var(--teal)">✓</span> Fintech News SG/ID/MY/PH<br>
        <span style="color:var(--teal)">✓</span> Asian Banker &middot; TechInAsia<br>
        <span style="color:var(--teal)">✓</span> MAS &middot; BNM &middot; BSP<br>
        <span style="color:var(--teal)">✓</span> DBS &middot; OCBC &middot; HSBC &middot; JPM<br>
        <span style="color:var(--teal)">✓</span> McKinsey &middot; KPMG &middot; EY &middot; OW<br>
        <span style="color:var(--teal)">✓</span> BIS &middot; ADB &middot; IMF &middot; SWIFT
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────
# FILTER
# ─────────────────────────────────────────
cutoff = datetime.now() - timedelta(days=45)

TRADE_FINANCE_ONLY_TERMS = {
    "bill of lading", "bills of lading", "letter of credit", "letters of credit",
    "documentary collection", "documentary collections", "trade document",
    "electronic trade document", "digital trade facilitation",
    "trade facilitation bill", "trade finance bill",
}

def _is_pure_trade_finance(s):
    combined = (
        (s.get("key_signal") or "") + " " +
        (s.get("so_what") or "")
    ).lower()
    has_tf_term = any(term in combined for term in TRADE_FINANCE_ONLY_TERMS)
    if not has_tf_term:
        return False
    redeeming = [
        "cash management", "treasury", "liquidity", "payment rail",
        "real-time payment", "virtual account", "api banking",
        "open banking", "digital payment", "cross-border payment",
        "settlement", "collection", "disbursement", "paynow",
        "promptpay", "duitnow", "qris", "upi", "swift gpi",
    ]
    has_redeeming = any(r in combined for r in redeeming)
    return not has_redeeming


def apply_filters(sigs):
    out  = []
    seen = set()
    for s in sigs:
        d = parse_date(s.get("date",""))
        if d and d < cutoff: continue
        if _is_pure_trade_finance(s): continue
        if not geo_ok(s, geo_filter): continue
        if product_filter    and s.get("product_area","").strip() not in product_filter:    continue
        if type_filter       and s.get("signal_type","").strip()  not in type_filter:       continue
        if source_filter     and src_tag(s) not in source_filter:                           continue
        if competitor_filter:
            raw_entity = s.get("entity","").strip()
            canon_entity = _canonical_entity(raw_entity)
            if canon_entity not in competitor_filter:
                continue
        if s.get("relevance_score",0) < min_score:                                          continue
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

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "◈  Overview", "⚡  Signals", "◎  Ask Intelligence", "📚  Intelligence Library", "▤  Weekly Digest"
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
                <div class="msub">Last 45 days</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            is_hi = active_drill == "high"
            st.markdown(f"""<div class="mcard blue {'active' if is_hi else ''}">
                <div class="mlbl">High Priority</div>
                <div class="mval" style="color:var(--blue)">{len(hi_list)}</div>
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
                <div class="mval" style="color:var(--pur)">{len(pd_list)}</div>
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
            st.markdown(f'<div class="geo-note" style="margin-top:10px">&#127981; {" · ".join(notes)}</div>',
                unsafe_allow_html=True)

        dm = st.session_state.get("drill_mode")
        if dm:
            cfg = {"high":("High Priority Signals — Score 4–5", hi_list, "dp_high"),
                   "pdf": ("PDF & Consultant Reports",           pd_list, "dp_pdf"),
                   "reg": ("Regulatory Signals",                 rg_list, "dp_reg")}
            if dm in cfg:
                label, items, pkey = cfg[dm]
                st.markdown(f'<div class="drill-panel"><div class="drill-title">&#9656; {label}</div>',
                    unsafe_allow_html=True)
                paginated(items, pkey, label.lower())
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        lc, rc = st.columns([3,2])

        with lc:
            st.markdown('<div class="sec-hdr">&#128293; Top Signals This Period</div>', unsafe_allow_html=True)
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

    # ══════════════════════════════════════════════════════════════════
    # TAB 2 — SIGNALS
    # ══════════════════════════════════════════════════════════════════
    with tab2:
        dated_fs   = [s for s in fs if s.get("date","").strip()]
        undated_fs = [s for s in fs if not s.get("date","").strip()]

        if "sig_view" not in st.session_state:
            st.session_state["sig_view"] = "market"

        tc1, tc2, tc3 = st.columns([3, 1.5, 1])
        with tc1:
            tb1, tb2 = st.columns(2)
            with tb1:
                mkt_label = f"Market signals  ({len(dated_fs)})"
                if st.button(mkt_label, key="tog_market",
                    type="primary" if st.session_state["sig_view"]=="market" else "secondary",
                    use_container_width=True):
                    st.session_state["sig_view"] = "market"
                    st.session_state["sig_page"] = 1
                    st.rerun()
            with tb2:
                ref_label = f"Competitive reference  ({len(undated_fs)})"
                if st.button(ref_label, key="tog_ref",
                    type="primary" if st.session_state["sig_view"]=="ref" else "secondary",
                    use_container_width=True):
                    st.session_state["sig_view"] = "ref"
                    st.session_state["ref_page"] = 1
                    st.rerun()
        with tc3:
            sort_by = st.selectbox("sort_sig", options=["Relevance","Date","Entity","Geography"],
                label_visibility="collapsed")

        if geo_filter:
            gn = ["ASEAN-Wide (all markets + ASEAN impact)" if g=="ASEAN-Wide" else f"{g} only" for g in geo_filter]
            st.markdown(f'<div class="geo-note">&#127981; {" · ".join(gn)}</div>', unsafe_allow_html=True)

        if st.session_state["sig_view"] == "market":
            st.markdown('''<div style="font-family:var(--font-mono);font-size:11px;
                letter-spacing:0.05em;color:var(--mu);padding:5px 0 10px">
                Dated signals only &middot; last 45 days &middot; sorted by relevance</div>''',
                unsafe_allow_html=True)

            disp_dated = dated_fs
            if sort_by == "Date":        disp_dated = sorted(dated_fs, key=lambda x:x.get("date",""), reverse=True)
            elif sort_by == "Entity":    disp_dated = sorted(dated_fs, key=lambda x:x.get("entity",""))
            elif sort_by == "Geography": disp_dated = sorted(dated_fs, key=lambda x:x.get("geography",""))

            if not disp_dated:
                st.markdown("""<div style="text-align:center;padding:40px 20px;color:var(--mu)">
                    <div style="font-size:22px;margin-bottom:8px">&#9677;</div>
                    <div style="font-family:var(--font-mono);font-size:11px;letter-spacing:0.1em">
                        NO DATED SIGNALS MATCH YOUR FILTERS</div></div>""", unsafe_allow_html=True)
            else:
                paginated(disp_dated, "sig_page", "market signals")

        else:
            st.markdown(
                '''<div style="font-family:var(--font-mono);font-size:11px;
                letter-spacing:0.05em;color:var(--pur);padding:5px 0 4px">
                Bank product pages, consultant PDFs, research reports &middot; no publish date &middot; not in digest</div>
                <div style="font-family:var(--font-mono);font-size:11px;
                color:var(--mu);padding-bottom:10px">
                For the full library view, see the &#128218; Intelligence Library tab &#8594;</div>''',
                unsafe_allow_html=True)

            disp_undated = undated_fs
            if sort_by == "Entity":    disp_undated = sorted(undated_fs, key=lambda x:x.get("entity",""))
            elif sort_by == "Geography": disp_undated = sorted(undated_fs, key=lambda x:x.get("geography",""))

            if not disp_undated:
                st.markdown('''<div style="text-align:center;padding:40px 20px;color:var(--mu)">
                    <div style="font-size:22px;margin-bottom:8px">&#9677;</div>
                    <div style="font-family:var(--font-mono);font-size:11px;letter-spacing:0.1em">
                        NO REFERENCE ITEMS MATCH YOUR FILTERS</div></div>''', unsafe_allow_html=True)
            else:
                paginated(disp_undated, "ref_page", "reference items")

    # ═══════════════════════
    # TAB 3 — ASK INTELLIGENCE
    # ═══════════════════════
    with tab3:
        fresh_sigs = sorted(
            [s for s in signals if (
                not s.get("date","").strip() or
                (lambda d: d is not None and d >= cutoff)(parse_date(s.get("date","")))
            )],
            key=lambda x:x.get("relevance_score",0), reverse=True)
        dated_chat  = [s for s in fresh_sigs if s.get("date","").strip()]
        undated_chat = [s for s in fresh_sigs if not s.get("date","").strip()]

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        st.markdown(f"""
        <div style="margin-bottom:10px">
            <div style="font-family:var(--font-serif);font-size:17px;font-weight:700;
                 color:var(--tx);margin-bottom:2px">Ask Intelligence</div>
            <div style="font-family:var(--font-sans);font-size:12px;color:var(--mu)">
                {len(dated_chat)} market signals (last 45 days) + {len(undated_chat)} competitive reference items.</div>
        </div>""", unsafe_allow_html=True)

        with st.form("chat_form", clear_on_submit=True):
            ci1, ci2, ci3 = st.columns([11, 1.4, 1.4])
            with ci1:
                user_input = st.text_input("chat_q",
                    placeholder="",
                    label_visibility="collapsed", key="chat_input")
            with ci2:
                send = st.form_submit_button("\u25BA", type="primary",
                    use_container_width=True)
            with ci3:
                clear = st.form_submit_button("\u2715", use_container_width=True,
                    help="Clear conversation")

        if clear:
            st.session_state.chat_history = []; st.rerun()

        if send and user_input.strip():
            st.session_state.chat_history.insert(0, {
                "role":"user","content":user_input.strip(),
                "answer":None,"sources":None,"error":None})
            st.rerun()

        BLOCKED_ENTITIES = {"standard chartered", "stanchart", "sc", "standard chartered bank"}

        def build_presets(sigs):
            if not sigs:
                return []
            ent, prod, geos = {}, {}, {}
            for s in sigs:
                e = s.get("entity","").strip()
                p = s.get("product_area","").strip()
                g = s.get("geography","").strip()
                if e and e.lower() not in BLOCKED_ENTITIES:
                    ent[e] = ent.get(e,0) + 1
                if p: prod[p] = prod.get(p,0) + 1
                if g: geos[g] = geos.get(g,0) + 1

            cands = []
            top_geos = [g for g,_ in sorted(geos.items(),key=lambda x:x[1],reverse=True)
                        if g not in ("Global",) ][:1]
            if top_geos:
                g = top_geos[0]
                if g == "ASEAN-Wide":
                    cands.append("What are the biggest cash management developments across ASEAN this month?")
                else:
                    cands.append(f"What are the key cash management signals coming out of {g}?")

            top_prods = [p for p,_ in sorted(prod.items(),key=lambda x:x[1],reverse=True)][:1]
            if top_prods:
                cands.append(f"Summarise the latest signals on {top_prods[0]} in ASEAN.")

            if len(top_prods) >= 2 or len(prod) >= 2:
                second = [p for p,_ in sorted(prod.items(),key=lambda x:x[1],reverse=True)
                          if p != (top_prods[0] if top_prods else "")][0:1]
                if second:
                    cands.append(f"What is happening in {second[0]} across ASEAN banks?")

            top_ents = [e for e,_ in sorted(ent.items(),key=lambda x:x[1],reverse=True)
                        if e.lower() not in BLOCKED_ENTITIES][:1]
            if top_ents:
                cands.append(f"What is {top_ents[0]} doing in ASEAN cash management?")

            has_reg = any(
                s.get("signal_type","").lower() == "regulatory update" or
                s.get("product_area","").lower() == "regulatory"
                for s in sigs
            )
            if has_reg:
                cands.append("What regulatory changes in ASEAN should transaction banks act on?")
            else:
                cands.append("What are the most important market trends in ASEAN cash management right now?")

            has_innov = any(
                s.get("product_area","") in ("Innovation","Payments & Collections")
                for s in sigs
            )
            if has_innov:
                cands.append("What are the latest real-time payment and innovation signals in ASEAN?")
            else:
                cands.append("Which banks are most active in ASEAN cash management this month?")

            return cands[:6]

        def _preset_tag(q):
            q = q.lower()
            if any(w in q for w in ("regulat","compliance","mandate","policy")):
                return ("REGULATORY", "var(--pur)")
            if any(w in q for w in ("innovation","real-time","api","digital")):
                return ("INNOVATION", "var(--ora)")
            if any(w in q for w in ("what is","bca","dbs","hsbc","jpmorgan",
                                     "deutsche","bangkok bank","doing in")):
                return ("COMPETITOR", "var(--teal)")
            return ("MARKET", "var(--blue)")

        presets = build_presets(fresh_sigs)

        for pi, pq in enumerate(presets):
            if st.session_state.get(f"_preset_clicked_{pi}"):
                st.session_state[f"_preset_clicked_{pi}"] = False
                st.session_state.chat_history.insert(0, {
                    "role":"user","content":pq,
                    "answer":None,"sources":None,"error":None})
                st.rerun()

        if presets and not st.session_state.chat_history:
            st.markdown('''<div style="font-family:var(--font-mono);font-size:11px;
                letter-spacing:0.07em;text-transform:uppercase;color:var(--mu);
                margin-top:12px;margin-bottom:6px">
                Suggested queries — click any to ask</div>''', unsafe_allow_html=True)

            pairs = list(zip(presets[::2], presets[1::2]))
            if len(presets) % 2:
                pairs.append((presets[-1], None))

            for row_i, (left_q, right_q) in enumerate(pairs):
                col_a, col_b = st.columns(2)
                for col, q in [(col_a, left_q), (col_b, right_q)]:
                    if q is None:
                        continue
                    pi = presets.index(q)
                    tag_label, tag_color = _preset_tag(q)
                    with col:
                        st.markdown(
                            f'<div style="font-family:var(--font-mono);'
                            f'font-size:10px;font-weight:600;letter-spacing:0.07em;'
                            f'color:{tag_color};margin-bottom:3px;text-transform:uppercase">'+
                            tag_label+'</div>',
                            unsafe_allow_html=True)
                        if st.button(q, key=f"preset_{pi}",
                                     use_container_width=True, type="secondary"):
                            st.session_state.chat_history.insert(0, {
                                "role":"user","content":q,
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
                                model="claude-sonnet-4-5", max_tokens=2500,
                                messages=[{"role":"user","content":(
                                    "You are a senior transaction banking analyst covering ASEAN Cash Management.\n"
                                    "Answer using the intelligence signals below. Two types are included:\n"
                                    "1. DATED signals (last 45 days) — recent news, regulatory updates, product launches.\n"
                                    "2. UNDATED signals — evergreen reference: bank product pages, consultant PDFs, research reports. No date but always valid context.\n"
                                    "Signals marked ASEAN Impact: True are relevant even if non-ASEAN origin.\n"
                                    "Be direct, cite entities, geographies, and dates where available.\n"
                                    "Weight consultant/PDF signals higher. Flag undated signals as reference context.\n"
                                    "End with: 'Implication for Transaction Banks:' on a new line.\n"
                                    "If insufficient signals, say so clearly.\n\n"
                                    f"Question: {msg['content']}\n\nSignals:\n{ctx[:100000]}"
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
                st.markdown(f'<div class="chat-err">&#9888; {msg["error"]}</div>', unsafe_allow_html=True)
            elif msg.get("answer"):
                st.markdown(f'<div class="chat-bot">{msg["answer"]}</div>', unsafe_allow_html=True)
                srcs = msg.get("sources") or []
                if srcs:
                    with st.expander("&#128204; Signals referenced", expanded=False):
                        for r in srcs:
                            icon = "&#128196;" if "pdf" in src_tag(r) else "&#128240;"
                            g = r.get("geography","")
                            ai_n = " &#10230; ASEAN" if g not in ASEAN_ALL and r.get("asean_impact") else ""
                            url = r.get("url","")
                            ul = f" · [source]({url})" if url and not url.startswith("local://") else ""
                            st.caption(f"{icon} [{r.get('date','')[:10]}] **{r.get('entity','')}** "
                                       f"({g}{ai_n}) — {r.get('key_signal','')[:80]}{ul}")
            elif msg.get("answer") is None and msg.get("error") is None:
                st.markdown('<div class="chat-bot" style="color:var(--mu)">Thinking…</div>',
                    unsafe_allow_html=True)

        if not fresh_sigs:
            st.warning("No signals available. Run the pipeline first.")

    # ═══════════════════════════════
    # TAB 4 — INTELLIGENCE LIBRARY
    # ═══════════════════════════════
    with tab4:
        all_undated = sorted(
            [s for s in signals if not s.get("date","").strip()],
            key=lambda x: x.get("relevance_score",0), reverse=True
        )
        lib_product  = [s for s in all_undated
                        if s.get("source_type","") == "bank-product"
                        or s.get("type","") in ("scrape-static","scrape")]
        lib_research = [s for s in all_undated if s not in lib_product]

        st.markdown("""
        <div style="margin-bottom:14px">
            <div style="font-family:var(--font-serif);font-size:17px;font-weight:700;
                 color:var(--tx);margin-bottom:2px">Intelligence Library</div>
            <div style="font-family:var(--font-sans);font-size:12px;color:var(--mu)">
                Evergreen reference content — no publish date. Use for context before meetings
                or when building competitive briefs. Also included in Ask Intelligence answers.</div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f'''<div style="display:flex;align-items:center;justify-content:space-between;
            font-family:var(--font-mono);font-size:11px;letter-spacing:0.07em;
            text-transform:uppercase;color:var(--ora);
            padding:8px 0 6px;border-bottom:1px solid var(--bd);margin-bottom:12px">
            <span>&#127970; Competitor product pages</span>
            <span style="background:rgba(245,158,11,0.12);color:var(--ora);padding:2px 8px;
                border-radius:3px;font-size:10px">{len(lib_product)} items</span>
        </div>''', unsafe_allow_html=True)

        if lib_product:
            for s in lib_product:
                url    = s.get("url","")
                link   = f'<a class="sc-src-lnk" href="{url}" target="_blank">&#8599; View</a>' if url and not url.startswith("local://") else ""
                entity = s.get("entity","") or ""
                geo    = s.get("geography","") or ""
                sig    = (s.get("key_signal","") or "")[:120]
                sw     = (s.get("so_what","") or "")[:120]
                st.markdown(f'''<div style="background:var(--sf2);border:1px solid var(--bd);
                    border-left:3px solid var(--ora);border-radius:6px;
                    padding:10px 12px;margin-bottom:7px">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:5px">
                        <div>
                            <span style="font-family:var(--font-mono);font-size:11px;
                                background:rgba(245,158,11,0.12);color:var(--ora);
                                padding:2px 6px;border-radius:2px;margin-right:5px">{entity}</span>
                            <span style="font-family:var(--font-mono);font-size:11px;
                                color:var(--mu)">{geo}</span>
                        </div>
                        {link}
                    </div>
                    <div style="font-size:12px;font-weight:500;color:var(--tx);
                        line-height:1.45;margin-bottom:4px">{sig}</div>
                    <div style="font-size:12px;color:var(--dim);line-height:1.5">
                        <span style="color:var(--teal);font-weight:500">So what:</span> {sw}</div>
                </div>''', unsafe_allow_html=True)
        else:
            st.info("No competitor product pages found. Run the pipeline to populate.")

        st.markdown(f'''<div style="display:flex;align-items:center;justify-content:space-between;
            font-family:var(--font-mono);font-size:11px;letter-spacing:0.07em;
            text-transform:uppercase;color:var(--pur);
            padding:8px 0 6px;border-bottom:1px solid var(--bd);margin:20px 0 12px">
            <span>&#128196; Research reports &amp; PDFs</span>
            <span style="background:rgba(167,139,250,0.12);color:var(--pur);padding:2px 8px;
                border-radius:3px;font-size:10px">{len(lib_research)} items</span>
        </div>''', unsafe_allow_html=True)

        if lib_research:
            for s in lib_research:
                url    = s.get("url","")
                link   = f'<a class="sc-src-lnk" href="{url}" target="_blank">&#8599; View</a>' if url and not url.startswith("local://") else ""
                entity = s.get("entity","") or (s.get("source","") or "")[:40]
                geo    = s.get("geography","") or ""
                sig    = (s.get("key_signal","") or "")[:120]
                sw     = (s.get("so_what","") or "")[:120]
                st.markdown(f'''<div style="background:var(--sf2);border:1px solid var(--bd);
                    border-left:3px solid var(--pur);border-radius:6px;
                    padding:10px 12px;margin-bottom:7px">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:5px">
                        <div>
                            <span style="font-family:var(--font-mono);font-size:11px;
                                background:rgba(167,139,250,0.12);color:var(--pur);
                                padding:2px 6px;border-radius:2px;margin-right:5px">{entity}</span>
                            <span style="font-family:var(--font-mono);font-size:11px;
                                color:var(--mu)">{geo}</span>
                        </div>
                        {link}
                    </div>
                    <div style="font-size:12px;font-weight:500;color:var(--tx);
                        line-height:1.45;margin-bottom:4px">{sig}</div>
                    <div style="font-size:12px;color:var(--dim);line-height:1.5">
                        <span style="color:var(--teal);font-weight:500">So what:</span> {sw}</div>
                </div>''', unsafe_allow_html=True)
        else:
            st.info("No research reports found. Add PDF URLs to sources.py or drop PDFs in documents/ folder.")

    # ═══════════════════════
    # TAB 5 — WEEKLY DIGEST
    # ═══════════════════════
    with tab5:
        d1, d2 = st.columns([4,1])
        with d1:
            st.markdown("""
            <div style="font-family:var(--font-serif);font-size:17px;font-weight:700;
                 color:var(--tx);margin-bottom:2px">Weekly Intelligence Digest</div>
            <div style="font-family:var(--font-sans);font-size:12px;color:var(--mu)">
                Auto-generated from the last 45 days &middot; Includes consultant reports and PDFs</div>
            """, unsafe_allow_html=True)

        dfiles = sorted(glob.glob("digest_*.md"), reverse=True)
        if dfiles:
            try:
                dd   = datetime.strptime(dfiles[0].replace("digest_","").replace(".md",""),"%Y%m%d")
                dold = (datetime.now()-dd).days
            except: dd=None; dold=0
            with d2:
                if dold>7:
                    st.markdown(f'<div style="background:rgba(248,113,113,0.08);border:1px solid '
                        f'rgba(248,113,113,0.22);border-radius:5px;padding:7px 11px;'
                        f'font-family:var(--font-mono);font-size:11px;'
                        f'color:var(--red);margin-top:4px">&#9888; {dold}d old</div>', unsafe_allow_html=True)

            sf = (st.selectbox("dig_sel", options=dfiles,
                  format_func=lambda x:x.replace("digest_","").replace(".md",""),
                  label_visibility="collapsed") if len(dfiles)>1 else dfiles[0])
            with open(sf) as f: dt = f.read()
            st.caption(f"Generated {dd.strftime('%d %B %Y')} · {dold} days ago" if dd else sf)
            st.divider()

            scols={"competitor":"var(--teal)","regulatory":"var(--blue)","consultant":"var(--pur)",
                   "research":"var(--pur)","innovation":"var(--ora)","transaction":"var(--teal)",
                   "watch":"var(--red)"}
            for sec in dt.split("###")[1:]:
                lines=sec.strip().split("\n")
                if not lines: continue
                title=lines[0].strip(); body="\n".join(lines[1:]).strip()
                color="var(--teal)"
                for k,v in scols.items():
                    if k.lower() in title.lower(): color=v; break
                st.markdown(f'<div style="font-family:var(--font-mono);font-size:11px;'
                    f'letter-spacing:0.07em;text-transform:uppercase;color:{color};'
                    f'margin-top:8px;margin-bottom:6px;padding-bottom:5px;'
                    f'border-bottom:1px solid var(--bd)">{title}</div>', unsafe_allow_html=True)
                bullets=[l.lstrip("-•").strip() for l in body.split("\n") if l.strip().startswith(("-","•"))]
                if bullets:
                    for b in bullets: st.markdown(f"— {b}")
                else:
                    st.markdown(body)
                st.markdown("<div style='margin-bottom:13px'></div>", unsafe_allow_html=True)
            st.divider()
            st.download_button("&#11015; Download Digest", data=dt, file_name=sf, mime="text/markdown")
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