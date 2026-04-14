RSS_FEEDS = [
    # Trade & Banking Publications — verified working feeds
    "https://www.tradefinanceglobal.com/feed/",
    "https://www.tradefinanceglobal.com/posts/category/articles/feed/",
    "https://www.tradefinanceglobal.com/posts/category/news/feed/",
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
    "https://www.pymnts.com/topic/fintech/feed/",
    "https://www.pymnts.com/topic/b2b/feed/",
    "https://www.pymnts.com/topic/banking/feed/",
    "https://www.finextra.com/rss/channel.aspx?channel=payments",
    "https://www.finextra.com/rss/channel.aspx?channel=wholesale",
    "https://www.finextra.com/rss/channel.aspx?channel=regulation",
    "https://theasianbanker.com/category/payments/feed/",
    "https://theasianbanker.com/category/wholesale-banking/feed/",
    "https://theasianbanker.com/category/digital-banking/feed/",
    "https://www.techinasia.com/tag/fintech/feed",
    "https://www.techinasia.com/tag/southeast-asia/feed",
    "https://www.techinasia.com/tag/singapore/feed",
    "https://www.paymentsdive.com/feeds/news?topic=banking",
    "https://www.paymentsdive.com/feeds/news?topic=b2b",
    "https://thepaypers.com/rss/payments",
    "https://thepaypers.com/rss/open-banking",
    "https://asianbankingandfinance.net/banking/feed/",
    "https://asianbankingandfinance.net/technology/feed/",
    "https://thefintechtimes.com/category/payments/feed/",
    "https://thefintechtimes.com/category/asia/feed/",
    "https://thefintechtimes.com/category/fintech/feed/",
    "https://www.bobsguide.com/category/banking-technology/feed/",
    "https://www.bobsguide.com/category/payments/feed/",

    # Regulatory Bodies — verified working
    "https://www.bnm.gov.my/rss",

    # Competitor Newsrooms
    "https://www.ocbc.com/group/news/rss.xml",
]

# Scrape URLs — trimmed to highest value pages only
# Sub-link following is limited to 5 per page (set in ingest.py)
SCRAPE_URLS = [
    # Competitors
    "https://www.dbs.com.sg/corporate/solutions/cash-management",
    "https://www.jpmorgan.com/payments/payments-apac",
    "https://www.business.hsbc.com.sg/en-sg/corporate-banking",
    "https://www.sc.com/en/corporate-investment-banking/transaction-banking/",
    "https://corporates.db.com/solutions/corporate-bank-solutions/cash-management/",
    "https://www.bangkokbank.com/en/Business-Banking/Manage-My-Business/Digital-Banking/iCash-NewSystem",
    "https://www.bca.co.id/en/bisnis/solusi/cash-management",

    # Consultant insights pages — scrape for PDF links only
    "https://www.mckinsey.com/industries/financial-services/our-insights",
    "https://www.oliverwyman.com/our-expertise/industries/financial-services.html",
    "https://www.bcg.com/industries/financial-institutions/transaction-banking",
    "https://www.accenture.com/sg-en/insights/banking",
    "https://kpmg.com/sg/en/home/insights.html",
    "https://www.ey.com/en_ap/insights",
    "https://www2.deloitte.com/ap/en/pages/financial-services/topics/banking.html",

    # Regulatory & Research
    "https://www.bis.org/cpmi/publications.htm",
    "https://www.adb.org/publications/series/trade-finance",
    "https://www.mas.gov.sg/publications",
]

# Direct PDF URLs — downloaded on every pipeline run
PDF_URLS = [
    # BIS
    "https://www.bis.org/cpmi/publ/d187.pdf",

    # ADB Trade Finance Gap Report
    "https://www.adb.org/sites/default/files/publication/922096/trade-finance-gaps-growth-jobs-survey-2023.pdf",
]