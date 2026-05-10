RSS_FEEDS = [
    # ════════════════════════════════════════════════
    # Trade & Banking Publications
    # ════════════════════════════════════════════════
    "https://www.tradefinanceglobal.com/feed/",
    "https://www.tradefinanceglobal.com/posts/category/articles/feed/",
    "https://www.tradefinanceglobal.com/posts/category/news/feed/",

    # ════════════════════════════════════════════════
    # Fintech News Network (ASEAN)
    # ════════════════════════════════════════════════
    "https://fintechnews.sg/payments/feed/",
    "https://fintechnews.sg/digital-banking-news-singapore/feed/",
    "https://fintechnews.sg/regtech/feed/",
    "https://fintechnews.sg/ai/feed/",
    "https://fintechnews.id/payments/feed/",
    "https://fintechnews.id/regtech/feed/",
    "https://fintechnews.my/payments/feed/",
    "https://fintechnews.my/regtech/feed/",
    "https://fintechnews.ph/payments/feed/",
    "https://fintechnews.sg/thailand/feed/",
    "https://fintechnews.sg/vietnam/feed/",

    # ════════════════════════════════════════════════
    # PYMNTS
    # ════════════════════════════════════════════════
    "https://www.pymnts.com/topic/fintech/feed/",
    "https://www.pymnts.com/topic/b2b/feed/",
    "https://www.pymnts.com/topic/banking/feed/",

    # ════════════════════════════════════════════════
    # Finextra — full channel set
    # ════════════════════════════════════════════════
    "https://www.finextra.com/rss/channel.aspx?channel=payments",
    "https://www.finextra.com/rss/channel.aspx?channel=wholesale",
    "https://www.finextra.com/rss/channel.aspx?channel=regulation",
    "https://www.finextra.com/rss/channel.aspx?channel=transaction",
    "https://www.finextra.com/rss/channel.aspx?channel=corporate",
    "https://www.finextra.com/rss/channel.aspx?channel=ai",

    # ════════════════════════════════════════════════
    # The Asian Banker — full category set
    # ════════════════════════════════════════════════
    "https://theasianbanker.com/feed/",
    "https://theasianbanker.com/category/payments/feed/",
    "https://theasianbanker.com/category/wholesale-banking/feed/",
    "https://theasianbanker.com/category/digital-banking/feed/",
    "https://theasianbanker.com/category/transaction-banking/feed/",
    "https://theasianbanker.com/category/corporate-banking/feed/",
    "https://theasianbanker.com/category/banking/feed/",

    # ════════════════════════════════════════════════
    # Tech in Asia
    # ════════════════════════════════════════════════
    "https://www.techinasia.com/tag/fintech/feed",
    "https://www.techinasia.com/tag/southeast-asia/feed",
    "https://www.techinasia.com/tag/singapore/feed",

    # ════════════════════════════════════════════════
    # Payments Dive
    # ════════════════════════════════════════════════
    "https://www.paymentsdive.com/feeds/news?topic=banking",
    "https://www.paymentsdive.com/feeds/news?topic=b2b",

    # ════════════════════════════════════════════════
    # The Paypers
    # ════════════════════════════════════════════════
    "https://thepaypers.com/rss/payments",
    "https://thepaypers.com/rss/open-banking",

    # ════════════════════════════════════════════════
    # Asian Banking & Finance
    # ════════════════════════════════════════════════
    "https://asianbankingandfinance.net/banking/feed/",
    "https://asianbankingandfinance.net/technology/feed/",
    "https://asianbankingandfinance.net/payments/feed/",

    # ════════════════════════════════════════════════
    # The Fintech Times
    # ════════════════════════════════════════════════
    "https://thefintechtimes.com/category/payments/feed/",
    "https://thefintechtimes.com/category/asia/feed/",
    "https://thefintechtimes.com/category/fintech/feed/",

    # ════════════════════════════════════════════════
    # Bobsguide
    # ════════════════════════════════════════════════
    "https://www.bobsguide.com/category/banking-technology/feed/",
    "https://www.bobsguide.com/category/payments/feed/",

    # ════════════════════════════════════════════════
    # BIS — confirmed working RSS feeds (VERIFIED)
    # Previously only had one PDF URL for BIS.
    # Added: full BIS feed + press releases feed
    # ════════════════════════════════════════════════
    "https://www.bis.org/doclist/rss_all_categories.rss",   # entire BIS website
    "https://www.bis.org/doclist/all_pressrels.rss",         # BIS press releases only

    # ════════════════════════════════════════════════
    # ADB — confirmed working RSS feeds (VERIFIED)
    # ════════════════════════════════════════════════
    "https://www.adb.org/rss/publications.xml",   # ADB research publications
    "https://www.adb.org/rss/news.xml",           # ADB news

    # ════════════════════════════════════════════════
    # Regulatory Bodies
    # ════════════════════════════════════════════════
    "https://www.bnm.gov.my/rss",                  # Bank Negara Malaysia

    # ════════════════════════════════════════════════
    # Competitor Newsrooms
    # ════════════════════════════════════════════════
    "https://www.ocbc.com/group/news/rss.xml",

    # ════════════════════════════════════════════════
    # Cybersecurity — Banking & Corporate Channel Threats
    # Scoped to threats affecting payment rails, SWIFT, corporate
    # banking portals, and treasury systems.
    # FS-ISAC and SWIFT ISAC require membership — not public RSS.
    # ════════════════════════════════════════════════
    #"https://www.finextra.com/rss/channel.aspx?channel=security",
    #"https://www.finextra.com/rss/channel.aspx?channel=crime",
    #"https://krebsonsecurity.com/feed/",
    #"https://therecord.media/feed",
    #"https://www.bankinfosecurity.com/rssFeeds.php?type=main",
]

