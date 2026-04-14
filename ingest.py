import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
import json
import os
import fitz  # PyMuPDF
from sources import RSS_FEEDS, SCRAPE_URLS, PDF_URLS

# ── Date freshness filter ──
def is_recent(date_str, days=30):
    """Returns True if the article is within the last X days."""
    if not date_str:
        return True
    try:
        from email.utils import parsedate_to_datetime
        pub_date = parsedate_to_datetime(date_str)
        pub_date = pub_date.replace(tzinfo=None)
        cutoff = datetime.now() - timedelta(days=days)
        return pub_date >= cutoff
    except Exception:
        try:
            for fmt in (
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d",
                "%a, %d %b %Y %H:%M:%S %Z",
                "%a, %d %b %Y %H:%M:%S %z",
                "%d %b %Y",
                "%B %d, %Y",
            ):
                try:
                    pub_date = datetime.strptime(
                        date_str[:25].strip(), fmt
                    )
                    cutoff = datetime.now() - timedelta(days=days)
                    return pub_date >= cutoff
                except Exception:
                    continue
        except Exception:
            pass
    return True

# ── Extract publish date from article HTML ──
def extract_date_from_page(soup):
    """Try to extract a publish date from common HTML date patterns."""
    meta_selectors = [
        {"property": "article:published_time"},
        {"name": "pubdate"},
        {"name": "publishdate"},
        {"name": "date"},
        {"itemprop": "datePublished"},
        {"name": "DC.date"},
        {"property": "og:published_time"},
        {"name": "article:published_time"},
    ]
    for attrs in meta_selectors:
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            return tag["content"]

    time_tag = soup.find("time")
    if time_tag:
        return time_tag.get("datetime") or time_tag.get_text(strip=True)

    for class_name in [
        "date", "published", "post-date", "entry-date",
        "article-date", "timestamp", "publish-date",
        "article__date", "post__date", "news-date"
    ]:
        tag = soup.find(class_=class_name)
        if tag:
            return tag.get_text(strip=True)

    return ""

# ── Extract text from a PDF ──
def extract_pdf_text(source, is_url=True):
    """
    Download and extract text from a PDF.
    source can be a URL or a local file path.
    Returns extracted text capped at 5000 characters.
    """
    try:
        if is_url:
            response = requests.get(
                source, timeout=30,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if response.status_code != 200:
                return None
            content_type = response.headers.get("Content-Type", "")
            if "pdf" not in content_type.lower() and \
               not source.lower().endswith(".pdf"):
                return None
            pdf_bytes = response.content
        else:
            with open(source, "rb") as f:
                pdf_bytes = f.read()

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
            if len(text) > 5000:
                break
        doc.close()

        text = text.strip()
        if len(text) < 100:
            return None

        return text[:5000]

    except Exception as e:
        print(f"    ✗ PDF extraction failed: {e}")
        return None

# ── Find PDF links on a page ──
def find_pdf_links(soup, base_url):
    """Find all PDF links on a page."""
    pdf_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)
        if full_url.lower().endswith(".pdf") or \
           "pdf" in full_url.lower():
            pdf_links.append(full_url)
    return list(dict.fromkeys(pdf_links))

# ── Fetch RSS articles ──
def fetch_rss_articles(feeds):
    articles = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            added = 0
            for entry in feed.entries[:20]:
                pub_date = entry.get("published", "")
                if pub_date and not is_recent(pub_date, days=30):
                    print(
                        f"    ↷ Skipped old: "
                        f"{entry.get('title','')[:50]}"
                    )
                    continue

                entry_url = entry.get("link", "")
                content = entry.get("summary", "")

                # Check if entry links directly to a PDF
                if entry_url.lower().endswith(".pdf"):
                    print(f"    📄 PDF in feed: {entry_url[:60]}")
                    pdf_text = extract_pdf_text(entry_url, is_url=True)
                    if pdf_text:
                        content = pdf_text

                articles.append({
                    "title": entry.get("title", ""),
                    "content": content,
                    "url": entry_url,
                    "source": feed.feed.get("title", url),
                    "date": pub_date or str(datetime.now()),
                    "type": "rss-pdf"
                          if entry_url.lower().endswith(".pdf")
                          else "rss"
                })
                added += 1

            print(f"  ✓ {url} — {added} recent articles kept")
        except Exception as e:
            print(f"  ✗ Failed: {url} — {e}")
    return articles

