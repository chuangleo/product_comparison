import json
import os
from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from decimal import Decimal

app = Flask(__name__)

# 註冊 min 函數到 Jinja2 模板環境
app.jinja_env.globals.update(min=min)

def save_to_json_files(products_data, momo_data, pchome_data):
    """
    將三個資料庫的資料分別儲存到三個 JSON 檔案 (只保留 latest 版本)
    
    Args:
        products_data: products 表格的資料列表
        momo_data: momo_products 表格的資料列表
        pchome_data: pchome_products 表格的資料列表
    """
    # 建立 json_exports 資料夾
    export_dir = 'json_exports'
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    # 轉換 Decimal 為 float
    def convert_decimal(data):
        converted = []
        for item in data:
            new_item = {}
            for key, value in item.items():
                if isinstance(value, Decimal):
                    new_item[key] = float(value)
                else:
                    new_item[key] = value
            converted.append(new_item)
        return converted
    
    products_data = convert_decimal(products_data)
    momo_data = convert_decimal(momo_data)
    pchome_data = convert_decimal(pchome_data)
    
    # 只儲存 latest 版本的三個檔案
    latest_products_file = os.path.join(export_dir, 'products_latest.json')
    with open(latest_products_file, 'w', encoding='utf-8') as f:
        json.dump(products_data, f, ensure_ascii=False, indent=2)
    print(f"✓ 已更新 products_latest.json ({len(products_data)} 筆)")
    
    latest_momo_file = os.path.join(export_dir, 'momo_products_latest.json')
    with open(latest_momo_file, 'w', encoding='utf-8') as f:
        json.dump(momo_data, f, ensure_ascii=False, indent=2)
    print(f"✓ 已更新 momo_products_latest.json ({len(momo_data)} 筆)")
    
    latest_pchome_file = os.path.join(export_dir, 'pchome_products_latest.json')
    with open(latest_pchome_file, 'w', encoding='utf-8') as f:
        json.dump(pchome_data, f, ensure_ascii=False, indent=2)
    print(f"✓ 已更新 pchome_products_latest.json ({len(pchome_data)} 筆)")
    
    return {
        'products': len(products_data),
        'momo_products': len(momo_data),
        'pchome_products': len(pchome_data)
    }

