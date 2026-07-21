"""
BidRadar V1 configuration.

Chinese name: 纸箱招标雷达系统
"""

from paths import BID_RESULTS_FILE

PROJECT_NAME = "BidRadar"
PROJECT_CN_NAME = "纸箱招标雷达系统"

INDUSTRY_KEYWORDS = [
    "纸箱",
    "包装箱",
    "瓦楞纸箱",
    "纸制品包装",
    "彩箱",
    "纸盒",
    "外包装箱",
    "纸包装",
    "包装材料",
    "包装耗材",
]

PURCHASE_KEYWORDS = [
    "年度采购",
    "供应商征集",
    "框架协议",
    "集中采购",
]

KEYWORDS = INDUSTRY_KEYWORDS + PURCHASE_KEYWORDS

PROVINCES = [
    "江苏",
    "安徽",
    "山东",
]

PROVINCE_ALIASES = {
    "江苏": [
        "江苏",
        "南京",
        "苏州",
        "昆山",
        "无锡",
        "常州",
        "南通",
        "徐州",
        "盐城",
        "扬州",
        "镇江",
        "泰州",
        "淮安",
        "连云港",
        "宿迁",
    ],
    "安徽": [
        "安徽",
        "合肥",
        "芜湖",
        "滁州",
        "马鞍山",
        "蚌埠",
        "阜阳",
        "安庆",
        "淮南",
        "淮北",
        "铜陵",
        "宣城",
        "六安",
        "亳州",
        "池州",
        "黄山",
    ],
    "山东": [
        "山东",
        "济南",
        "青岛",
        "烟台",
        "潍坊",
        "临沂",
        "淄博",
        "济宁",
        "泰安",
        "威海",
        "日照",
        "德州",
        "聊城",
        "滨州",
        "菏泽",
        "枣庄",
        "东营",
    ],
}

ALLOW_UNKNOWN_PROVINCE = True

PROVINCE_CONFIDENCE_COLUMN = "地区识别置信度"

SOURCE_PROVINCE_RULES = {
    "江苏公共资源交易": "江苏",
    "安徽公共资源交易": "安徽",
    "山东公共资源交易": "山东",
}

PROVINCE_TEXT_ALIASES = {
    "江苏": [
        "江苏",
        "南京",
        "苏州",
        "昆山",
        "无锡",
        "常州",
        "南通",
        "扬州",
        "镇江",
        "泰州",
        "徐州",
        "盐城",
        "淮安",
        "连云港",
        "宿迁",
    ],
    "安徽": [
        "安徽",
        "合肥",
        "芜湖",
        "蚌埠",
        "淮南",
        "马鞍山",
        "淮北",
        "铜陵",
        "安庆",
        "黄山",
        "滁州",
        "阜阳",
        "宿州",
        "六安",
        "亳州",
        "池州",
        "宣城",
    ],
    "山东": [
        "山东",
        "济南",
        "青岛",
        "烟台",
        "潍坊",
        "淄博",
        "枣庄",
        "东营",
        "济宁",
        "泰安",
        "威海",
        "日照",
        "临沂",
        "德州",
        "聊城",
        "滨州",
        "菏泽",
    ],
}

for province_name in PROVINCE_TEXT_ALIASES:
    if province_name not in PROVINCES:
        PROVINCES.append(province_name)

OUTPUT_FILE = BID_RESULTS_FILE

EXCEL_COLUMNS = [
    "采集日期",
    "省份",
    "城市",
    "招标标题",
    "采购单位",
    "公告类型",
    "发布日期",
    "截止日期",
    "预算金额",
    "信息来源",
    "链接",
    "匹配关键词",
    "价值等级",
    "跟进状态",
    "备注",
]
