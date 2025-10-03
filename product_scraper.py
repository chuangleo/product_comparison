import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
from urllib.parse import quote
import re
import warnings
import logging
import os

# 在文件開頭添加這些行來抑制所有警告和日誌
warnings.filterwarnings("ignore")
logging.getLogger('selenium').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

# 抑制 Chrome 相關的錯誤訊息
os.environ['WDM_LOG_LEVEL'] = '0'
os.environ['WDM_PRINT_FIRST_LINE'] = 'False'

def fetch_products_for_momo(keyword, max_products=50):
    """
    使用 Selenium 從 momo 購物網抓取商品資訊
    
    Args:
        keyword (str): 搜尋關鍵字
        max_products (int): 最大抓取商品數量
    
    Returns:
        list: 商品資訊列表，每個商品包含 id, title, price, image_url, url, platform, sku
    """
    
    products = []
    product_id = 1  # 順序編號
    driver = None
    page = 1  # 當前頁數
    
    try:
        # 設定 Chrome 選項
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # 無頭模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 禁用圖片載入以提高速度
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 初始化 WebDriver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        print(f"正在搜尋 momo: {keyword}")
        
        # 等待頁面載入
        wait = WebDriverWait(driver, 15)
        
        # 多頁抓取循環
        while len(products) < max_products:
            # 建構搜尋 URL（包含頁數）
            encoded_keyword = quote(keyword)
            search_url = f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={encoded_keyword}&searchType=1&cateLevel=0&ent=k&sortType=1&curPage={page}"
            
            print(f"正在抓取第 {page} 頁...")
            
            # 頁面載入重試
            attempt = 1
            max_attempts = 3
            product_elements = []
            while attempt <= max_attempts:
                try:
                    driver.get(search_url)
                    time.sleep(3)  # 等待頁面載入
                    
                    # 嘗試查找商品元素
                    selectors_to_try = [
                        "li.listAreaLi",
                        ".listAreaUl li.listAreaLi",
                        "li.goodsItemLi",
                        ".prdListArea .goodsItemLi",
                        ".searchPrdListArea li",
                        "li[data-gtm]",
                        ".goodsItemLi",
                        ".searchPrdList li"
                    ]
                    
                    for selector in selectors_to_try:
                        try:
                            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                            product_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            if product_elements:
                                #print(f"使用選擇器 '{selector}' 找到 {len(product_elements)} 個商品")
                                break
                        except TimeoutException:
                            continue
                    
                    # 如果找到有效商品元素或商品數量少於 20 個但大於 0，則退出重試
                    if product_elements:
                        break
                    # 如果未找到商品元素或商品數量少於 20 個，則重試
                    print(f"第 {page} 頁未找到足夠商品元素（找到 {len(product_elements)} 個），重試 {attempt}/{max_attempts}")
                    attempt += 1
                    time.sleep(random.uniform(3, 6))  # 重試間隔
                except TimeoutException:
                    print(f"第 {page} 頁載入超時，重試 {attempt}/{max_attempts}")
                    attempt += 1
                    time.sleep(random.uniform(3, 6))
            
            if not product_elements:
                print("無法找到商品元素，可能頁面結構已改變或已到達最後一頁")
                break
            
            print(f"開始解析 {len(product_elements)} 個商品")
            page_products_count = 0
            
            # 解析每個商品
            for i, element in enumerate(product_elements):
                try:
                    # 如果已經獲得足夠的商品，就停止
                    if len(products) >= max_products:
                        break
                    
                    # 提取商品標題
                    title = ""
                    title_selectors = [
                        "h3.prdName",
                        ".prdNameTitle h3.prdName",
                        ".prdName",
                        "h3",
                        "a[title]",
                        "img[alt]",
                        ".goodsName",
                        ".goodsInfo h3",
                        "a"
                    ]
                    
                    for selector in title_selectors:
                        try:
                            title_elem = element.find_element(By.CSS_SELECTOR, selector)
                            if selector == "img[alt]":
                                title = title_elem.get_attribute("alt").strip()
                            elif selector == "a[title]":
                                title = title_elem.get_attribute("title").strip()
                            else:
                                title = title_elem.text.strip()
                            
                            if title and len(title) > 5:  # 確保標題有足夠長度
                                break
                        except NoSuchElementException:
                            continue
                    
                    # 如果沒有找到標題，跳過這個商品
                    if not title:
                        continue
                    
                    # 提取價格
                    price = 0
                    price_selectors = [
                        ".money .price b",
                        ".price b",
                        ".money b",
                        ".price",
                        ".money",
                        ".cost",
                        "b",
                        "strong",
                        ".goodsPrice",
                        ".priceInfo"
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_elements = element.find_elements(By.CSS_SELECTOR, selector)
                            for price_elem in price_elements:
                                price_text = price_elem.text
                                if price_text and ('$' in price_text or 'NT' in price_text or any(c.isdigit() for c in price_text)):
                                    # 提取數字
                                    numbers = re.findall(r'\d+', price_text.replace(',', ''))
                                    if numbers:
                                        # 取最大的數字作為價格（避免取到折扣百分比等小數字）
                                        potential_prices = [int(num) for num in numbers if int(num) > 10]
                                        if potential_prices:
                                            price = max(potential_prices)
                                            break
                            if price > 0:
                                break
                        except NoSuchElementException:
                            continue
                    
                    # 如果沒有找到價格，跳過這個商品
                    if price <= 0:
                        continue
                    
                    # 提取商品連結
                    url = ""
                    try:
                        link_elem = element.find_element(By.CSS_SELECTOR, "a.goods-img-url")
                        url = link_elem.get_attribute("href")
                        if not url.startswith("http"):
                            url = "https://www.momoshop.com.tw" + url
                    except NoSuchElementException:
                        # 嘗試找其他可能的連結選擇器
                        try:
                            link_elem = element.find_element(By.CSS_SELECTOR, "a[href*='/goods/']")
                            url = link_elem.get_attribute("href")
                            if not url.startswith("http"):
                                url = "https://www.momoshop.com.tw" + url
                        except NoSuchElementException:
                            # 嘗試找任何連結
                            try:
                                link_elem = element.find_element(By.CSS_SELECTOR, "a[href]")
                                url = link_elem.get_attribute("href")
                                if url and not url.startswith("http"):
                                    url = "https://www.momoshop.com.tw" + url
                            except NoSuchElementException:
                                url = ""
                    
                    # 提取 i_code 作為 sku，如果找不到則使用網址最後一段
                    sku = ""
                    if url:
                        # 首先嘗試提取 i_code
                        match = re.search(r'i_code=(\d+)', url)
                        if match:
                            sku = match.group(1)
                        else:
                            # 如果找不到 i_code，則使用網址的最後一段
                            # 例如：https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code=123456
                            # 或：https://www.momoshop.com.tw/product/ABC123
                            url_parts = url.rstrip('/').split('/')
                            if url_parts:
                                last_part = url_parts[-1]
                                # 如果最後一段包含參數，只取檔名部分
                                if '?' in last_part:
                                    last_part = last_part.split('?')[0]
                                # 如果最後一段有副檔名，去掉副檔名
                                if '.' in last_part:
                                    last_part = last_part.split('.')[0]
                                sku = last_part
                    
                    # 提取商品圖片
                    image_url = ""
                    try:
                        # 優先尋找第一個商品圖片
                        img_elem = element.find_element(By.CSS_SELECTOR, "img.prdImg")
                        # 優先使用 src，然後是 data-original，最後是 data-src
                        image_url = (img_elem.get_attribute("src") or 
                                   img_elem.get_attribute("data-original") or 
                                   img_elem.get_attribute("data-src"))
                        
                        if image_url:
                            # 處理相對路徑和協議相對路徑
                            if image_url.startswith("//"):
                                image_url = "https:" + image_url
                            elif image_url.startswith("/"):
                                image_url = "https://www.momoshop.com.tw" + image_url
                            elif not image_url.startswith("http"):
                                # 如果是相對路徑但不以 / 開頭，假設是 momoshop 的圖片
                                if "momoshop" not in image_url:
                                    image_url = "https://cdn3.momoshop.com.tw/momoshop/upload/media/" + image_url
                                else:
                                    image_url = "https://" + image_url
                    except NoSuchElementException:
                        # 如果找不到 prdImg，嘗試其他圖片選擇器
                        try:
                            img_elem = element.find_element(By.CSS_SELECTOR, "img")
                            image_url = (img_elem.get_attribute("src") or 
                                       img_elem.get_attribute("data-original") or 
                                       img_elem.get_attribute("data-src"))
                            
                            if image_url:
                                # 處理相對路徑和協議相對路徑
                                if image_url.startswith("//"):
                                    image_url = "https:" + image_url
                                elif image_url.startswith("/"):
                                    image_url = "https://www.momoshop.com.tw" + image_url
                                elif not image_url.startswith("http"):
                                    if "momoshop" not in image_url:
                                        image_url = "https://cdn3.momoshop.com.tw/momoshop/upload/media/" + image_url
                                    else:
                                        image_url = "https://" + image_url
                        except NoSuchElementException:
                            image_url = ""
                    
                    # 確保所有必要欄位都有值才加入商品
                    if title and price > 0 and url:
                        product = {
                            "id": product_id,
                            "title": title,
                            "price": price,
                            "image_url": image_url if image_url else "",
                            "url": url,
                            "platform": "momo",
                            "sku": sku
                        }
                        products.append(product)
                        product_id += 1
                        page_products_count += 1
                        #print(f"成功解析商品 {len(products)}: {title[:50]}... (NT$ {price:,})")
                    
                    # 避免過於頻繁的操作
                    time.sleep(random.uniform(0.05, 0.1))
                    
                except Exception as e:
                    print(f"解析第 {i+1} 個商品時發生錯誤: {e}")
                    continue
            
            #print(f"第 {page} 頁抓取到 {page_products_count} 個有效商品，目前總計 {len(products)} 個商品")
            
            # 如果這一頁的商品數量少於預期，可能是最後一頁了
            if len(product_elements) < 20:  # momo 一般每頁有 30 個商品，如果少於 20 個可能是最後一頁
                print("可能已到達最後一頁，停止抓取")
                break
            
            # 如果這一頁沒有找到任何有效商品，也停止抓取
            if page_products_count == 0:
                print("這一頁沒有找到有效商品，停止抓取")
                break
                
            # 如果還需要更多商品，則跳到下一頁
            if len(products) < max_products:
                page += 1
                time.sleep(random.uniform(2, 3))  # 頁面間隔
            else:
                break
        
        print(f"成功從 momo 獲取 {len(products)} 個商品")
        return products
        
    except Exception as e:
        print(f"momo Selenium 爬蟲發生錯誤: {e}")
        return []
    
    finally:
        # 確保關閉瀏覽器
        if driver:
            try:
                driver.quit()
            except:
                pass


def fetch_products_for_pchome(keyword, max_products=50):
    """
    使用 Selenium 從 PChome 購物網抓取商品資訊，優化效率的同時獲取詳細商品名稱
    
    Args:
        keyword (str): 搜尋關鍵字
        max_products (int): 最大抓取商品數量
    
    Returns:
        list: 商品資訊列表，每個商品包含 id, title, price, image_url, url, platform, sku
    """
    products = []
    product_id = 1
    driver = None
    page = 1

    try:
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        # 啟用圖片載入以獲取更完整的頁面內容
        prefs = {
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        print(f"正在搜尋 PChome: {keyword}")

        # 收集所有基本商品信息
        all_basic_products = []
        
        while len(all_basic_products) < max_products:
            encoded_keyword = quote(keyword)
            search_url = f"https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={encoded_keyword}&page={page}&sort=sale/dc"
            print(f"正在抓取第 {page} 頁基本信息...")

            driver.get(search_url)
            time.sleep(1)

            try:
                body = driver.find_element(By.TAG_NAME, "pre").text
                data = json.loads(body)
                items = data.get("prods", [])
            except Exception as e:
                print("解析 PChome 商品 JSON 失敗:", e)
                break

            if not items:
                print("無法找到商品元素，可能已到達最後一頁")
                break

            for item in items:
                if len(all_basic_products) >= max_products:
                    break
                    
                base_title = item.get("name", "")
                price = item.get("price", 0)
                pid = item.get("Id", "")
                url = f"https://24h.pchome.com.tw/prod/{pid}" if pid else ""
                sku = pid if pid else ""
                image_url = item.get("picB", "")
                
                # 修正圖片 URL 處理邏輯
                if image_url:
                    if image_url.startswith("//"):
                        image_url = "https:" + image_url
                    elif image_url.startswith("/"):
                        image_url = "https://cs.ecimg.tw" + image_url
                    elif not image_url.startswith("http"):
                        image_url = "https://cs.ecimg.tw/" + image_url
                else:
                    image_url = ""

                if base_title and price > 0 and url:
                    all_basic_products.append({
                        "base_title": base_title,
                        "price": price,
                        "pid": pid,
                        "url": url,
                        "sku": sku,
                        "image_url": image_url
                    })

            if len(items) < 20:
                print("可能已到達最後一頁，停止抓取基本信息")
                break

            page += 1
            time.sleep(0.5)

        print(f"收集到 {len(all_basic_products)} 個基本商品信息")
        
        # 批量獲取詳細名稱 - 使用多標籤頁優化
        print("開始批量獲取詳細商品名稱...")
        
        batch_size = 5  # 每批處理 5 個商品
        for i in range(0, len(all_basic_products), batch_size):
            batch = all_basic_products[i:i+batch_size]
            print(f"處理批次 {i//batch_size + 1}/{(len(all_basic_products) + batch_size - 1)//batch_size}")
            
            # 為每個商品打開新標籤頁
            original_window = driver.current_window_handle
            windows_data = []
            
            for j, product_info in enumerate(batch):
                try:
                    if j == 0:
                        # 第一個商品使用當前標籤頁
                        driver.get(product_info["url"])
                        windows_data.append({
                            "handle": original_window,
                            "product_info": product_info
                        })
                    else:
                        # 其他商品打開新標籤頁
                        driver.execute_script("window.open('');")
                        driver.switch_to.window(driver.window_handles[-1])
                        driver.get(product_info["url"])
                        windows_data.append({
                            "handle": driver.current_window_handle,
                            "product_info": product_info
                        })
                except Exception as e:
                    print(f"打開商品頁面失敗: {e}")
                    continue
            
            # 等待所有頁面載入
            time.sleep(3)
            
            # 逐一處理每個標籤頁
            for window_data in windows_data:
                try:
                    driver.switch_to.window(window_data["handle"])
                    product_info = window_data["product_info"]
                    
                    # 獲取詳細名稱
                    detailed_title = product_info["base_title"]
                    try:
                        secondary_element = driver.find_element(By.CSS_SELECTOR, "span.o-prodMainName__colorSecondary.o-prodMainName__colorSecondary--1700[aria-hidden='true']")
                        secondary_name = secondary_element.text.strip()
                        if secondary_name:
                            # 將品牌名稱放在前面，商品名稱放在後面
                            detailed_title = secondary_name + " " + product_info["base_title"]
                            print(f"組合完整名稱: {secondary_name} + {product_info['base_title']}")
                    except NoSuchElementException:
                        try:
                            secondary_element = driver.find_element(By.CSS_SELECTOR, "span.o-prodMainName__colorSecondary")
                            secondary_name = secondary_element.text.strip()
                            if secondary_name:
                                # 將品牌名稱放在前面，商品名稱放在後面
                                detailed_title = secondary_name + " " + product_info["base_title"]
                                print(f"組合完整名稱（備用選擇器）: {secondary_name} + {product_info['base_title']}")
                        except NoSuchElementException:
                            pass  # 使用原始名稱                    # 創建最終商品對象
                    product = {
                        "id": product_id,
                        "title": detailed_title,
                        "price": product_info["price"],
                        "image_url": product_info["image_url"],
                        "url": product_info["url"],
                        "platform": "pchome",
                        "sku": product_info["sku"]
                    }
                    products.append(product)
                    product_id += 1
                    
                except Exception as e:
                    print(f"處理商品詳細信息失敗: {e}")
                    continue
            
            # 關閉除了第一個標籤頁外的所有標籤頁
            for handle in driver.window_handles[1:]:
                driver.switch_to.window(handle)
                driver.close()
            
            # 切換回原始標籤頁
            driver.switch_to.window(original_window)
            
            # 批次間稍作休息
            time.sleep(1)

        print(f"成功從 PChome 獲取 {len(products)} 個商品")
        return products

    except Exception as e:
        print(f"PChome Selenium 爬蟲發生錯誤: {e}")
        return []

    finally:
        # 確保關閉瀏覽器
        if driver:
            try:
                driver.quit()
            except:
                pass


if __name__ == "__main__":
    # 測試爬蟲
    keyword = input("輸入關鍵字: ")
    english_keyword = input("輸入關鍵字的英文名稱: ")
    num = int(input("輸入數量: "))
    products = fetch_products_for_momo(keyword, num)
    
    # 為每個商品添加查詢關鍵字
    for product in products:
        product['query'] = english_keyword
    
    # 儲存 products 至 JSON 檔案
    with open("momo_products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    if products:
        print(f"\n找到 {len(products)} 個商品：")
        for product in products:
            print(f"ID: {product['id']}")
            print(f"標題: {product['title']}")
            print(f"價格: NT$ {product['price']:,}")
            print(f"圖片: {product['image_url']}")
            print(f"連結: {product['url']}")
            print(f"平台: {product['platform']}")
            print("-" * 50)
    else:
        print("沒有找到商品")

    products = fetch_products_for_pchome(keyword, num)
    
    # 為每個商品添加查詢關鍵字
    for product in products:
        product['query'] = english_keyword
    
    # 儲存 products 至 JSON 檔案
    with open("pchome_products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    if products:
        print(f"\n找到 {len(products)} 個商品：")
        for product in products:
            print(f"ID: {product['id']}")
            print(f"標題: {product['title']}")
            print(f"價格: NT$ {product['price']:,}")
            print(f"圖片: {product['image_url']}")
            print(f"連結: {product['url']}")
            print(f"平台: {product['platform']}")
            print("-" * 50)
    else:
        print("沒有找到商品")