# ── Scrape pages, follow links, download PDFs ──
def scrape_page(url):
    try:
        response = requests.get(
            url, timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        soup = BeautifulSoup(response.text, "html.parser")

        # Find PDF links before cleaning
        pdf_links = find_pdf_links(soup, url)

        # Clean noise
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        # Find article links on the page — limit to 5
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("/"):
                base = urlparse(url)
                href = f"{base.scheme}://{base.netloc}{href}"
            if urlparse(url).netloc in href:
                links.append(href)

        links = list(dict.fromkeys(links))[:5]

        articles = []

        # Scrape main page itself
        text = soup.get_text(separator=" ", strip=True)[:3000]
        if len(text) > 200:
            articles.append({
                "title": soup.title.string if soup.title else url,
                "content": text,
                "url": url,
                "source": url,
                "date": str(datetime.now()),
                "type": "scrape"
            })

        # Download PDFs found on this page — limit to 2
        pdf_count = 0
        for pdf_url in pdf_links[:2]:
            print(f"    📄 Downloading PDF: {pdf_url[:70]}")
            pdf_text = extract_pdf_text(pdf_url, is_url=True)
            if pdf_text:
                pdf_title = (
                    pdf_url.split("/")[-1]
                    .replace(".pdf", "")
                    .replace("-", " ")
                    .replace("_", " ")
                    .title()
                )
                articles.append({
                    "title": pdf_title,
                    "content": pdf_text,
                    "url": pdf_url,
                    "source": url,
                    "date": str(datetime.now()),
                    "type": "pdf"
                })
                pdf_count += 1
                print(f"    ✓ PDF extracted: {pdf_title[:60]}")

        # Go into each linked article
        kept = 0
        skipped = 0
        for link in links:
            if link.lower().endswith(".pdf"):
                continue
            try:
                r = requests.get(
                    link, timeout=10,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                s = BeautifulSoup(r.text, "html.parser")

                pub_date = extract_date_from_page(s)

                if pub_date and not is_recent(pub_date, days=30):
                    skipped += 1
                    print(f"    ↷ Skipped old: {link[:60]}")
                    continue

                # Look for PDFs linked from this article — limit to 1
                sub_pdf_links = find_pdf_links(s, link)
                for pdf_url in sub_pdf_links[:1]:
                    print(
                        f"    📄 PDF in article: {pdf_url[:60]}"
                    )
                    pdf_text = extract_pdf_text(pdf_url, is_url=True)
                    if pdf_text:
                        pdf_title = (
                            pdf_url.split("/")[-1]
                            .replace(".pdf", "")
                            .replace("-", " ")
                            .replace("_", " ")
                            .title()
                        )
                        articles.append({
                            "title": pdf_title,
                            "content": pdf_text,
                            "url": pdf_url,
                            "source": url,
                            "date": pub_date or str(datetime.now()),
                            "type": "pdf"
                        })
                        print(
                            f"    ✓ PDF extracted: {pdf_title[:60]}"
                        )

                # Clean and extract page text
                for tag in s(["script", "style", "nav", "footer"]):
                    tag.decompose()
                body = s.get_text(separator=" ", strip=True)[:3000]
                title = s.title.string if s.title else link

                if len(body) > 300:
                    articles.append({
                        "title": title,
                        "content": body,
                        "url": link,
                        "source": url,
                        "date": pub_date if pub_date
                                else str(datetime.now()),
                        "type": "scrape-deep"
                    })
                    kept += 1
                    print(
                        f"    ✓ {title[:60]} "
                        f"[{pub_date[:10] if pub_date else 'no date'}]"
                    )

            except Exception:
                pass

        print(
            f"  ✓ Scraped {url} — "
            f"{kept} articles, {pdf_count} PDFs, "
            f"{skipped} old ones skipped"
        )
        return articles

    except Exception as e:
        print(f"  ✗ Failed to scrape {url} — {e}")
        return []

# ── Fetch direct PDF URLs ──
def fetch_direct_pdfs(pdf_urls):
    articles = []
    print(f"\n── Fetching {len(pdf_urls)} direct PDF URLs ──")
    for url in pdf_urls:
        print(f"  📄 Fetching: {url[:70]}")
        pdf_text = extract_pdf_text(url, is_url=True)
        if pdf_text:
            pdf_title = (
                url.split("/")[-1]
                .replace(".pdf", "")
                .replace("-", " ")
                .replace("_", " ")
                .title()
            )
            articles.append({
                "title": pdf_title,
                "content": pdf_text,
                "url": url,
                "source": url,
                "date": str(datetime.now()),
                "type": "pdf-direct"
            })
            print(f"  ✓ Extracted: {pdf_title[:60]}")
        else:
            print(f"  ✗ Could not extract: {url[:70]}")
    return articles

# ── Fetch PDFs from local documents folder ──
def fetch_local_pdfs(folder="documents"):
    articles = []
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"\n── Created {folder}/ — drop PDFs here manually ──")
        return articles

    pdf_files = [f for f in os.listdir(folder) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"\n── No PDFs in {folder}/ folder ──")
        return articles

    print(f"\n── Reading {len(pdf_files)} local PDFs from {folder}/ ──")
    for filename in pdf_files:
        path = os.path.join(folder, filename)
        print(f"  📄 Reading: {filename}")
        pdf_text = extract_pdf_text(path, is_url=False)
        if pdf_text:
            articles.append({
                "title": filename
                    .replace(".pdf", "")
                    .replace("-", " ")
                    .replace("_", " ")
                    .title(),
                "content": pdf_text,
                "url": f"local://{path}",
                "source": "local",
                "date": str(datetime.now()),
                "type": "pdf-local"
            })
            print(f"  ✓ Extracted: {filename}")
        else:
            print(f"  ✗ Could not extract: {filename}")
    return articles

# ── Main pipeline ──
def ingest_all():
    print("\n── Fetching RSS feeds (last 30 days only) ──")
    articles = fetch_rss_articles(RSS_FEEDS)

    print("\n── Scraping pages (last 30 days, 5 sub-links per page) ──")
    for url in SCRAPE_URLS:
        pages = scrape_page(url)
        if pages:
            articles.extend(pages)

    pdf_articles = fetch_direct_pdfs(PDF_URLS)
    articles.extend(pdf_articles)

    local_articles = fetch_local_pdfs("documents")
    articles.extend(local_articles)

    with open("raw_articles.json", "w") as f:
        json.dump(articles, f, indent=2)

    # Summary breakdown
    types = {}
    for a in articles:
        t = a.get("type", "unknown")
        types[t] = types.get(t, 0) + 1

    print(f"\n✅ Done — {len(articles)} total items saved to raw_articles.json")
    print(f"   Breakdown:")
    for t, count in sorted(types.items()):
        print(f"   · {t}: {count}")

    return articles

if __name__ == "__main__":
    ingest_all()