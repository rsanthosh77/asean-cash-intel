import anthropic
import json
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

EXTRACTION_PROMPT = """
You are an intelligence analyst for a leading transaction bank,
focused on Cash Management in ASEAN.

Analyze the content below and extract structured intelligence.
The content may come from a news article, a scraped web page, a PDF report
from a consultant firm (McKinsey, KPMG, Deloitte, PwC, EY, Oliver Wyman,
BCG, Accenture), a regulatory paper, or a bank product page.

Return ONLY valid JSON in this exact format, with no other text:

{{
  "relevant": true or false,
  "entity": "name of bank, regulator, consultant firm, or fintech mentioned",
  "geography": "see geography rules below",
  "asean_impact": true or false,
  "product_area": "see product area rules below",
  "signal_type": "one of: Product Launch | Partnership | Regulatory Update | Pricing Signal | Talent/Hiring | Market Trend | Consultant Report | Research Finding | Other",
  "key_signal": "one sentence — the single most important competitive or market insight",
  "so_what": "one sentence — why this matters for transaction banks operating in ASEAN Cash Management",
  "relevance_score": a number from 1 to 5,
  "source_type": "one of: news | consultant-report | regulatory | bank-product | pdf | other"
}}

PRODUCT AREA RULES — assign the single best-matching category:

"Liquidity Management"
  → Notional pooling, cash concentration, sweeping, intraday liquidity,
    liquidity forecasting, working capital optimisation, overdraft facilities,
    investment of surplus cash, short-term funding

"Payments & Collections"
  → Any payment rail or scheme: SWIFT, SWIFT gpi, SEPA, ACH, Faster Payments,
    PayNow, PromptPay, DuitNow, QRIS, UPI, GoPay, OVO, GrabPay, FPS,
    real-time payments, instant payments, bulk payments, payroll, collections,
    receivables, direct debit, standing orders, payment hubs, payment factories,
    cross-border payments, correspondent banking, remittances

"Virtual Accounts"
  → Virtual account management, virtual IBANs, virtual account structures,
    multi-currency virtual accounts, e-commerce collection via virtual accounts,
    reconciliation via virtual accounts

"API Banking"
  → Any mention of: API, APIs, open banking, open finance, banking-as-a-service,
    BaaS, embedded banking, embedded finance, ERP integration, SAP integration,
    Oracle integration, host-to-host connectivity, ISO 20022, SWIFT MX,
    webhook, developer portal, SDK, fintech connectivity, third-party integration,
    programmable money, smart contracts for banking

"FX & Hedging"
  → Foreign exchange, FX, currency conversion, hedging, forwards, swaps,
    multi-currency accounts, currency risk, FX overlay, cross-currency pooling

"Regulatory"
  → Central bank guidelines, compliance requirements, AML, KYC, sanctions,
    data localisation, open banking mandates, licensing, regulatory sandbox,
    consultation papers, SNAP API mandate, reporting requirements

"Innovation"
  → ANY of the following topics MUST be tagged Innovation:
    - Digital assets, tokenisation, tokenized deposits, stablecoins, CBDC,
      mBridge, Project Dunbar, Project Orchid, digital currency
    - Blockchain, distributed ledger, DLT, smart contracts for finance
    - Artificial intelligence, AI, machine learning, ML, generative AI,
      large language models, LLM used in banking or treasury or cash management
    - Embedded finance, super apps, platform banking
    - Quantum computing in finance
    - New fintech business models disrupting cash management

"Market Research"
  → Industry surveys, benchmarks, research reports, market sizing,
    analyst forecasts, consultant whitepapers that do not fit the above

"Other"
  → Use only when none of the above apply at all

IMPORTANT: If a signal mentions APIs, open banking, or ERP connectivity
it MUST be tagged "API Banking" not "Other". If it mentions AI, tokenisation,
or digital assets in a cash management context it MUST be tagged "Innovation".
If it mentions PayNow, PromptPay, DuitNow, QRIS, UPI, or any real-time
payment rail linkage it MUST be tagged "Payments & Collections" AND scored 5.

GEOGRAPHY RULES — follow exactly:

Use ONLY these values for the geography field:
- A single ASEAN country if the signal applies to exactly one:
  Singapore, Indonesia, Malaysia, Thailand, Philippines, Vietnam,
  Myanmar, Cambodia, Laos, Brunei
- "ASEAN-Wide" if the signal applies to two or more ASEAN countries,
  or to ASEAN as a region broadly
- A non-ASEAN name (e.g. "India", "China", "Europe", "Global") ONLY
  if the signal originates entirely outside ASEAN

For the asean_impact field:
- true  = signal has meaningful implications for banks operating in ASEAN,
          even if it originates outside ASEAN
- false = signal has zero meaningful connection to ASEAN banking

SCORING RULES:
5 = Any of: direct competitive threat, major regulatory change, consultant
    report with specific ASEAN cash management findings, OR any signal about
    real-time payment rail integrations (PayNow, PromptPay, DuitNow, QRIS,
    UPI, FPS, or linkages between these rails)
4 = Significant market move or research finding worth briefing teams
3 = Useful context or global trend with ASEAN implications
2 = Loosely related, low urgency
1 = Minimal relevance

Mark as relevant ONLY if the content directly touches on:
- Cash management, liquidity, treasury
- Payments, collections, settlements (including real-time rails)
- Virtual accounts, notional pooling
- API banking, open banking, ERP integration
- Cross-border payments, FX, hedging
- Digital banking, fintech, embedded finance relevant to cash/payments
- ASEAN banking regulation affecting cash management or payments
- Consultant research on banking or payments trends
- AI or machine learning applied to banking or treasury
- Digital assets, tokenisation, CBDC with cash management implications
- Real-time payment rails in ASEAN (PayNow, PromptPay, DuitNow, QRIS, UPI)

Set relevant to FALSE for:
- Pure trade finance content (letters of credit, bills of lading,
  documentary collections, trade document frameworks, supply chain
  finance, receivables financing) UNLESS the signal also directly
  discusses cash management, treasury, or payments infrastructure
- Equity capital markets, M&A, investment banking
- Insurance products
- Content completely unrelated to banking or finance

SOURCE TYPE GUIDANCE — set source_type accordingly:
- content_type "scrape-static" or "scrape": static bank product/service page.
  Set source_type to "bank-product". Cap relevance_score at 3 unless a
  clear new product launch is evident in the text.
- content_type "pdf", "pdf-direct", "pdf-local": research/regulatory document.
  Set source_type to "pdf". Score 3-5 based on analytical depth.
- content_type "rss" or "scrape-deep": news article. Score normally 1-5.

Content type: {content_type}
Content:
{content}
"""

