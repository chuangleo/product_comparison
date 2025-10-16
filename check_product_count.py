import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from urllib.parse import quote
import warnings
import logging
import os

# 抑制警告和日誌
warnings.filterwarnings("ignore")
logging.getLogger('selenium').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)
os.environ['WDM_LOG_LEVEL'] = '0'
os.environ['WDM_PRINT_FIRST_LINE'] = 'False'


def check_momo_product_count(keyword, target_count=100):
    """
    檢查 momo 購物網是否有至少 target_count 筆商品
    
    Args:
        keyword (str): 搜尋關鍵字
        target_count (int): 目標商品數量
    
    Returns:
        dict: 包含 platform, has_enough, actual_count 的字典
    """
    driver = None
    try:
        # 設定 Chrome 選項（無頭模式，快速）
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 無頭模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # 禁用圖片載入以提高速度
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(20)
        
        print(f"正在檢查 momo: {keyword}")
        
        # 建構搜尋 URL（只檢查第一頁）
        encoded_keyword = quote(keyword)
        search_url = f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={encoded_keyword}&searchType=1&cateLevel=0&ent=k&sortType=1&curPage=1"
        
        driver.get(search_url)
        time.sleep(3)
        
        # 嘗試找到總商品數量的顯示元素
        wait = WebDriverWait(driver, 10)
        total_count = 0
        
        # 方法1: 尋找顯示總數的元素
        selectors_for_total = [
            ".searchListArea .searchTotal",
            ".searchTotal",
            "span.totalNum",
            ".totalResults",
            "div[class*='total']"
        ]
        
        for selector in selectors_for_total:
            try:
                total_elem = driver.find_element(By.CSS_SELECTOR, selector)
                total_text = total_elem.text
                # 提取數字
                import re
                numbers = re.findall(r'\d+', total_text)
                if numbers:
                    total_count = int(numbers[0])
                    print(f"  → 從頁面元素找到總數: {total_count}")
                    break
            except NoSuchElementException:
                continue
        
        # 方法2: 如果找不到總數，計算商品元素數量並推估
        if total_count == 0:
            selectors_to_try = [
                "li.listAreaLi",
                ".listAreaUl li.listAreaLi",
                "li.goodsItemLi",
                ".prdListArea .goodsItemLi",
                ".searchPrdListArea li",
                "li[data-gtm]"
            ]
            
            for selector in selectors_to_try:
                try:
                    product_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if product_elements:
                        first_page_count = len(product_elements)
                        # momo 每頁通常 30 個商品，推估總數
                        # 但我們只關心是否超過 target_count
                        print(f"  → 第一頁找到 {first_page_count} 個商品")
                        
                        # 如果第一頁就有 30 個商品，很可能有更多頁
                        if first_page_count >= 30:
                            # 估計至少有 3-4 頁的商品
                            total_count = first_page_count * 3
                        else:
                            total_count = first_page_count
                        break
                except NoSuchElementException:
                    continue
        
        has_enough = total_count >= target_count
        
        return {
            "platform": "momo",
            "has_enough": has_enough,
            "actual_count": total_count,
            "keyword": keyword
        }
        
    except Exception as e:
        print(f"momo 檢查發生錯誤: {e}")
        return {
            "platform": "momo",
            "has_enough": False,
            "actual_count": 0,
            "keyword": keyword,
            "error": str(e)
        }
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def check_pchome_product_count(keyword, target_count=100):
    """
    檢查 PChome 購物網是否有至少 target_count 筆商品
    
    Args:
        keyword (str): 搜尋關鍵字
        target_count (int): 目標商品數量
    
    Returns:
        dict: 包含 platform, has_enough, actual_count 的字典
    """
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 無頭模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(20)
        
        print(f"正在檢查 PChome: {keyword}")
        
        encoded_keyword = quote(keyword)
        search_url = f"https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={encoded_keyword}&page=1&sort=sale/dc"
        
        driver.get(search_url)
        time.sleep(2)
        
        try:
            # PChome 的搜尋結果是 JSON 格式
            body = driver.find_element(By.TAG_NAME, "pre").text
            data = json.loads(body)
            
            # 從 JSON 中取得總商品數
            total_count = data.get("totalRows", 0)
            print(f"  → PChome 總商品數: {total_count}")
            
            has_enough = total_count >= target_count
            
            return {
                "platform": "pchome",
                "has_enough": has_enough,
                "actual_count": total_count,
                "keyword": keyword
            }
            
        except Exception as e:
            print(f"解析 PChome JSON 失敗: {e}")
            return {
                "platform": "pchome",
                "has_enough": False,
                "actual_count": 0,
                "keyword": keyword,
                "error": str(e)
            }
        
    except Exception as e:
        print(f"PChome 檢查發生錯誤: {e}")
        return {
            "platform": "pchome",
            "has_enough": False,
            "actual_count": 0,
            "keyword": keyword,
            "error": str(e)
        }
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def check_both_platforms(keyword, target_count=100):
    """
    同時檢查 momo 和 PChome 兩個平台的商品數量
    
    Args:
        keyword (str): 搜尋關鍵字
        target_count (int): 目標商品數量（預設 100）
    
    Returns:
        dict: 包含兩個平台檢查結果的字典
    """
    print(f"\n{'='*60}")
    print(f"檢查關鍵字: {keyword}")
    print(f"目標數量: {target_count} 筆")
    print(f"{'='*60}\n")
    
    # 檢查 momo
    momo_result = check_momo_product_count(keyword, target_count)
    
    # 檢查 PChome
    pchome_result = check_pchome_product_count(keyword, target_count)
    
    # 整理結果
    results = {
        "keyword": keyword,
        "target_count": target_count,
        "momo": momo_result,
        "pchome": pchome_result,
        "both_have_enough": momo_result["has_enough"] and pchome_result["has_enough"]
    }
    
    # 顯示結果
    print(f"\n{'='*60}")
    print(f"檢查結果摘要")
    print(f"{'='*60}")
    print(f"關鍵字: {keyword}")
    print(f"\nmomo 購物網:")
    print(f"  • 商品數量: {momo_result['actual_count']} 筆")
    print(f"  • 是否足夠: {'✓ 是' if momo_result['has_enough'] else '✗ 否'}")
    if "error" in momo_result:
        print(f"  • 錯誤: {momo_result['error']}")
    
    print(f"\nPChome 購物網:")
    print(f"  • 商品數量: {pchome_result['actual_count']} 筆")
    print(f"  • 是否足夠: {'✓ 是' if pchome_result['has_enough'] else '✗ 否'}")
    if "error" in pchome_result:
        print(f"  • 錯誤: {pchome_result['error']}")
    
    print(f"\n最終結論:")
    if results["both_have_enough"]:
        print(f"  ✓ 兩個平台都有至少 {target_count} 筆商品")
    else:
        print(f"  ✗ 至少有一個平台商品數量不足 {target_count} 筆")
    print(f"{'='*60}\n")
    
    return results


if __name__ == "__main__":
    print("="*60)
    print("商品數量檢查工具")
    print("檢查 momo 和 PChome 是否有足夠的商品數量")
    print("="*60)
    
    keyword = input("\n請輸入搜尋關鍵字: ").strip()
    
    if not keyword:
        print("錯誤: 關鍵字不能為空")
        exit(1)
    
    # 詢問目標數量（預設 100）
    target_input = input("請輸入目標商品數量 (預設 100): ").strip()
    target_count = int(target_input) if target_input.isdigit() else 100
    
    # 執行檢查
    results = check_both_platforms(keyword, target_count)