# ════════════════════════════════════════════════
# SCRAPE URLs
# ingest.py follows up to 25 article links per page
# ════════════════════════════════════════════════
SCRAPE_URLS = [
    # ── Competitor product pages ──
    "https://www.dbs.com.sg/corporate/solutions/cash-management",
    "https://www.jpmorgan.com/payments/payments-apac",
    "https://www.jpmorgan.com/insights/payments/trends-innovation/",
    "https://www.business.hsbc.com.sg/en-sg/corporate-banking",
    "https://www.sc.com/en/corporate-investment-banking/transaction-banking/",
    "https://corporates.db.com/solutions/corporate-bank-solutions/cash-management/",
    "https://www.bangkokbank.com/en/Business-Banking/Manage-My-Business/Digital-Banking/iCash-NewSystem",
    "https://www.bca.co.id/en/bisnis/solusi/cash-management",

    # ── DBS Newsroom — confirmed active (VERIFIED)
    # No RSS available; scraping gives press release index
    # ════════════════════════════════════════════════
    "https://www.dbs.com/media/news-list.page",

    # ── SWIFT news — confirmed active (VERIFIED)
    # Swift Institute closed 2024 — use swift.com/news instead
    # ════════════════════════════════════════════════
    "https://www.swift.com/news-events/news",

    # ── MAS (Monetary Authority of Singapore) — confirmed active (VERIFIED)
    # No RSS available; scraping captures media releases and regulations
    # ════════════════════════════════════════════════
    "https://www.mas.gov.sg/news",
    "https://www.mas.gov.sg/regulation/regulations-and-guidance",
    #"https://www.mas.gov.sg/regulation/regulations-and-guidance/technology-risk-management-guidelines",

    # ── BSP (Bangko Sentral ng Pilipinas) — confirmed active (VERIFIED)
    # RSS feed URLs are SharePoint templates and don't resolve.
    # Scraping the media releases page instead.
    # ════════════════════════════════════════════════
    "https://www.bsp.gov.ph/SitePages/MediaAndResearch/MediaList.aspx?TabId=1",

    # ── BOT (Bank of Thailand) — confirmed active (VERIFIED)
    # No English RSS found. Scraping English news page.
    # ════════════════════════════════════════════════
    "https://www.bot.or.th/en/news-and-media/news.html",

    # ── Temenos — confirmed active, no public RSS (VERIFIED)
    # Leading core banking vendor; ASEAN deployments frequent
    # ════════════════════════════════════════════════
    "https://www.temenos.com/news/",

    # ── Finastra — confirmed active, no public RSS (VERIFIED)
    # Major payments platform vendor covering ASEAN banks
    # ════════════════════════════════════════════════
    "https://www.finastra.com/news-events/articles",

    # ── Asian Banker editorial index ──
    "https://www.theasianbanker.com/updates-and-articles",

    # ── Specific high-value Asian Banker articles ──
    "https://www.theasianbanker.com/updates-and-articles/standard-chartered-builds-transaction-banking-around-asean-s-cross-border-complexity",

    # ── Consultant insights ──
    "https://www.mckinsey.com/industries/financial-services/our-insights",
    "https://www.oliverwyman.com/our-expertise/industries/financial-services.html",
    "https://www.bcg.com/industries/financial-institutions/transaction-banking",
    "https://www.accenture.com/sg-en/insights/banking",
    "https://kpmg.com/sg/en/home/insights.html",
    "https://www.ey.com/en_ap/insights",
    "https://www2.deloitte.com/ap/en/pages/financial-services/topics/banking.html",

    # ── Regulatory & Research ──
    "https://www.bis.org/cpmi/publications.htm",
    "https://www.mas.gov.sg/publications",
    "https://www.adb.org/publications/series/trade-finance",
]

# ════════════════════════════════════════════════
# Direct PDF URLs — downloaded on every pipeline run
# ════════════════════════════════════════════════
PDF_URLS = [
    # BIS CPMI — cross-border payments framework
    "https://www.bis.org/cpmi/publ/d187.pdf",

    # ADB Trade Finance Gap Report
    "https://www.adb.org/sites/default/files/publication/922096/trade-finance-gaps-growth-jobs-survey-2023.pdf",

    # McKinsey 2025 Global Payments Report (VERIFIED — publicly accessible)
    "https://www.finews.asia/images/download/McKinsey_The_2025_Global_Payments_Report_DRAFT_EMBARGOv2914040.pdf",

    # J.P. Morgan: Payments Are Eating the World (VERIFIED — public PDF)
    "https://www.jpmorgan.com/content/dam/jpm/treasury-services/documents/jpm-payments-are-eating-the-world.pdf",
]