# Canonical ASEAN geography values
ASEAN_COUNTRIES = {
    "Singapore", "Indonesia", "Malaysia", "Thailand",
    "Philippines", "Vietnam", "Myanmar", "Cambodia",
    "Laos", "Brunei"
}
ASEAN_ALL = ASEAN_COUNTRIES | {"ASEAN-Wide"}

# Canonical product areas
VALID_PRODUCT_AREAS = {
    "Liquidity Management",
    "Payments & Collections",
    "Virtual Accounts",
    "API Banking",
    "FX & Hedging",
    "Regulatory",
    "Innovation",
    "Market Research",
    "Other"
}

# Keywords that force Innovation tag
INNOVATION_KEYWORDS = [
    "digital asset", "tokenis", "tokeniz", "stablecoin", "cbdc",
    "mbridge", "blockchain", "distributed ledger", "dlt",
    "generative ai", "large language model", "llm", "machine learning",
    " ai ", "artificial intelligence", "embedded finance", "super app"
]

# Keywords that force API Banking tag
API_KEYWORDS = [
    "api", "open banking", "open finance", "baas", "banking-as-a-service",
    "embedded banking", "erp integration", "sap integration",
    "oracle integration", "host-to-host", "iso 20022", "swift mx",
    "webhook", "developer portal", "sdk", "programmable money"
]

# Real-time payment rail keywords → score 5
REALTIME_RAIL_KEYWORDS = [
    "paynow", "promptpay", "duitnow", "qris", "upi linkage",
    "fps linkage", "real-time payment", "instant payment",
    "payment rail", "rail linkage", "rail integration",
    "mbridge", "project nexus"
]

def normalise_geography(geo_raw):
    if not geo_raw:
        return "ASEAN-Wide"
    geo = geo_raw.strip()
    if geo in ASEAN_ALL:
        return geo
    aliases = {
        "ASEAN": "ASEAN-Wide", "Asean": "ASEAN-Wide",
        "asean": "ASEAN-Wide", "asean-wide": "ASEAN-Wide",
        "Southeast Asia": "ASEAN-Wide", "SEA": "ASEAN-Wide",
        "Regional": "ASEAN-Wide",
        "SG": "Singapore", "ID": "Indonesia", "MY": "Malaysia",
        "TH": "Thailand", "PH": "Philippines", "VN": "Vietnam",
        "MM": "Myanmar", "KH": "Cambodia", "LA": "Laos", "BN": "Brunei",
    }
    if geo in aliases:
        return aliases[geo]
    matched = [c for c in ASEAN_COUNTRIES if c.lower() in geo.lower()]
    if len(matched) >= 2:
        return "ASEAN-Wide"
    if len(matched) == 1:
        return matched[0]
    return geo

