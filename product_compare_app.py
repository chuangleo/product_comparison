import json
import os
from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# 註冊 min 函數到 Jinja2 模板環境
app.jinja_env.globals.update(min=min)

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
                id INT AUTO_INCREMENT PRIMARY KEY,
                sku VARCHAR(100) UNIQUE,
                title VARCHAR(255),
                image TEXT,
                url TEXT,
                platform VARCHAR(50),
                connect VARCHAR(100),
                price DECIMAL(10, 2)
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
            INSERT INTO pchome_products (sku, title, image, url, platform, connect, price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
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
                        product.get('price', 0)
                    ))
                    inserted_count += 1
                except Error as e:
                    print(f"插入商品時發生錯誤: {e}, 商品: {product.get('sku', '無SKU')}")
                # print(f"已插入商品到 pchome_database.pchome_products：{product}")

            print(f"總共處理了 {len(pchome_products)} 筆商品")
            print(f"成功插入了 {inserted_count} 筆商品資料到 pchome_database.pchome_products")
            
            pchome_conn.commit()

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

        if products_conn.is_connected() and momo_conn.is_connected():
            products_cursor = products_conn.cursor()
            momo_cursor = momo_conn.cursor()

            create_products_table_query = """
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sku VARCHAR(100),
                title VARCHAR(255),
                image TEXT,
                url TEXT,
                platform VARCHAR(50),
                connect VARCHAR(100),
                price DECIMAL(10, 2),
                uncertainty_level TINYINT UNSIGNED NULL CHECK (uncertainty_level BETWEEN 1 AND 100)
            )
            """
            products_cursor.execute(create_products_table_query)
            print("表格 'products_database.products' 已建立或已存在")

            create_momo_table_query = """
            CREATE TABLE IF NOT EXISTS momo_products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sku VARCHAR(100),
                title VARCHAR(255),
                image TEXT,
                url TEXT,
                platform VARCHAR(50),
                connect VARCHAR(100),
                price DECIMAL(10, 2),
                num INT
            )
            """
            momo_cursor.execute(create_momo_table_query)
            print("表格 'momo_database.momo_products' 已建立或已存在")

            insert_products_query = """
            INSERT INTO products (sku, title, image, url, platform, connect, price, uncertainty_level)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            inserted_products_count = 0
            for product in products:
                try:
                    products_cursor.execute(insert_products_query, (
                        product['sku'],
                        product['title'],
                        product['image'],
                        product['url'],
                        product['platform'],
                        product['connect'],
                        product['price'],
                        product.get('uncertainty_level', None)
                    ))
                    inserted_products_count += 1
                    print(f"已插入商品到 products_database.products：{product}")
                except Error as e:
                    print(f"插入 products 商品時發生錯誤: {e}, 商品: {product.get('sku', '無SKU')}")

            insert_momo_query = """
            INSERT IGNORE INTO momo_products (sku, title, image, url, platform, connect, price, num)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
                        product['num']
                    ))
                    if momo_cursor.rowcount > 0:
                        inserted_momo_count += 1
                        print(f"已插入商品到 momo_database.momo_products：{product}")
                    else:
                        print(f"商品 SKU {product['sku']} 已存在，跳過插入")
                except Error as e:
                    print(f"插入 MOMO 商品時發生錯誤: {e}, 商品: {product.get('sku', '無SKU')}")

            products_conn.commit()
            momo_conn.commit()
            print(f"已插入 {inserted_products_count} 筆商品資料到 products_database.products")
            print(f"已插入 {inserted_momo_count} 筆商品資料到 momo_database.momo_products")
            return jsonify({'success': True})

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
            products_cursor.execute("TRUNCATE TABLE products")
            print("已清空 products_database.products 表格")
            products_conn.commit()
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
            momo_cursor.execute("TRUNCATE TABLE momo_products")
            print("已清空 momo_database.momo_products 表格")
            momo_conn.commit()
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
            pchome_cursor.execute("TRUNCATE TABLE pchome_products")
            print("已清空 pchome_database.pchome_products 表格")
            pchome_conn.commit()
            return jsonify({'success': True})

    except Error as e:
        print(f"MySQL 錯誤: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        if 'pchome_conn' in locals() and pchome_conn.is_connected():
            pchome_cursor.close()
            pchome_conn.close()
            print("pchome_database 連線已關閉")

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