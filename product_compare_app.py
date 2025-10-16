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

if __name__ == "__main__":
    # 避免在 Flask reloader 重啟時重複執行初始化
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        initialize_pchome_database()
    app.run(debug=True, port=5000)