def override_product_area(result, full_text):
    """
    Post-process product area to catch cases Claude might miss.
    Checks key_signal + so_what + title text for forcing keywords.
    """
    text_lower = full_text.lower()

    # Innovation override
    for kw in INNOVATION_KEYWORDS:
        if kw in text_lower:
            return "Innovation"

    # API Banking override
    for kw in API_KEYWORDS:
        if kw in text_lower:
            return "API Banking"

    # Validate against known list
    pa = result.get("product_area", "Other")
    if pa not in VALID_PRODUCT_AREAS:
        return "Other"

    return pa

def override_score(result, full_text):
    """Force score 5 for real-time payment rail signals."""
    text_lower = full_text.lower()
    for kw in REALTIME_RAIL_KEYWORDS:
        if kw in text_lower:
            return 5
    return result.get("relevance_score", 1)

def extract_signal(article):
    content_type = article.get("type", "unknown")
    full_content = f"Title: {article['title']}\n\n{article['content'][:2000]}"

    prompt = EXTRACTION_PROMPT.format(
        content_type=content_type,
        content=full_content
    )
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw.strip())

        if result.get("relevant"):
            result["geography"] = normalise_geography(result.get("geography", ""))

            # Build combined text for override checks
            check_text = " ".join([
                article.get("title", ""),
                article.get("content", "")[:500],
                result.get("key_signal", ""),
                result.get("so_what", "")
            ])

            result["product_area"] = override_product_area(result, check_text)
            result["relevance_score"] = override_score(result, check_text)

            if "asean_impact" not in result:
                result["asean_impact"] = result["geography"] in ASEAN_ALL

        return result

    except json.JSONDecodeError as e:
        print(f"  ✗ JSON parse failed: {e}")
        return {"relevant": False}
    except Exception as e:
        print(f"  ✗ Extraction failed: {e}")
        return {"relevant": False}

def make_dedup_key(signal):
    """Fingerprint for deduplication — same entity + key_signal = duplicate."""
    entity = (signal.get("entity") or "").lower().strip()
    key    = (signal.get("key_signal") or "").lower().strip()[:80]
    return f"{entity}||{key}"

def extract_all(articles):
    results = []
    skipped = 0
    seen_keys = set()

    for i, article in enumerate(articles):
        title = article['title'][:60] if article['title'] else "No title"
        source_type = article.get("type", "")
        print(f"  Processing {i+1}/{len(articles)} [{source_type}]: {title}")

        signal = extract_signal(article)

        if signal.get("relevant"):
            # Deduplication check
            dk = make_dedup_key(signal)
            if dk in seen_keys:
                print(f"  ⟳ Duplicate skipped: {title[:60]}")
                continue
            seen_keys.add(dk)

            # Sanitise date: static/product pages have no real publish date.
            # If the ingest type suggests a static page and the date looks
            # like a synthetic datetime stamp, clear it so the digest
            # doesn't treat it as fresh news.
            article_type = article.get("type", "")
            article_date = article.get("date", "")
            STATIC_TYPES = {"scrape-static", "scrape", "pdf",
                            "pdf-direct", "pdf-local"}
            is_synthetic = (
                article_type in STATIC_TYPES and
                article_date and
                " " in article_date and   # datetime has a space: "2026-04-17 14:32:..."
                article_date[:10] == article_date[:10]  # sanity
            )
            if is_synthetic:
                article = {**article, "date": ""}

            results.append({**article, **signal})
            print(
                f"  ✓ Score {signal.get('relevance_score')} | "
                f"{signal.get('entity')} | "
                f"Geo: {signal.get('geography')} | "
                f"{signal.get('product_area')}"
            )
        else:
            skipped += 1
            print(f"  — Not relevant, skipped")

    with open("extracted_signals.json", "w") as f:
        json.dump(results, f, indent=2)

    source_types = {}
    geo_counts   = {}
    product_counts = {}
    for r in results:
        t = r.get("source_type", "unknown")
        source_types[t] = source_types.get(t, 0) + 1
        g = r.get("geography", "unknown")
        geo_counts[g] = geo_counts.get(g, 0) + 1
        p = r.get("product_area", "unknown")
        product_counts[p] = product_counts.get(p, 0) + 1

    print(f"\n✅ Done — {len(results)} relevant signals saved")
    print(f"   {skipped} skipped as not relevant")
    print(f"\n   By source type:")
    for t, c in sorted(source_types.items()): print(f"   · {t}: {c}")
    print(f"\n   By geography:")
    for g, c in sorted(geo_counts.items(), key=lambda x: x[1], reverse=True): print(f"   · {g}: {c}")
    print(f"\n   By product area:")
    for p, c in sorted(product_counts.items(), key=lambda x: x[1], reverse=True): print(f"   · {p}: {c}")

    return results

if __name__ == "__main__":
    with open("raw_articles.json") as f:
        articles = json.load(f)
    if not articles:
        print("⚠️  raw_articles.json is empty — run ingest.py first")
    else:
        print(f"\n── Extracting signals from {len(articles)} items ──")
        extract_all(articles)