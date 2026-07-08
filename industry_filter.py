"""
BidRadar V1.6 industry filter.

Only bids related to cartons or paper packaging should enter Excel.
Purchase words such as 年度采购 and 集中采购 are not retention conditions.
"""

from config import INDUSTRY_KEYWORDS


def is_carton_related(text):
    """判断文本是否命中纸箱/纸包装行业关键词。"""
    text = str(text)

    return any(
        keyword in text
        for keyword in INDUSTRY_KEYWORDS
    )