def initialize_pchome_database(pchome_file="pchome_products.json"):
    """
    將 pchome_products.json 的內容插入 pchome_database.pchome_products 表格，插入前清空表格以避免重複
    
    Args:
        pchome_file (str): PChome 商品 JSON 檔案路徑
    """
    pchome_products = []
    if os.path.exists(pchome_file):
        with open(pchome_file, "r", encoding="utf-8") as f:
            pchome_products = json.load(f)
    else:
        print(f"錯誤：{pchome_file} 檔案不存在")
        return

    try:
        # 先連接到 MySQL 伺服器（不指定資料庫）來建立資料庫
        temp_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )
        
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("CREATE DATABASE IF NOT EXISTS pchome_database")
        temp_cursor.close()
        temp_conn.close()
        print("資料庫 'pchome_database' 已建立或已存在")
        
        # 然後連接到指定的資料庫
        pchome_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='pchome_database',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )

        if pchome_conn.is_connected():
            pchome_cursor = pchome_conn.cursor()
            create_pchome_table_query = """
            CREATE TABLE IF NOT EXISTS pchome_products (
                sku VARCHAR(100) UNIQUE,
                title VARCHAR(255),
                image TEXT,
                url TEXT,
                platform VARCHAR(50),
                connect VARCHAR(100),
                price DECIMAL(10, 2),
                query VARCHAR(100)
            )
            """
            pchome_cursor.execute(create_pchome_table_query)
            print("表格 'pchome_database.pchome_products' 已建立或已存在")

            # 檢查表格是否已有資料
            pchome_cursor.execute("SELECT COUNT(*) FROM pchome_products")
            existing_count = pchome_cursor.fetchone()[0]
            
            if existing_count > 0:
                print(f"表格中已有 {existing_count} 筆資料，跳過插入")
                return
            
            print("表格為空，開始插入商品資料")

            # 插入 PChome 商品資料
            insert_pchome_query = """
            INSERT INTO pchome_products (sku, title, image, url, platform, connect, price, query)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            inserted_count = 0
            for product in pchome_products:
                try:
                    pchome_cursor.execute(insert_pchome_query, (
                        product.get('sku', '無SKU'),
                        product.get('title', '未知商品名稱'),
                        product.get('image_url', '無圖片'),
                        product.get('url', '無連結'),
                        product.get('platform', 'pchome'),
                        '',
                        product.get('price', 0),
                        product.get('query', '')
                    ))
                    inserted_count += 1
                except Error as e:
                    print(f"插入商品時發生錯誤: {e}, 商品: {product.get('sku', '無SKU')}")
                # print(f"已插入商品到 pchome_database.pchome_products：{product}")

            print(f"總共處理了 {len(pchome_products)} 筆商品")
            print(f"成功插入了 {inserted_count} 筆商品資料到 pchome_database.pchome_products")
            
            pchome_conn.commit()
            
            # 🆕 插入後更新 pchome_products_latest.json
            try:
                # 查詢所有 pchome 資料
                pchome_cursor.execute("SELECT * FROM pchome_products")
                all_pchome = [dict(zip([col[0] for col in pchome_cursor.description], row)) 
                             for row in pchome_cursor.fetchall()]
                
                # 轉換 Decimal 為 float
                for item in all_pchome:
                    for key, value in item.items():
                        if isinstance(value, Decimal):
                            item[key] = float(value)
                
                # 儲存到 JSON
                export_dir = 'json_exports'
                if not os.path.exists(export_dir):
                    os.makedirs(export_dir)
                
                latest_pchome_file = os.path.join(export_dir, 'pchome_products_latest.json')
                with open(latest_pchome_file, 'w', encoding='utf-8') as f:
                    json.dump(all_pchome, f, ensure_ascii=False, indent=2)
                print(f"✓ 已更新 pchome_products_latest.json ({len(all_pchome)} 筆)")
            except Exception as e:
                print(f"更新 JSON 時發生錯誤: {e}")

    except Error as e:
        print(f"MySQL 錯誤: {e}")
    finally:
        if 'pchome_conn' in locals() and pchome_conn.is_connected():
            pchome_cursor.close()
            pchome_conn.close()
            print("pchome_database 連線已關閉")

def generate_comparison_html(momo_file="momo_products.json", pchome_file="pchome_products.json"):
    """
    讀取 Momo 和 PChome 的 JSON 檔案，返回數據供模板使用
    
    Args:
        momo_file (str): Momo 商品 JSON 檔案路徑
        pchome_file (str): PChome 商品 JSON 檔案路徑
    
    Returns:
        tuple: (momo_products, pchome_products, max_length)
    """
    momo_products = []
    if os.path.exists(momo_file):
        with open(momo_file, "r", encoding="utf-8") as f:
            momo_products = json.load(f)
    else:
        print(f"錯誤：{momo_file} 檔案不存在")

    pchome_products = []
    if os.path.exists(pchome_file):
        with open(pchome_file, "r", encoding="utf-8") as f:
            pchome_products = json.load(f)
    else:
        print(f"錯誤：{pchome_file} 檔案不存在")

    max_length = len(pchome_products)  # 以 PCHome 商品數量為表格行數
    
    return momo_products, pchome_products, max_length

@app.route('/')
def index():
    """
    首頁路由，渲染商品比較頁面
    """
    momo_products, pchome_products, max_length = generate_comparison_html()
    return render_template('comparison.html', 
                         momo_products=momo_products, 
                         pchome_products=pchome_products, 
                         max_length=max_length)

@app.route('/save-to-mysql', methods=['POST'])
def save_to_mysql():
    try:
        data = request.get_json()
        products = data.get('products', [])
        momo_products = data.get('momo_products', [])
        print("收到用於插入的商品資料：", products)
        print("收到用於插入的 MOMO 商品資料：", momo_products)

        # 建立資料庫（如果不存在）
        temp_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("CREATE DATABASE IF NOT EXISTS products_database")
        temp_cursor.execute("CREATE DATABASE IF NOT EXISTS momo_database")
        temp_cursor.close()
        temp_conn.close()

        products_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='products_database',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )

        momo_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='momo_database',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )

        pchome_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='pchome_database',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )

        if products_conn.is_connected() and momo_conn.is_connected() and pchome_conn.is_connected():
            products_cursor = products_conn.cursor()
            momo_cursor = momo_conn.cursor()
            pchome_cursor = pchome_conn.cursor()

            # 先檢查收到的資料
            print(f"準備處理的商品數量：{len(products)}")
            print("收到的商品資料：", json.dumps(products, ensure_ascii=False, indent=2))

            # 確認表格存在（移除 UNIQUE 限制以允許重複 SKU）
            create_products_table_query = """
            CREATE TABLE IF NOT EXISTS products (
                sku VARCHAR(100),
                title VARCHAR(255),
                image TEXT,
                url TEXT,
                platform VARCHAR(50),
                connect VARCHAR(100),
                price DECIMAL(10, 2),
                uncertainty_problem TINYINT UNSIGNED NOT NULL DEFAULT 0 CHECK (uncertainty_problem BETWEEN 0 AND 100),
                query VARCHAR(100)
            )
            """
            products_cursor.execute(create_products_table_query)
            print("表格 'products_database.products' 已建立或已存在（允許重複 SKU）")

            create_momo_table_query = """
            CREATE TABLE IF NOT EXISTS momo_products (
                sku VARCHAR(100),
                title VARCHAR(255),
                image TEXT,
                url TEXT,
                platform VARCHAR(50),
                connect VARCHAR(100),
                price DECIMAL(10, 2),
                num INT,
                query VARCHAR(100)
            )
            """
            momo_cursor.execute(create_momo_table_query)
            print("表格 'momo_database.momo_products' 已建立或已存在（允許重複 SKU）")

            # 簡單的插入語句，允許重複
            insert_products_query = """
            INSERT INTO products (sku, title, image, url, platform, connect, price, uncertainty_problem, query)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            inserted_products_count = 0
            
            for product in products:
                try:
                    # 直接插入新記錄
                    products_cursor.execute(insert_products_query, (
                        product['sku'],
                        product['title'],
                        product['image'],
                        product['url'],
                        product['platform'],
                        product['connect'],
                        product['price'],
                        product.get('uncertainty_problem', 0),
                        product.get('query', '')
                    ))
                    
                    inserted_products_count += 1
                    print(f"已新增商品：{json.dumps(product, ensure_ascii=False)}")
                    
                except Error as e:
                    print(f"處理商品時發生錯誤: {e}")
                    print(f"問題商品資料: {json.dumps(product, ensure_ascii=False)}")
                    continue  # 繼續處理下一個商品
                    
            print(f"總共處理了 {len(products)} 筆商品")
            print(f"成功新增了 {inserted_products_count} 筆")

            insert_momo_query = """
            INSERT INTO momo_products (sku, title, image, url, platform, connect, price, num, query)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            inserted_momo_count = 0
            for product in momo_products:
                try:
                    momo_cursor.execute(insert_momo_query, (
                        product['sku'],
                        product['title'],
                        product['image'],
                        product['url'],
                        product['platform'],
                        product['connect'],
                        product['price'],
                        product['num'],
                        product.get('query', '')
                    ))
                    inserted_momo_count += 1
                    print(f"已新增 MOMO 商品：{json.dumps(product, ensure_ascii=False)}")
                except Error as e:
                    print(f"插入 MOMO 商品時發生錯誤: {e}, 商品: {product.get('sku', '無SKU')}")

            products_conn.commit()
            momo_conn.commit()
            
            # 🆕 新增:匯出三個資料庫的所有資料到三個 JSON 檔案
            try:
                # 查詢 products 表格所有資料
                products_cursor.execute("SELECT * FROM products")
                all_products = [dict(zip([col[0] for col in products_cursor.description], row)) 
                               for row in products_cursor.fetchall()]
                
                # 查詢 momo_products 表格所有資料
                momo_cursor.execute("SELECT * FROM momo_products")
                all_momo = [dict(zip([col[0] for col in momo_cursor.description], row)) 
                           for row in momo_cursor.fetchall()]
                
                # 查詢 pchome_products 表格所有資料
                pchome_cursor.execute("SELECT * FROM pchome_products")
                all_pchome = [dict(zip([col[0] for col in pchome_cursor.description], row)) 
                             for row in pchome_cursor.fetchall()]
                
                # 儲存到三個 JSON 檔案
                json_counts = save_to_json_files(all_products, all_momo, all_pchome)
                
                print(f"已插入 {inserted_products_count} 筆商品資料到 products_database.products")
                print(f"已插入 {inserted_momo_count} 筆商品資料到 momo_database.momo_products")
                print(f"已匯出 JSON: products={json_counts['products']}筆, momo={json_counts['momo_products']}筆, pchome={json_counts['pchome_products']}筆")
                
                return jsonify({
                    'success': True,
                    'message': '成功儲存到資料庫並匯出 JSON',
                    'inserted': {
                        'products': inserted_products_count,
                        'momo_products': inserted_momo_count
                    },
                    'json_exported': json_counts
                })
                
            except Exception as e:
                print(f"匯出 JSON 時發生錯誤: {e}")
                # JSON 匯出失敗不影響資料庫儲存
                return jsonify({
                    'success': True,
                    'message': '資料已儲存到資料庫,但 JSON 匯出失敗',
                    'json_error': str(e)
                })

    except Error as e:
        print(f"MySQL 錯誤: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        if 'products_conn' in locals() and products_conn.is_connected():
            products_cursor.close()
            products_conn.close()
            print("products_database 連線已關閉")
        if 'momo_conn' in locals() and momo_conn.is_connected():
            momo_cursor.close()
            momo_conn.close()
            print("momo_database 連線已關閉")
        if 'pchome_conn' in locals() and pchome_conn.is_connected():
            pchome_cursor.close()
            pchome_conn.close()
            print("pchome_database 連線已關閉")

@app.route('/clear-products', methods=['POST'])
def clear_products():
    try:
        # 建立資料庫（如果不存在）
        temp_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("CREATE DATABASE IF NOT EXISTS products_database")
        temp_cursor.close()
        temp_conn.close()

        products_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='products_database',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )

        if products_conn.is_connected():
            products_cursor = products_conn.cursor()
            # 確保表格存在（若不存在就建立），以避免 TRUNCATE 時出現 1146 錯誤
            create_products_table_query = """
            CREATE TABLE IF NOT EXISTS products (
                sku VARCHAR(100),
                title VARCHAR(255),
                image TEXT,
                url TEXT,
                platform VARCHAR(50),
                connect VARCHAR(100),
                price DECIMAL(10, 2),
                uncertainty_problem TINYINT UNSIGNED NOT NULL DEFAULT 0 CHECK (uncertainty_problem BETWEEN 0 AND 100),
                query VARCHAR(100)
            )
            """
            products_cursor.execute(create_products_table_query)
            products_cursor.execute("TRUNCATE TABLE products")
            print("已清空 products_database.products 表格（若原本不存在則已建立再清空）")
            products_conn.commit()
            
            # 🆕 清空後更新 JSON 檔案(寫入空陣列)
            try:
                export_dir = 'json_exports'
                if not os.path.exists(export_dir):
                    os.makedirs(export_dir)
                
                latest_products_file = os.path.join(export_dir, 'products_latest.json')
                with open(latest_products_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                print("✓ 已清空 products_latest.json")
            except Exception as e:
                print(f"更新 JSON 時發生錯誤: {e}")
            
            return jsonify({'success': True})

    except Error as e:
        print(f"MySQL 錯誤: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        if 'products_conn' in locals() and products_conn.is_connected():
            products_cursor.close()
            products_conn.close()
            print("products_database 連線已關閉")

@app.route('/clear-momo-products', methods=['POST'])
def clear_momo_products():
    try:
        # 建立資料庫（如果不存在）
        temp_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("CREATE DATABASE IF NOT EXISTS momo_database")
        temp_cursor.close()
        temp_conn.close()

        momo_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='momo_database',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )

        if momo_conn.is_connected():
            momo_cursor = momo_conn.cursor()
            # 確保表格存在（若不存在就建立），以避免 TRUNCATE 時出現 1146 錯誤
            create_momo_table_query = """
            CREATE TABLE IF NOT EXISTS momo_products (
                sku VARCHAR(100),
                title VARCHAR(255),
                image TEXT,
                url TEXT,
                platform VARCHAR(50),
                connect VARCHAR(100),
                price DECIMAL(10, 2),
                num INT,
                query VARCHAR(100)
            )
            """
            momo_cursor.execute(create_momo_table_query)
            momo_cursor.execute("TRUNCATE TABLE momo_products")
            print("已清空 momo_database.momo_products 表格（若原本不存在則已建立再清空）")
            momo_conn.commit()
            
            # 🆕 清空後更新 JSON 檔案(寫入空陣列)
            try:
                export_dir = 'json_exports'
                if not os.path.exists(export_dir):
                    os.makedirs(export_dir)
                
                latest_momo_file = os.path.join(export_dir, 'momo_products_latest.json')
                with open(latest_momo_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                print("✓ 已清空 momo_products_latest.json")
            except Exception as e:
                print(f"更新 JSON 時發生錯誤: {e}")
            
            return jsonify({'success': True})

    except Error as e:
        print(f"MySQL 錯誤: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        if 'momo_conn' in locals() and momo_conn.is_connected():
            momo_cursor.close()
            momo_conn.close()
            print("momo_database 連線已關閉")

@app.route('/clear-pchome-products', methods=['POST'])
def clear_pchome_products():
    print("\n" + "="*50)
    print("🔴 開始執行清空 PChome 表格操作")
    print("="*50)
    try:
        # 建立資料庫（如果不存在）
        temp_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("CREATE DATABASE IF NOT EXISTS pchome_database")
        temp_cursor.close()
        temp_conn.close()
        print("✓ 資料庫連線成功")

        pchome_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='pchome_database',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )

        if pchome_conn.is_connected():
            pchome_cursor = pchome_conn.cursor()
            # 確保表格存在（若不存在就建立），以避免 TRUNCATE 時出現 1146 錯誤
            create_pchome_table_query = """
            CREATE TABLE IF NOT EXISTS pchome_products (
                sku VARCHAR(100) UNIQUE,
                title VARCHAR(255),
                image TEXT,
                url TEXT,
                platform VARCHAR(50),
                connect VARCHAR(100),
                price DECIMAL(10, 2),
                query VARCHAR(100)
            )
            """
            pchome_cursor.execute(create_pchome_table_query)
            print("✓ 表格已確認存在")
            
            # 步驟 1: 清空資料庫表格
            pchome_cursor.execute("TRUNCATE TABLE pchome_products")
            print("✅ 步驟 1: 已清空 pchome_database.pchome_products 表格")
            pchome_conn.commit()
            
            # 步驟 2: 清空 JSON 檔案(寫入空陣列)
            export_dir = 'json_exports'
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            
            latest_pchome_file = os.path.join(export_dir, 'pchome_products_latest.json')
            try:
                with open(latest_pchome_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                print("✅ 步驟 2: 已清空 pchome_products_latest.json")
            except Exception as e:
                print(f"❌ 清空 JSON 時發生錯誤: {e}")
            
            # 步驟 3: 從 pchome_products.json 讀取資料並插入到資料庫
            pchome_file = "pchome_products.json"
            inserted_count = 0
            
            if os.path.exists(pchome_file):
                with open(pchome_file, "r", encoding="utf-8") as f:
                    pchome_products = json.load(f)
                
                print(f"✓ 從 {pchome_file} 讀取到 {len(pchome_products)} 筆資料")
                
                # 插入資料到資料庫
                insert_pchome_query = """
                INSERT INTO pchome_products (sku, title, image, url, platform, connect, price, query)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                for product in pchome_products:
                    try:
                        pchome_cursor.execute(insert_pchome_query, (
                            product.get('sku', '無SKU'),
                            product.get('title', '未知商品名稱'),
                            product.get('image_url', '無圖片'),
                            product.get('url', '無連結'),
                            product.get('platform', 'pchome'),
                            '',
                            product.get('price', 0),
                            product.get('query', '')
                        ))
                        inserted_count += 1
                    except Error as e:
                        print(f"❌ 插入商品時發生錯誤: {e}, 商品: {product.get('sku', '無SKU')}")
                
                pchome_conn.commit()
                print(f"✅ 步驟 3: 成功插入了 {inserted_count} 筆商品資料到資料庫")
                
                # 步驟 4: 從資料庫讀取資料並更新 JSON 檔案
                pchome_cursor.execute("SELECT * FROM pchome_products")
                all_pchome = [dict(zip([col[0] for col in pchome_cursor.description], row)) 
                             for row in pchome_cursor.fetchall()]
                
                print(f"✓ 從資料庫讀取到 {len(all_pchome)} 筆資料")
                
                # 轉換 Decimal 為 float
                for item in all_pchome:
                    for key, value in item.items():
                        if isinstance(value, Decimal):
                            item[key] = float(value)
                
                # 寫入 JSON 檔案
                try:
                    with open(latest_pchome_file, 'w', encoding='utf-8') as f:
                        json.dump(all_pchome, f, ensure_ascii=False, indent=2)
                    print(f"✅ 步驟 4: 已將資料庫資料更新到 pchome_products_latest.json ({len(all_pchome)} 筆)")
                except Exception as e:
                    print(f"❌ 更新 JSON 時發生錯誤: {e}")
                    
            else:
                print(f"❌ 警告：{pchome_file} 檔案不存在，無法重新插入資料")
            
            print("="*50)
            print("✅ 清空 PChome 表格操作完成")
            print(f"   - 清空資料庫 ✓")
            print(f"   - 清空 JSON 檔案 ✓")
            print(f"   - 插入 {inserted_count} 筆資料到資料庫 ✓")
            print(f"   - 更新 JSON 檔案 ✓")
            print("="*50 + "\n")
            return jsonify({'success': True, 'inserted': inserted_count})

    except Error as e:
        print(f"❌ MySQL 錯誤: {e}")
        print("="*50 + "\n")
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        if 'pchome_conn' in locals() and pchome_conn.is_connected():
            pchome_cursor.close()
            pchome_conn.close()
            print("✓ pchome_database 連線已關閉")

