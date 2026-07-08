"""
BidRadar V1.2 value scoring.

The score is based on bid title, buyer name, city, and notice type.
"""

HIGH_VALUE_WORDS = {
    "年度采购": 30,
    "框架协议": 30,
    "集中采购": 25,
    "供应商征集": 20,
}

KEY_INDUSTRIES = [
    "食品",
    "饮料",
    "家电",
    "新能源",
    "医药",
    "物流",
    "汽车",
]

KEY_CITIES = [
    "苏州",
    "昆山",
    "无锡",
    "常州",
    "合肥",
    "芜湖",
    "滁州",
    "青岛",
    "烟台",
    "潍坊",
    "临沂",
]

BUYER_WORDS = {
    "集团": 20,
    "股份": 20,
    "制造": 15,
}


def score_bid(bid, debug=False):
    """Return score, level, priority, and recommend for one bid record."""
    title = str(bid.get("招标标题", ""))
    buyer = str(bid.get("采购单位", ""))
    city = str(bid.get("城市", ""))
    notice_type = str(bid.get("公告类型", ""))

    score = 0
    matched_rules = []
    text = " ".join([title, buyer, city, notice_type])

    for word, points in HIGH_VALUE_WORDS.items():
        if word in title or word in notice_type:
            score += points
            matched_rules.append((f"采购关键词：{word}", points))

    for industry in KEY_INDUSTRIES:
        if industry in text:
            score += 20
            matched_rules.append((f"重点行业：{industry}", 20))

    for key_city in KEY_CITIES:
        if key_city in city or key_city in title:
            score += 20
            matched_rules.append((f"重点城市：{key_city}", 20))

    for word, points in BUYER_WORDS.items():
        if word in buyer:
            score += points
            matched_rules.append((f"采购单位关键词：{word}", points))

    if debug:
        print("=" * 40)
        print("评分调试")
        print(f"招标标题：{title}")

        if matched_rules:
            for rule, points in matched_rules:
                print(f"{rule} +{points}")
        else:
            print("未命中加分规则")

        print(f"最终得分：{score}")
        print("=" * 40)

    return {
        "score": score,
        "level": get_level(score),
        "priority": get_priority(score),
        "recommend": get_recommend(score),
    }


def get_level(score):
    if score >= 90:
        return "★★★★★"

    if score >= 70:
        return "★★★★"

    if score >= 50:
        return "★★★"

    if score >= 30:
        return "★★"

    return "★"


def get_priority(score):
    if score >= 90:
        return "最高"

    if score >= 70:
        return "高"

    if score >= 50:
        return "中"

    if score >= 30:
        return "低"

    return "观察"


def get_recommend(score):
    if score >= 70:
        return "建议重点跟进"

    if score >= 50:
        return "建议跟进"

    if score >= 30:
        return "可作为备选"

    return "暂不优先"
