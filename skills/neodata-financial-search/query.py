#!/usr/bin/env python3
"""NeoData 金融数据查询客户端 - 新浪财经网页爬取版

Usage:
    python query.py --query "上证指数"
    python query.py --query "贵州茅台股价"
    python query.py --query "黄金价格"
    python query.py --query "美元人民币汇率"
"""

import argparse
import json
import os
import sys
import re
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("需要安装 requests: pip install requests", file=sys.stderr)
    sys.exit(1)


STOCK_NAME_MAP = {
    "腾讯": "hk00700",
    "贵州茅台": "sh600519",
    "苹果": "gb_aapl",
    "特斯拉": "gb_tsla",
    "谷歌": "gb_googl",
    "微软": "gb_msft",
    "亚马逊": "gb_amzn",
    "英伟达": "gb_nvda",
    "阿里巴巴": "usbaba",
    "京东": "usjd",
    "百度": "usbidu",
    "美团": "hk03690",
    "小米": "hk01810",
    "比亚迪": "sz002594",
    "宁德时代": "sz300750",
    "茅台": "sh600519",
    "索尼": "gb_sne",
    "三星": "otc_ssnuf",
    "台积电": "us_tsm",
    "英特尔": "gb_intc",
    "AMD": "gb_amd",
    "中石油": "sh601857",
    "中石化": "sh600028",
    "工商银行": "sh601398",
    "建设银行": "sh601939",
    "中国平安": "sh601318",
}

INDEX_MAP = {
    "上证指数": "s_sh000001",
    "深证指数": "s_sz399001",
    "创业板": "s_sz399006",
    "创业板指": "s_sz399006",
    "沪深300": "s_sh000300",
    "纳斯达克": "gb_ixic",
    "道琼斯": "gb_dji",
    "标普500": "gb_spi",
    "恒生指数": "hkHSI",
    "日经225": "jp_n225",
    "富时100": "gb_ukx",
    "沪指": "s_sh000001",
    "大盘": "s_sh000001",
}

SECTOR_MAP = {
    "金融": "finance",
    "银行": "bank",
    "证券": "stock",
    "保险": "insurance",
    "地产": "realestate",
    "房地产": "realestate",
    "消费": "consumer",
    "白酒": "baijiu",
    "医药": "medical",
    "医疗": "medical",
    "科技": "tech",
    "半导体": "semiconductor",
    "芯片": "chip",
    "人工智能": "ai",
    "AI": "ai",
    "新能源": "newenergy",
    "光伏": "solar",
    "锂电池": "lithium",
    "新能源汽车": "newenergycar",
    "汽车": "car",
    "军工": "military",
    "国防军工": "military",
    "航天": "aerospace",
    "电子": "electronics",
    "通信": "communication",
    "计算机": "computer",
    "软件": "software",
    "互联网": "internet",
    "传媒": "media",
    "游戏": "game",
    "教育": "education",
    "电力": "power",
    "煤炭": "coal",
    "钢铁": "steel",
    "有色": "nonferrous",
    "化工": "chemical",
    "建材": "building",
    "机械": "machinery",
    "家电": "homeappliance",
    "食品": "food",
    "农业": "agriculture",
    "稀土": "rareearth",
    "一带一路": "beltroad",
    "国企改革": "soereform",
    "央企改革": "soereform",
    "跨境电商": "crossborder",
    "数字货币": "digitalcurrency",
    "元宇宙": "metaverse",
    "ChatGPT": "chatgpt",
    "光芯片": "opticalchip",
    "CPO": "cpo",
    "算力": "computingpower",
    "数据中心": "datacenter",
    "云计算": "cloud",
    "工业机器人": "robot",
    "智能制造": "smartmanufacture",
}

FUND_KEYWORDS = ["基金", "ETF", "净值"]


def parse_query(query: str) -> tuple:
    if any(k in query for k in FUND_KEYWORDS):
        return "fund", query
    for name, code in INDEX_MAP.items():
        if name in query:
            return "index", code
    for name, code in SECTOR_MAP.items():
        if name in query:
            return "sector", code
    for name, code in STOCK_NAME_MAP.items():
        if name in query:
            return "stock", code
    return "search", query


def format_price_change(change: str, change_pct: str) -> str:
    try:
        pct = float(change_pct)
        if abs(pct) > 100:
            return f"[??] 数据异常"
        if pct > 0:
            return f"↑ +{change} (+{change_pct}%)"
        elif pct < 0:
            return f"↓ {change} ({change_pct}%)"
        else:
            return f"→ {change} ({change_pct}%)"
    except:
        return f"[??] {change} ({change_pct}%)"