@app.route('/initialize-pchome', methods=['POST'])
def initialize_pchome():
    try:
        initialize_pchome_database()
        return jsonify({'success': True})
    except Error as e:
        print(f"MySQL 錯誤: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/export-all-data', methods=['POST'])
def export_all_data():
    """
    匯出所有資料：
    1. 匯出 3 個 table 的 SQL 檔案（INSERT 語句）到 sql 資料夾
    2. 匯出 3 個 JSON 檔案到 json 資料夾
    3. 打包成 ZIP 檔案供下載（檔名使用 query 名稱）
    """
    print("\n" + "="*50)
    print("📦 開始執行資料匯出操作")
    print("="*50)
    
    import zipfile
    import io
    from flask import send_file
    
    try:
        # 連接到三個資料庫
        products_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='products_database',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )

        momo_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='momo_database',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )

        pchome_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='pchome_database',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )

        if products_conn.is_connected() and momo_conn.is_connected() and pchome_conn.is_connected():
            products_cursor = products_conn.cursor()
            momo_cursor = momo_conn.cursor()
            pchome_cursor = pchome_conn.cursor()
            
            # 建立記憶體中的 ZIP 檔案
            memory_file = io.BytesIO()
            
            # 獲取 query 名稱（從 momo_products 表中取得）
            query_name = "product_data"  # 預設值
            try:
                momo_cursor.execute("SELECT query FROM momo_products LIMIT 1")
                result = momo_cursor.fetchone()
                if result and result[0]:
                    query_name = result[0].replace(' ', '_')  # 將空格替換為底線
            except:
                pass
            
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                
                # === 1. 匯出 products 表的 SQL 和 JSON ===
                print("✓ 正在匯出 products 表...")
                products_cursor.execute("SELECT * FROM products")
                products_data = [dict(zip([col[0] for col in products_cursor.description], row)) 
                                for row in products_cursor.fetchall()]
                
                # 產生 SQL INSERT 語句並放入 sql 資料夾（不包含建表語句，只有資料）
                products_sql = generate_sql_insert('products', products_data, [
                    'sku', 'title', 'image', 'url', 'platform', 'connect', 'price', 'uncertainty_problem', 'query'
                ], include_create_table=False)
                zipf.writestr('sql/products.sql', products_sql)
                
                # 產生 JSON 並放入 json 資料夾
                products_json = json.dumps(convert_decimal(products_data), ensure_ascii=False, indent=2)
                zipf.writestr('json/products.json', products_json)
                print(f"  ✅ products: {len(products_data)} 筆記錄")
                
                # === 2. 匯出 momo_products 表的 SQL 和 JSON ===
                print("✓ 正在匯出 momo_products 表...")
                momo_cursor.execute("SELECT * FROM momo_products")
                momo_data = [dict(zip([col[0] for col in momo_cursor.description], row)) 
                            for row in momo_cursor.fetchall()]
                
                # 產生 SQL INSERT 語句並放入 sql 資料夾（不包含建表語句，只有資料）
                momo_sql = generate_sql_insert('momo_products', momo_data, [
                    'sku', 'title', 'image', 'url', 'platform', 'connect', 'price', 'num', 'query'
                ], include_create_table=False)
                zipf.writestr('sql/momo_products.sql', momo_sql)
                
                # 產生 JSON 並放入 json 資料夾
                momo_json = json.dumps(convert_decimal(momo_data), ensure_ascii=False, indent=2)
                zipf.writestr('json/momo_products.json', momo_json)
                print(f"  ✅ momo_products: {len(momo_data)} 筆記錄")
                
                # === 3. 匯出 pchome_products 表的 SQL 和 JSON ===
                print("✓ 正在匯出 pchome_products 表...")
                pchome_cursor.execute("SELECT * FROM pchome_products")
                pchome_data = [dict(zip([col[0] for col in pchome_cursor.description], row)) 
                              for row in pchome_cursor.fetchall()]
                
                # 產生 SQL INSERT 語句並放入 sql 資料夾（不包含建表語句，只有資料）
                pchome_sql = generate_sql_insert('pchome_products', pchome_data, [
                    'sku', 'title', 'image', 'url', 'platform', 'connect', 'price', 'query'
                ], include_create_table=False)
                zipf.writestr('sql/pchome_products.sql', pchome_sql)
                
                # 產生 JSON 並放入 json 資料夾
                pchome_json = json.dumps(convert_decimal(pchome_data), ensure_ascii=False, indent=2)
                zipf.writestr('json/pchome_products.json', pchome_json)
                print(f"  ✅ pchome_products: {len(pchome_data)} 筆記錄")
            
            # 將檔案指標移到開頭
            memory_file.seek(0)
            
            # 產生檔案名稱（使用 query 名稱）
            filename = f'{query_name}.zip'
            
            print("="*50)
            print("✅ 資料匯出完成")
            print(f"   - Query 名稱：{query_name}")
            print(f"   - 匯出檔名：{filename}")
            print(f"   - 總共匯出 {len(products_data) + len(momo_data) + len(pchome_data)} 筆記錄")
            print(f"   - 檔案結構：sql/ 和 json/ 資料夾")
            print("="*50 + "\n")
            
            return send_file(
                memory_file,
                mimetype='application/zip',
                as_attachment=True,
                download_name=filename
            )

    except Error as e:
        print(f"❌ MySQL 錯誤: {e}")
        print("="*50 + "\n")
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        if 'products_conn' in locals() and products_conn.is_connected():
            products_cursor.close()
            products_conn.close()
            print("✓ products_database 連線已關閉")
        if 'momo_conn' in locals() and momo_conn.is_connected():
            momo_cursor.close()
            momo_conn.close()
            print("✓ momo_database 連線已關閉")
        if 'pchome_conn' in locals() and pchome_conn.is_connected():
            pchome_cursor.close()
            pchome_conn.close()
            print("✓ pchome_database 連線已關閉")

