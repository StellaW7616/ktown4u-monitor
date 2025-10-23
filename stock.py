import requests, re, json, time, os
from datetime import datetime

# ========== 配置区 ==========
DATA_FILE = "sales_history.json"
LOG_FILE = "sales_log.csv"

# 商品分组
product_groups = {
"韩彬": [
        "https://www.ktown4u.com/iteminfo?goods_no=149449",
        "https://kr.ktown4u.com/iteminfo?goods_no=149449",
        "https://cn.ktown4u.com/iteminfo?goods_no=149449",
        "https://jp.ktown4u.com/iteminfo?goods_no=149449",
    ],
    "安炯燮": [
        "https://www.ktown4u.com/iteminfo?goods_no=149450",
        "https://kr.ktown4u.com/iteminfo?goods_no=149450",
        "https://cn.ktown4u.com/iteminfo?goods_no=149450",
        "https://jp.ktown4u.com/iteminfo?goods_no=149450",
    ],
    "具本奕": [
        "https://www.ktown4u.com/iteminfo?goods_no=149451",
        "https://kr.ktown4u.com/iteminfo?goods_no=149451",
        "https://cn.ktown4u.com/iteminfo?goods_no=149451",
        "https://jp.ktown4u.com/iteminfo?goods_no=149451",
    ],
    "恩灿": [
        "https://www.ktown4u.com/iteminfo?goods_no=149452",
        "https://kr.ktown4u.com/iteminfo?goods_no=149452",
        "https://cn.ktown4u.com/iteminfo?goods_no=149452",
        "https://jp.ktown4u.com/iteminfo?goods_no=149452",
    ],
    "李义雄": [
        "https://www.ktown4u.com/iteminfo?goods_no=149453",
        "https://kr.ktown4u.com/iteminfo?goods_no=149453",
        "https://cn.ktown4u.com/iteminfo?goods_no=149453",
        "https://jp.ktown4u.com/iteminfo?goods_no=149453",
    ],
    "金台来": [
        "https://www.ktown4u.com/iteminfo?goods_no=149454",
        "https://kr.ktown4u.com/iteminfo?goods_no=149454",
        "https://cn.ktown4u.com/iteminfo?goods_no=149454",
        "https://jp.ktown4u.com/iteminfo?goods_no=149454",
    ],
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.ktown4u.com/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# ========== 函数区 ==========
def load_history():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"  ⚠️ 读取历史记录失败: {e}")
            return {}
    return {}

def save_history(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  ⚠️ 保存历史记录失败: {e}")

def extract_info(html):
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not match:
        return None, None
    
    try:
        data = json.loads(match.group(1))
        pageProps = data.get("props", {}).get("pageProps", {}) or data.get("pageProps", {})
        product = pageProps.get("productDetails", {})
        
        if not product:
            return None, None
        
        name = product.get("productName") or product.get("name")
        sales = product.get("quantity") or product.get("stock") or product.get("restockNum") or 0
        
        return name, sales
    except:
        return None, None

def correct_sales(raw_sales):
    """
    数据校正函数
    1. 每满3本多算1本，所以需要除以 1.33 或乘以 0.75
    2. 负数表示卖出，需要转换为正数
    """
    # 取绝对值（因为负数表示卖出）
    corrected = abs(raw_sales)
    # 除以 1.33 来去掉水分（每3本多算1本 = 4本中3本是真实的）
    corrected = corrected * 3 // 4
    return corrected

def log_sales_change(product_name, old_sales, new_sales, change):
    try:
        file_exists = os.path.exists(LOG_FILE)
        with open(LOG_FILE, 'a', encoding='utf-8', newline='') as f:
            if not file_exists:
                f.write("时间,商品名称,前原始销量,前校正销量,原始变化,现原始销量,现校正销量,校正变化\n")
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            old_corrected = correct_sales(old_sales)
            new_corrected = correct_sales(new_sales)
            change_corrected = new_corrected - old_corrected
            f.write(f"{timestamp},{product_name},{old_sales},{old_corrected},{change},{new_sales},{new_corrected},{change_corrected}\n")
    except Exception as e:
        print(f"  ⚠️ 保存日志失败: {e}")

# ========== 主程序（一次性运行）==========
print(f"🟢 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始检查...\n")

last_quantities = load_history()

for group_name, group_urls in product_groups.items():
    total_sales = 0
    product_name = None
    all_loaded = True
    
    for url in group_urls:
        try:
            print(f"  📍 {url}")
            r = requests.get(url, headers=HEADERS, timeout=10)
            
            if r.status_code != 200:
                print(f"    ❌ HTTP {r.status_code}")
                all_loaded = False
                continue
            
            name, qty = extract_info(r.text)
            
            if not name:
                all_loaded = False
                continue
            
            product_name = name
            total_sales += qty
            print(f"    ✓ 销量: {qty}")
            
        except Exception as e:
            print(f"    ❌ 错误: {e}")
            all_loaded = False
    
    # 显示和记录结果
    if all_loaded and product_name:
        # 校正销量数据
        total_sales_corrected = correct_sales(total_sales)
        
        if group_name not in last_quantities or last_quantities[group_name] is None:
            print(f"\n  ✅ [{product_name}]")
            print(f"     原始销量: {total_sales}")
            print(f"     校正销量: {total_sales_corrected}\n")
            last_quantities[group_name] = total_sales
        elif last_quantities[group_name] != total_sales:
            change = total_sales - last_quantities[group_name]
            change_corrected = correct_sales(total_sales) - correct_sales(last_quantities[group_name])
            direction = "📈" if change < 0 else "📉"
            print(f"\n  🔔 [{product_name}]")
            print(f"     原始变化: {last_quantities[group_name]} → {total_sales} ({direction} {abs(change)})")
            print(f"     校正变化: {correct_sales(last_quantities[group_name])} → {total_sales_corrected} ({abs(change_corrected)})\n")
            log_sales_change(product_name, last_quantities[group_name], total_sales, change)
            last_quantities[group_name] = total_sales
        else:
            print(f"\n  🔹 [{product_name}]")
            print(f"     原始销量: {total_sales}")
            print(f"     校正销量: {total_sales_corrected}\n")
        
        save_history(last_quantities)

print("✅ 检查完成")