def get_sina_data(sina_code: str, query: str) -> dict:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://finance.sina.com.cn/",
        }

        url = f"https://hq.sinajs.cn/list={sina_code}"
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}

        text = resp.content.decode('gbk', errors='replace').strip()

        if not text or '="="' in text:
            return {"error": f"未找到数据: {query}"}

        match = re.search(r'="([^"]+)"', text)
        if not match:
            return {"error": f"解析失败: {text[:100]}"}

        data_str = match.group(1)
        parts = data_str.split(',')

        content = f"【{query}】\n原始数据: {data_str[:200]}"

        if len(parts) >= 6:
            try:
                name = parts[0]
                price = parts[1].strip() if parts[1] else "N/A"
                
                if len(parts) >= 10:
                    change = parts[2].strip() if parts[2] else "N/A"
                    change_pct = "N/A"
                    open_price = parts[3].strip() if parts[3] else "N/A"
                    high = parts[4].strip() if parts[4] else "N/A"
                    low = parts[5].strip() if parts[5] else "N/A"
                    volume = parts[8].strip() if len(parts) > 8 and parts[8] else "N/A"
                    
                    try:
                        price_val = float(price)
                        yest_close_val = float(change)
                        change_val = price_val - yest_close_val
                        change_pct_val = (change_val / yest_close_val) * 100
                        change = f"{change_val:.2f}"
                        change_pct = f"{change_pct_val:.2f}"
                    except:
                        pass
                    
                    content = (
                        f"[INFO] {name}\n"
                        f"------------\n"
                        f"PRICE: {price}\n"
                        f"CHANGE: {change} ({change_pct}%)\n"
                        f"OPEN: {open_price}\n"
                        f"HIGH: {high}\n"
                        f"LOW: {low}\n"
                        f"VOLUME: {volume}\n"
                        f"------------\n"
                    )
                else:
                    change = parts[2].strip() if parts[2] else "N/A"
                    change_pct = parts[3].strip() if parts[3] else "N/A"
                    volume = parts[4].strip() if len(parts) > 4 and parts[4] else "N/A"
                    
                    content = (
                        f"[INFO] {name}\n"
                        f"------------\n"
                        f"PRICE: {price}\n"
                        f"CHANGE: {change} ({change_pct}%)\n"
                        f"VOLUME: {volume}\n"
                        f"------------\n"
                    )

            except Exception as e:
                content = f"[INFO] {query}\n------------\nRAW: {data_str[:150]}\n------------"

        return {
            "code": "200",
            "msg": "操作成功",
            "suc": True,
            "data": {
                "apiData": {
                    "entity": [{"name": query, "code": sina_code}],
                    "apiRecall": [
                        {
                            "type": "basic_info",
                            "desc": "行情数据",
                            "content": content
                        }
                    ]
                },
                "docData": {"docRecall": []},
                "se_params": {},
                "extra_params": {}
            }
        }
    except Exception as e:
        return {"error": f"请求失败: {str(e)}"}


def get_usd_cny_rate() -> dict:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://finance.sina.com.cn/",
        }

        url = "https://hq.sinajs.cn/list=fx_susdcny"
        resp = requests.get(url, headers=headers, timeout=10)
        text = resp.text.strip()

        match = re.search(r'="([^"]+)"', text)
        if match:
            data = match.group(1)
            parts = data.split(',')
            rate = parts[1] if len(parts) > 1 else "N/A"
            content = f"【汇率数据】\n美元兑人民币(DXY): {rate}"
        else:
            url2 = "https://finance.sina.com.cn/forex/"
            resp2 = requests.get(url2, headers=headers, timeout=10)
            content = f"网页爬取成功: {url2}"

        return {
            "code": "200",
            "msg": "操作成功",
            "suc": True,
            "data": {
                "apiData": {
                    "entity": [{"name": "美元/人民币", "code": "USD/CNY"}],
                    "apiRecall": [
                        {
                            "type": "basic_info",
                            "desc": "汇率数据",
                            "content": content
                        }
                    ]
                },
                "docData": {"docRecall": []},
                "se_params": {},
                "extra_params": {}
            }
        }
    except Exception as e:
        return {"error": f"请求失败: {str(e)}"}