def generate_sql_insert(table_name, data, columns, include_create_table=True):
    """
    產生完整的 SQL 檔案（可選擇是否包含建表語句）
    
    Args:
        table_name: 資料表名稱
        data: 資料列表（字典格式）
        columns: 欄位名稱列表
        include_create_table: 是否包含 DROP 和 CREATE TABLE 語句（預設 False，只匯出資料）
    
    Returns:
        完整的 SQL 語句字串
    """
    sql_lines = []
    
    # SQL 檔案標頭
    sql_lines.append("-- MySQL dump")
    sql_lines.append(f"-- 匯出時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_lines.append("-- ------------------------------------------------------")
    sql_lines.append("")
    
    # 設定字元集
    sql_lines.append("/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;")
    sql_lines.append("/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;")
    sql_lines.append("/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;")
    sql_lines.append("/*!50503 SET NAMES utf8mb4 */;")
    sql_lines.append("/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;")
    sql_lines.append("/*!40103 SET TIME_ZONE='+00:00' */;")
    sql_lines.append("/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;")
    sql_lines.append("/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;")
    sql_lines.append("/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;")
    sql_lines.append("/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;")
    sql_lines.append("")
    
    # 只在需要時才包含建表語句
    if include_create_table:
        # 定義各表的建表語句
        table_schemas = {
            'products': """
CREATE TABLE IF NOT EXISTS `products` (
  `sku` varchar(100) DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `image` text,
  `url` text,
  `platform` varchar(50) DEFAULT NULL,
  `connect` varchar(100) DEFAULT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `uncertainty_problem` tinyint unsigned NOT NULL DEFAULT '0',
  `query` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
""",
            'momo_products': """
CREATE TABLE IF NOT EXISTS `momo_products` (
  `sku` varchar(100) DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `image` text,
  `url` text,
  `platform` varchar(50) DEFAULT NULL,
  `connect` varchar(100) DEFAULT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `num` int DEFAULT NULL,
  `query` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
""",
            'pchome_products': """
CREATE TABLE IF NOT EXISTS `pchome_products` (
  `sku` varchar(100) DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `image` text,
  `url` text,
  `platform` varchar(50) DEFAULT NULL,
  `connect` varchar(100) DEFAULT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `query` varchar(100) DEFAULT NULL,
  UNIQUE KEY `sku` (`sku`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
"""
        }
        
        # 加入建表語句
        sql_lines.append(f"--")
        sql_lines.append(f"-- Table structure for table `{table_name}`")
        sql_lines.append(f"--")
        sql_lines.append("")
        sql_lines.append(f"DROP TABLE IF EXISTS `{table_name}`;")
        sql_lines.append(table_schemas.get(table_name, f"-- 無建表語句: {table_name}"))
        sql_lines.append("")
    
    # 加入資料
    if not data:
        sql_lines.append(f"-- {table_name} 表沒有資料")
    else:
        sql_lines.append(f"--")
        sql_lines.append(f"-- Dumping data for table `{table_name}` ({len(data)} 筆)")
        sql_lines.append(f"-- 注意：此檔案只包含資料，不會修改表結構")
        sql_lines.append(f"--")
        sql_lines.append("")
        
        # 清空表格資料（但保留表結構）
        sql_lines.append(f"-- 清空現有資料")
        sql_lines.append(f"TRUNCATE TABLE `{table_name}`;")
        sql_lines.append("")
        
        sql_lines.append("LOCK TABLES `" + table_name + "` WRITE;")
        sql_lines.append("/*!40000 ALTER TABLE `" + table_name + "` DISABLE KEYS */;")
        
        for item in data:
            values = []
            for col in columns:
                value = item.get(col)
                if value is None:
                    values.append('NULL')
                elif isinstance(value, (int, float, Decimal)):
                    values.append(str(value))
                else:
                    # 字串需要跳脫特殊字元
                    escaped_value = str(value).replace('\\', '\\\\').replace("'", "\\'")
                    values.append(f"'{escaped_value}'")
            
            values_str = ', '.join(values)
            sql_lines.append(f"INSERT INTO `{table_name}` ({', '.join([f'`{col}`' for col in columns])}) VALUES ({values_str});")
        
        sql_lines.append("/*!40000 ALTER TABLE `" + table_name + "` ENABLE KEYS */;")
        sql_lines.append("UNLOCK TABLES;")
    
    sql_lines.append("")
    
    # SQL 檔案結尾
    sql_lines.append("/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;")
    sql_lines.append("/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;")
    sql_lines.append("/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;")
    sql_lines.append("/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;")
    sql_lines.append("/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;")
    sql_lines.append("/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;")
    sql_lines.append("/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;")
    sql_lines.append("/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;")
    sql_lines.append("")
    sql_lines.append("-- Dump completed")
    
    return '\n'.join(sql_lines)

def convert_decimal(data):
    """轉換 Decimal 為 float"""
    converted = []
    for item in data:
        new_item = {}
        for key, value in item.items():
            if isinstance(value, Decimal):
                new_item[key] = float(value)
            else:
                new_item[key] = value
        converted.append(new_item)
    return converted

@app.route('/delete-labeled-product', methods=['POST'])
def delete_labeled_product():
    """
    根據 MOMO 商品的 SKU 刪除對應的標註記錄
    - 從 momo_database.momo_products 刪除該 MOMO 商品
    - 從 products_database.products 刪除所有連結到該 MOMO SKU 的 PChome 商品
    - 更新對應的 JSON 檔案
    """
    print("\n" + "="*50)
    print("🗑️ 開始執行刪除已標註商品操作")
    print("="*50)
    
    try:
        data = request.get_json()
        momo_sku = data.get('momo_sku')
        
        if not momo_sku:
            print("❌ 錯誤：未提供 MOMO SKU")
            return jsonify({'success': False, 'error': '未提供 MOMO SKU'}), 400
        
        print(f"📝 接收到刪除請求，MOMO SKU: {momo_sku}")
        
        # 連接到資料庫
        products_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='products_database',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )

        momo_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='momo_database',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )

        pchome_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='pchome_database',
            auth_plugin='caching_sha2_password',
            autocommit=True,
            use_unicode=True,
            charset='utf8mb4'
        )

        if products_conn.is_connected() and momo_conn.is_connected() and pchome_conn.is_connected():
            products_cursor = products_conn.cursor()
            momo_cursor = momo_conn.cursor()
            pchome_cursor = pchome_conn.cursor()
            
            # 步驟 1: 先查詢有多少筆 products 會被刪除
            products_cursor.execute(
                "SELECT COUNT(*) FROM products WHERE connect = %s",
                (momo_sku,)
            )
            products_count = products_cursor.fetchone()[0]
            print(f"✓ 找到 {products_count} 筆連結到 MOMO SKU {momo_sku} 的 PChome 商品")
            
            # 步驟 2: 刪除 products 表中所有 connect 等於該 momo_sku 的記錄
            delete_products_query = "DELETE FROM products WHERE connect = %s"
            products_cursor.execute(delete_products_query, (momo_sku,))
            products_deleted = products_cursor.rowcount
            print(f"✅ 步驟 1: 從 products 表刪除了 {products_deleted} 筆記錄")
            
            # 步驟 3: 刪除 momo_products 表中該 SKU 的記錄
            delete_momo_query = "DELETE FROM momo_products WHERE sku = %s"
            momo_cursor.execute(delete_momo_query, (momo_sku,))
            momo_deleted = momo_cursor.rowcount
            print(f"✅ 步驟 2: 從 momo_products 表刪除了 {momo_deleted} 筆記錄")
            
            products_conn.commit()
            momo_conn.commit()
            
            # 步驟 4: 更新 JSON 檔案
            try:
                # 查詢 products 表格所有資料
                products_cursor.execute("SELECT * FROM products")
                all_products = [dict(zip([col[0] for col in products_cursor.description], row)) 
                               for row in products_cursor.fetchall()]
                
                # 查詢 momo_products 表格所有資料
                momo_cursor.execute("SELECT * FROM momo_products")
                all_momo = [dict(zip([col[0] for col in momo_cursor.description], row)) 
                           for row in momo_cursor.fetchall()]
                
                # 查詢 pchome_products 表格所有資料
                pchome_cursor.execute("SELECT * FROM pchome_products")
                all_pchome = [dict(zip([col[0] for col in pchome_cursor.description], row)) 
                             for row in pchome_cursor.fetchall()]
                
                # 儲存到三個 JSON 檔案
                json_counts = save_to_json_files(all_products, all_momo, all_pchome)
                print(f"✅ 步驟 3: 已更新 JSON 檔案")
                print(f"   - products_latest.json: {json_counts['products']} 筆")
                print(f"   - momo_products_latest.json: {json_counts['momo_products']} 筆")
                print(f"   - pchome_products_latest.json: {json_counts['pchome_products']} 筆")
                
            except Exception as e:
                print(f"❌ 更新 JSON 時發生錯誤: {e}")
                # JSON 更新失敗不影響資料庫刪除
            
            print("="*50)
            print(f"✅ 刪除操作完成")
            print(f"   - 刪除 {products_deleted} 筆 PChome 商品")
            print(f"   - 刪除 {momo_deleted} 筆 MOMO 商品")
            print("="*50 + "\n")
            
            return jsonify({
                'success': True,
                'message': f'成功刪除 {momo_deleted} 筆 MOMO 商品和 {products_deleted} 筆相關 PChome 商品',
                'deleted': {
                    'products': products_deleted,
                    'momo_products': momo_deleted
                }
            })

    except Error as e:
        print(f"❌ MySQL 錯誤: {e}")
        print("="*50 + "\n")
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        if 'products_conn' in locals() and products_conn.is_connected():
            products_cursor.close()
            products_conn.close()
            print("✓ products_database 連線已關閉")
        if 'momo_conn' in locals() and momo_conn.is_connected():
            momo_cursor.close()
            momo_conn.close()
            print("✓ momo_database 連線已關閉")
        if 'pchome_conn' in locals() and pchome_conn.is_connected():
            pchome_cursor.close()
            pchome_conn.close()
            print("✓ pchome_database 連線已關閉")

if __name__ == "__main__":
    # 避免在 Flask reloader 重啟時重複執行初始化
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        initialize_pchome_database()
    app.run(debug=True, port=5000)