"""
BidRadar V1.7 public data sources.

Only use public pages. If a page requires login, CAPTCHA, or blocks normal
access, the crawler will skip it.
"""

SEARCH_KEYWORDS = [
    "纸箱",
    "包装箱",
    "瓦楞纸箱",
    "包装材料",
    "彩箱",
    "纸盒",
]

SOURCES = [
    {
        "source_name": "江苏公共资源交易相关公开网页",
        "url": "http://jsggzy.jszwfw.gov.cn/",
        "province": "江苏",
        "supports_keyword_search": False,
    },
    {
        "source_name": "安徽公共资源交易相关公开网页",
        "url": "https://ggzy.ah.gov.cn/",
        "province": "安徽",
        "supports_keyword_search": False,
    },
    {
        "source_name": "山东公共资源交易相关公开网页",
        "url": "http://ggzyjy.shandong.gov.cn/",
        "province": "山东",
        "supports_keyword_search": False,
    },
    {
        "source_name": "中国政府采购网公开搜索页",
        "url": "https://search.ccgp.gov.cn/bxsearch",
        "search_url_template": (
            "https://search.ccgp.gov.cn/bxsearch?"
            "searchtype=1&page_index=1&bidSort=0&pinMu=0&bidType=0"
            "&dbselect=bidx&kw={keyword}&timeType=0"
        ),
        "province": "",
        "supports_keyword_search": True,
    },
    {
        "source_name": "中国招标投标公共服务平台公开搜索页",
        "url": "http://bulletin.cebpubservice.com/xxfbcmses/search/bulletin.html",
        "search_url_template": (
            "http://bulletin.cebpubservice.com/xxfbcmses/search/bulletin.html?"
            "searchDate=1994-07-02&dates=300&word={keyword}"
        ),
        "province": "",
        "supports_keyword_search": True,
    },
]