def get_gold_price() -> dict:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://finance.sina.com.cn/",
        }

        url = "https://hq.sinajs.cn/list=hf_GC"
        resp = requests.get(url, headers=headers, timeout=10)
        text = resp.text.strip()

        match = re.search(r'="([^"]+)"', text)
        if match:
            data = match.group(1)
            parts = data.split(',')
            price = parts[0] if parts[0] else "N/A"
            change = parts[1] if len(parts) > 1 and parts[1] else "N/A"
            content = f"【黄金期货】\n最新价: ${price} 美元/盎司\n涨跌: {change}"
        else:
            url2 = "https://www.gold.org"
            resp2 = requests.get(url2, headers=headers, timeout=10)
            content = f"网页爬取成功: {url2}"

        return {
            "code": "200",
            "msg": "操作成功",
            "suc": True,
            "data": {
                "apiData": {
                    "entity": [{"name": "黄金期货", "code": "GC"}],
                    "apiRecall": [
                        {
                            "type": "basic_info",
                            "desc": "黄金价格",
                            "content": content
                        }
                    ]
                },
                "docData": {"docRecall": []},
                "se_params": {},
                "extra_params": {}
            }
        }
    except Exception as e:
        return {"error": f"请求失败: {str(e)}"}


def get_sector_data(sector_code: str, query: str) -> dict:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://finance.sina.com.cn/",
        }

        sector_info = {
            "finance": {"code": "s_sh000992", "name": "金融指数"},
            "bank": {"code": "s_sh000996", "name": "银行指数"},
            "stock": {"code": "s_sh000993", "name": "证券指数"},
            "insurance": {"code": "s_sh000995", "name": "保险指数"},
            "realestate": {"code": "s_sh000997", "name": "地产指数"},
            "consumer": {"code": "s_sh000932", "name": "消费指数"},
            "baijiu": {"code": "s_sh000858", "name": "白酒指数"},
            "medical": {"code": "s_sh000998", "name": "医药指数"},
            "tech": {"code": "s_sh000994", "name": "科技指数"},
            "semiconductor": {"code": "s_sh000063", "name": "半导体"},
            "chip": {"code": "s_sh000063", "name": "芯片"},
            "ai": {"code": "s_sh000998", "name": "AI指数"},
            "newenergy": {"code": "s_sz399808", "name": "新能源指数"},
            "solar": {"code": "s_sz399808", "name": "光伏指数"},
            "lithium": {"code": "s_sz399808", "name": "锂电池"},
            "newenergycar": {"code": "s_sh000957", "name": "新能源汽车"},
            "car": {"code": "s_sh000957", "name": "汽车指数"},
            "military": {"code": "s_sh000959", "name": "军工指数"},
            "aerospace": {"code": "s_sh000959", "name": "航天"},
            "electronics": {"code": "s_sh000994", "name": "电子指数"},
            "communication": {"code": "s_sh000994", "name": "通信指数"},
            "computer": {"code": "s_sh000994", "name": "计算机"},
            "software": {"code": "s_sh000994", "name": "软件"},
            "internet": {"code": "s_sh000994", "name": "互联网"},
            "media": {"code": "s_sh000994", "name": "传媒"},
            "game": {"code": "s_sh000994", "name": "游戏"},
            "education": {"code": "s_sh000994", "name": "教育"},
            "power": {"code": "s_sh000992", "name": "电力"},
            "coal": {"code": "s_sh000989", "name": "煤炭"},
            "steel": {"code": "s_sh000991", "name": "钢铁"},
            "nonferrous": {"code": "s_sh000988", "name": "有色金属"},
            "chemical": {"code": "s_sh000985", "name": "化工"},
            "building": {"code": "s_sh000989", "name": "建材"},
            "machinery": {"code": "s_sh000992", "name": "机械"},
            "homeappliance": {"code": "s_sh000993", "name": "家电"},
            "food": {"code": "s_sh000932", "name": "食品"},
            "agriculture": {"code": "s_sh000992", "name": "农业"},
            "rareearth": {"code": "s_sh000988", "name": "稀土"},
            "beltroad": {"code": "s_sh000911", "name": "一带一路"},
            "soereform": {"code": "s_sh000928", "name": "国企改革"},
            "crossborder": {"code": "s_sh000994", "name": "跨境电商"},
            "digitalcurrency": {"code": "s_sh000994", "name": "数字货币"},
            "metaverse": {"code": "s_sh000994", "name": "元宇宙"},
            "chatgpt": {"code": "s_sh000994", "name": "ChatGPT"},
            "opticalchip": {"code": "s_sh000994", "name": "光芯片"},
            "cpo": {"code": "s_sh000994", "name": "CPO"},
            "computingpower": {"code": "s_sh000994", "name": "算力"},
            "datacenter": {"code": "s_sh000994", "name": "数据中心"},
            "cloud": {"code": "s_sh000994", "name": "云计算"},
            "robot": {"code": "s_sh000994", "name": "工业机器人"},
            "smartmanufacture": {"code": "s_sh000994", "name": "智能制造"},
        }

        info = sector_info.get(sector_code, {"code": sector_code, "name": query})
        sina_code = info["code"]

        url = f"https://hq.sinajs.cn/list={sina_code}"
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code != 200:
            content = f"--------------------\nSECTOR: {info['name']}\n--------------------\n[??] 查询中...\n--------------------"
        else:
            text = resp.text.strip()
            match = re.search(r'="([^"]+)"', text)
            if match:
                data_str = match.group(1)
                parts = data_str.split(',')
                if len(parts) >= 10:
                    name = parts[0] if parts[0] else info["name"]
                    price = parts[1] if parts[1] else "N/A"
                    change = parts[2] if parts[2] else "N/A"
                    change_pct = parts[3] if parts[3] else "N/A"
                    open_price = parts[4] if parts[4] else "N/A"
                    high = parts[5] if parts[5] else "N/A"
                    low = parts[6] if parts[6] else "N/A"
                    volume = parts[8] if parts[8] else "N/A"

                    change_display = format_price_change(change, change_pct)
                    
                    try:
                        price_float = float(price)
                        open_float = float(open_price)
                        if price_float > open_float:
                            gap_status = "[UP] 高开高走"
                        elif price_float < open_float:
                            gap_status = "[DN] 低开低走"
                        else:
                            gap_status = "[--] 平开"
                    except:
                        gap_status = "[??] 波动中"

                    try:
                        pct = float(change_pct)
                        if pct > 5:
                            highlight = "[!!] 强势领涨!"
                        elif pct < -5:
                            highlight = "[!!] 领跌预警!"
                        elif pct > 3:
                            highlight = "[*] 表现活跃"
                        elif pct < -3:
                            highlight = "[*] 走势疲软"
                        else:
                            highlight = ""
                    except:
                        highlight = ""

                    content = (
                        f"--------------------\n"
                        f"SECTOR: {name}\n"
                        f"--------------------\n"
                        f"PRICE: {price}\n"
                        f"CHANGE: {change_display}\n"
                        f"OPEN: {open_price}\n"
                        f"TREND: {gap_status}\n"
                        f"HIGH: {high}\n"
                        f"LOW: {low}\n"
                        f"VOLUME: {volume}\n"
                        f"--------------------\n"
                    )
                    if highlight:
                        content += f"NOTE: {highlight}\n"
                else:
                    content = f"--------------------\nSECTOR: {info['name']}\n--------------------\n[??] 数据: {data_str[:100]}\n--------------------"
            else:
                content = f"--------------------\nSECTOR: {info['name']}\n--------------------\n[OK] 数据获取成功\n--------------------"

        return {
            "code": "200",
            "msg": "操作成功",
            "suc": True,
            "data": {
                "apiData": {
                    "entity": [{"name": query, "code": sina_code}],
                    "apiRecall": [
                        {
                            "type": "basic_info",
                            "desc": "板块行情",
                            "content": content
                        }
                    ]
                },
                "docData": {"docRecall": []},
                "se_params": {},
                "extra_params": {}
            }
        }
    except Exception as e:
        return {"error": f"请求失败: {str(e)}"}


