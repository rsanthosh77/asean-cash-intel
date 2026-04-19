import anthropic
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
client = anthropic.Anthropic()

def generate_digest(signals):

    cutoff = datetime.now() - timedelta(days=45)
    today  = datetime.now().date()

    def _parse_date(ds):
        """Parse any date format, always return timezone-naive datetime or None."""
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
                    return datetime.strptime(s, fmt).replace(tzinfo=None)
                except Exception:
                    pass
        return None

    recent = []
    excluded_static = 0
    for s in signals:
        date_str = s.get("date", "")
        sig_type = s.get("type", "")

        # Empty date = genuinely undated (PDFs, static pages after fix)
        # Include them — extract.py will judge relevance
        if not date_str:
            recent.append(s)
            continue

        d = _parse_date(date_str)
        if d is None:
            # Unparseable date — include conservatively
            recent.append(s)
            continue

        # Exclude signals where the date is today AND type is static/pdf
        # These are old content re-stamped by ingest.py (pre-fix runs)
        is_synthetic_date = (
            d.date() == today and
            sig_type in ("scrape-static", "scrape", "pdf",
                         "pdf-direct", "pdf-local")
        )
        if is_synthetic_date:
            excluded_static += 1
            continue

        if d >= cutoff:
            recent.append(s)

    if excluded_static:
        print(f"   ⚠️  Excluded {excluded_static} signals with synthetic today-date "
              f"(old static pages re-stamped by ingest — re-run ingest.py to fix)")

    if not recent:
        print("⚠️  No signals within last 30 days — using all signals")
        recent = signals

    # Sort by relevance score descending, take top 30
    top_signals = sorted(
        recent,
        key=lambda x: x.get("relevance_score", 0),
        reverse=True
    )[:30]

    # Deduplicate by entity + key_signal fingerprint
    seen = set()
    deduped = []
    for s in top_signals:
        key = f"{(s.get('entity') or '').lower()}||{(s.get('key_signal') or '').lower()[:80]}"
        if key not in seen:
            seen.add(key)
            deduped.append(s)
    top_signals = deduped

    # Build signal text — include source, date, and labels
    signals_text = ""
    for s in top_signals:
        source_type = s.get("source_type", s.get("type", "news"))
        source_label = ""
        if "pdf" in source_type or "pdf" in s.get("type", ""):
            source_label = "[PDF REPORT] "
        elif "consultant" in source_type:
            source_label = "[CONSULTANT REPORT] "
        elif "regulatory" in source_type or s.get("signal_type") == "Regulatory Update":
            source_label = "[REGULATORY] "

        # Date handling
        date_raw = s.get("date", "")
        date_display = date_raw[:10] if date_raw else ""
        date_note = " [DATE UNVERIFIED]" if not date_raw else ""

        # Source URL
        url = s.get("url", "")
        if url and url.startswith("local://"):
            url = ""

        signals_text += (
            f"\n---\n"
            f"{source_label}"
            f"Entity: {s.get('entity', '')}\n"
            f"Geography: {s.get('geography', '')}\n"
            f"Product Area: {s.get('product_area', '')}\n"
            f"Signal Type: {s.get('signal_type', '')}\n"
            f"Relevance Score: {s.get('relevance_score', '')}\n"
            f"Date: {date_display}{date_note}\n"
            f"Source URL: {url if url else 'Not available'}\n"
            f"Key Signal: {s.get('key_signal', '')}\n"
            f"So What: {s.get('so_what', '')}\n"
        )

    prompt = f"""
You are a senior transaction banking analyst.
Write a crisp weekly intelligence digest for an ASEAN Cash Management
product and innovation team at a leading transaction bank.

The signals include news articles, regulatory publications, and research
reports from consultant firms (McKinsey, KPMG, EY, Deloitte, Oliver Wyman,
BCG, Accenture). Signals labelled [PDF REPORT] or [CONSULTANT REPORT]
carry higher analytical weight and should be cited explicitly by firm name.
Signals labelled [REGULATORY] are compliance-relevant and should be
flagged with urgency.

IMPORTANT FORMATTING RULES FOR EACH BULLET:
- Each bullet must be exactly 2 sentences
- Sentence 1: the intelligence finding — be direct and specific
- Sentence 2: cite the source like this: (Source: [Entity], [Date], [URL])
  If date is marked [DATE UNVERIFIED] write: (Source: [Entity], date unverified — treat with caution, [URL])
  If URL is "Not available" omit the URL from the citation
- Lead competitor bullets with the entity name in bold e.g. **DBS**

Format the digest EXACTLY like this — no deviation:

## ASEAN Cash Management Intelligence — Week of {datetime.now().strftime('%d %B %Y')}

### 🏦 Competitor Moves
[3 bullet points — competitor actions in ASEAN cash management]

### 🏛️ Regulatory Pulse
[2 bullet points — regulatory signals across ASEAN markets, flag compliance deadlines]

### 📊 Consultant & Research Insights
[2 bullet points — cite firm name explicitly, note if date unverified]

### 💡 Innovation Signals
[2 bullet points — fintechs, AI in banking, digital assets, real-time rails, infrastructure shifts]

### ⚡ So What for Transaction Banks
[3 specific and actionable implications for transaction banks in ASEAN Cash Management,
each naming a specific product area or market]

### 📌 Watch Next Week
[2 things worth monitoring — regulatory deadlines, expected announcements, conference signals]

Rules:
- Prioritise signals with higher relevance scores
- Do not invent facts not present in the signals
- If a section has insufficient signals, say so briefly and move on
- For signals with no date, note that the timing is unverified

Signals:
{signals_text}
"""

    print("\n── Generating weekly digest ──")
    print(f"   Using {len(top_signals)} signals ({len(recent)} total in window)")

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )

    digest = response.content[0].text.strip()

    filename = f"digest_{datetime.now().strftime('%Y%m%d')}.md"
    with open(filename, "w") as f:
        f.write(digest)

    print(f"\n✅ Done — digest saved to {filename}")
    print(f"\n{'='*60}")
    print(digest)
    print(f"{'='*60}\n")

    return digest

if __name__ == "__main__":
    with open("extracted_signals.json") as f:
        signals = json.load(f)
    if not signals:
        print("⚠️  extracted_signals.json is empty — run extract.py first")
    else:
        print(f"── Found {len(signals)} signals ──")
        generate_digest(signals)