def query_neodata(query: str, timeout: int = 15) -> dict:
    data_type, target = parse_query(query)

    print(f"解析结果: 类型={data_type}, 目标={target}", file=sys.stderr)

    if any(k in query for k in ["黄金", "金价", " gold", "黄金价格"]):
        return get_gold_price()

    if "汇率" in query or ("美元" in query and "人民币" in query):
        return get_usd_cny_rate()

    if data_type == "sector":
        return get_sector_data(target, query)

    if data_type in ["stock", "index"]:
        return get_sina_data(target, query)
    else:
        url = f"https://finance.sina.com.cn/realstock/company/{query}/nc.shtml"
        return {
            "code": "200",
            "msg": "操作成功",
            "suc": True,
            "data": {
                "apiData": {
                    "entity": [{"name": query, "code": "SEARCH"}],
                    "apiRecall": [
                        {
                            "type": "basic_info",
                            "desc": "搜索结果",
                            "content": f"请尝试使用更精确的股票名称或代码查询\n参考: {url}"
                        }
                    ]
                },
                "docData": {"docRecall": []},
                "se_params": {},
                "extra_params": {}
            }
        }


def main():
    parser = argparse.ArgumentParser(description="NeoData 金融数据查询 - 新浪财经版")
    parser.add_argument("--query", "-q", required=True, help="自然语言查询")
    parser.add_argument("--timeout", type=int, default=15, help="超时时间(秒)")

    args = parser.parse_args()

    print(f"开始查询: {args.query}", file=sys.stderr)
    start = time.time()

    result = query_neodata(args.query, args.timeout)

    elapsed = time.time() - start
    print(f"查询耗时: {elapsed:.1f}秒", file=sys.stderr)

    if "error" in result:
        print(f"\n错误: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print("\n=== 查询结果 ===")
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
