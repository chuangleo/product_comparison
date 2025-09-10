import json
import os
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

def initialize_pchome_database(pchome_file="pchome_products.json"):
    """
    將 pchome_products.json 的內容插入 pchome_database.pchome_products 表格
    
    Args:
        pchome_file (str): PChome 商品 JSON 檔案路徑
    """
    # 讀取 PChome JSON 檔案
    pchome_products = []
    if os.path.exists(pchome_file):
        with open(pchome_file, "r", encoding="utf-8") as f:
            pchome_products = json.load(f)
    else:
        print(f"錯誤：{pchome_file} 檔案不存在")
        return

    try:
        # 連接到 pchome_database 資料庫
        pchome_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='pchome_database'
        )

        if pchome_conn.is_connected():
            pchome_cursor = pchome_conn.cursor()

            # 建立 pchome_products 表格
            create_pchome_table_query = """
            CREATE TABLE IF NOT EXISTS pchome_products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sku VARCHAR(100),
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

            # 插入 PChome 商品資料
            insert_pchome_query = """
            INSERT INTO pchome_products (sku, title, image, url, platform, connect, price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            for product in pchome_products:
                pchome_cursor.execute(insert_pchome_query, (
                    product.get('sku', '無SKU'),
                    product.get('title', '未知商品名稱'),
                    product.get('image_url', '無圖片'),
                    product.get('url', '無連結'),
                    product.get('platform', 'pchome'),
                    '',  # connect 初始設為空
                    product.get('price', 0)
                ))
                print(f"已插入商品到 pchome_database.pchome_products：{product}")

            pchome_conn.commit()
            print(f"已插入 {pchome_cursor.rowcount} 筆商品資料到 pchome_database.pchome_products")

    except Error as e:
        print(f"MySQL 錯誤: {e}")
    finally:
        if 'pchome_conn' in locals() and pchome_conn.is_connected():
            pchome_cursor.close()
            pchome_conn.close()
            print("pchome_database 連線已關閉")

def generate_comparison_html(momo_file="momo_products.json", pchome_file="pchome_products.json", output_file="static/comparison.html"):
    """
    讀取 Momo 和 PChome 的 JSON 檔案，生成帶有勾選框的比較網頁，支持匯出僅勾選的商品為 TXT 檔案，
    將勾選的商品插入 products_database.products 和 momo_database.momo_products 表格，並支援清空資料庫
    
    Args:
        momo_file (str): Momo 商品 JSON 檔案路徑
        pchome_file (str): PChome 商品 JSON 檔案路徑
        output_file (str): 輸出的 HTML 檔案名稱，預設為 static/comparison.html
    """
    # 確保 static 資料夾存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # 讀取 Momo JSON 檔案
    momo_products = []
    if os.path.exists(momo_file):
        with open(momo_file, "r", encoding="utf-8") as f:
            momo_products = json.load(f)
    else:
        print(f"錯誤：{momo_file} 檔案不存在")

    # 讀取 PChome JSON 檔案
    pchome_products = []
    if os.path.exists(pchome_file):
        with open(pchome_file, "r", encoding="utf-8") as f:
            pchome_products = json.load(f)
    else:
        print(f"錯誤：{pchome_file} 檔案不存在")

    # 計算最大商品數量
    max_length = max(len(momo_products), len(pchome_products))

    # HTML 模板
    html_content = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>商品比較與標註 - Momo vs PChome</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .comparison-container {
            max-width: 1200px;
            margin: 0 auto;
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: center;
            vertical-align: top;
        }
        th {
            background-color: #f2f2f2;
            font-size: 1.2em;
        }
        .product-card {
            width: 500px;
            height: 300px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            overflow-y: auto;
        }
        .product-content {
            padding: 5px;
        }
        .product-image {
            width: 100%;
            height: 150px;
            border-radius: 5px;
            object-fit: contain;
        }
        .product-title {
            font-size: 1.1em;
            margin: 5px 0;
            color: #333;
            word-wrap: break-word;
            overflow-wrap: break-word;
            height: 80px;
            overflow-y: auto;
        }
        .product-price {
            font-size: 1em;
            color: #e44d26;
            margin: 5px 0;
            height: 20px;
        }
        .buy-button {
            display: inline-block;
            padding: 8px 16px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 5px;
            height: 30px;
            line-height: 30px;
            text-align: center;
        }
        .buy-button:hover {
            background-color: #0056b3;
        }
        .empty-card {
            height: 300px;
            background-color: #f9f9f9;
            color: #888;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .checkbox-container {
            margin-top: 5px;
        }
        #exportButton, #clearProductsButton, #clearMomoButton, #clearPchomeButton {
            display: inline-block;
            margin: 20px 10px;
            padding: 10px 20px;
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        #exportButton:hover {
            background-color: #218838;
        }
        #clearProductsButton, #clearMomoButton, #clearPchomeButton {
            background-color: #dc3545;
        }
        #clearProductsButton:hover, #clearMomoButton:hover, #clearPchomeButton:hover {
            background-color: #c82333;
        }
    </style>
</head>
<body>
    <div class="comparison-container">
        <table>
            <thead>
                <tr>
                    <th>Momo 商品</th>
                    <th>PChome 商品</th>
                </tr>
            </thead>
            <tbody>
"""

    # 填充表格內容
    for i in range(max_length):
        momo_product = momo_products[i] if i < len(momo_products) else None
        pchome_product = pchome_products[i] if i < len(pchome_products) else None

        html_content += "<tr>"
        # Momo 商品
        if momo_product:
            title = momo_product['title'].replace('"', '&quot;').replace("'", '&apos;')
            image_url = momo_product['image_url'] if momo_product['image_url'] else "https://via.placeholder.com/300x200?text=No+Image"
            html_content += f"""
                <td>
                    <div class="product-card">
                        <div class="product-content">
                            <img src="{image_url}" alt="{title}" class="product-image">
                            <h3 class="product-title">{title}</h3>
                            <p class="product-price">NT${momo_product['price']:,}</p>
                            <a href="{momo_product['url']}" class="buy-button" target="_blank">立即購買</a>
                        </div>
                        <div class="checkbox-container">
                            <input type="checkbox" id="momo_{momo_product['id']}" name="selected_products" value="{momo_product['id']}" data-platform="momo">
                            <label for="momo_{momo_product['id']}">選取</label>
                        </div>
                    </div>
                </td>
            """
        else:
            html_content += "<td><div class='empty-card'>無對應商品</div></td>"

        # PChome 商品
        if pchome_product:
            title = pchome_product['title'].replace('"', '&quot;').replace("'", '&apos;')
            raw_image_url = pchome_product['image_url']
            image_url = raw_image_url if raw_image_url and raw_image_url.startswith("http") else "https://cs.ecimg.tw" + (raw_image_url if raw_image_url else "")
            print(f"Debug: raw_image_url={raw_image_url}, processed_image_url={image_url}")
            if not image_url or not image_url.startswith("http"):
                image_url = "https://via.placeholder.com/300x200?text=No+Image"
            html_content += f"""
                <td>
                    <div class="product-card">
                        <div class="product-content">
                            <img src="{image_url}" alt="{title}" class="product-image">
                            <h3 class="product-title">{title}</h3>
                            <p class="product-price">NT${pchome_product['price']:,}</p>
                            <a href="{pchome_product['url']}" class="buy-button" target="_blank">立即購買</a>
                        </div>
                        <div class="checkbox-container">
                            <input type="checkbox" id="pchome_{pchome_product['id']}" name="selected_products" value="{pchome_product['id']}" data-platform="pchome">
                            <label for="pchome_{pchome_product['id']}">選取</label>
                        </div>
                    </div>
                </td>
            """
        else:
            html_content += "<td><div class='empty-card'>無對應商品</div></td>"

        html_content += "</tr>"

    html_content += """
            </tbody>
        </table>
        <button id="exportButton">匯出勾選商品</button>
        <button id="clearProductsButton">清空 leaf 表格</button>
        <button id="clearMomoButton">清空 root 表格</button>
        <button id="clearPchomeButton">清空 All PCHome Products 表格</button>
    </div>

    <script>
        // 確保 DOM 載入後執行
        window.onload = function() {
            const exportButton = document.getElementById('exportButton');
            const clearProductsButton = document.getElementById('clearProductsButton');
            const clearMomoButton = document.getElementById('clearMomoButton');
            const clearPchomeButton = document.getElementById('clearPchomeButton');

            if (!exportButton) {
                console.error('Export button not found!');
                return;
            }
            if (!clearProductsButton) {
                console.error('Clear Products button not found!');
                return;
            }
            if (!clearMomoButton) {
                console.error('Clear MOMO button not found!');
                return;
            }
            if (!clearPchomeButton) {
                console.error('Clear PCHome button not found!');
                return;
            }

            exportButton.addEventListener('click', function() {
                console.log('Export button clicked');
                const checkboxes = document.getElementsByName('selected_products');
                if (!checkboxes || checkboxes.length === 0) {
                    console.error('No checkboxes found!');
                    alert('未找到可選商品！');
                    return;
                }

                const selectedItems = Array.from(checkboxes)
                    .filter(checkbox => checkbox.checked)
                    .map(checkbox => ({
                        id: checkbox.value,
                        platform: checkbox.getAttribute('data-platform')
                    }));

                if (selectedItems.length === 0) {
                    console.log('No items selected');
                    alert('請先勾選至少一個商品！');
                    return;
                }

                console.log('Selected IDs:', selectedItems);
                const momoProducts = """ + json.dumps(momo_products) + """;
                const pchomeProducts = """ + json.dumps(pchome_products) + """;

                // 收集勾選的商品資料並生成 txtContent
                let txtContent = '';
                const gSku = [];
                const selectedProducts = [];
                const momoSelectedProducts = [];
                txtContent += `======MOMO商品=======\n`;
                for (const item of selectedItems) {
                    if (item.platform === 'momo') {
                        const momoProduct = momoProducts.find(p => String(p.id) === item.id);
                        if (momoProduct) {
                            const product = momoProduct;
                            gSku.push(momoProduct['sku'] || '無SKU');
                            txtContent += `sku: ${momoProduct['sku'] || '無SKU'}\n`;
                            txtContent += `title: ${momoProduct['title'] || '未知商品名稱'}\n`;
                            txtContent += `image: ${momoProduct['image_url'] || '無圖片'}\n`;
                            txtContent += `url: ${momoProduct['url'] || '無連結'}\n`;
                            txtContent += `platform: ${momoProduct['platform'] || 'momo'}\n`;
                            txtContent += `price: NT$${momoProduct['price']?.toLocaleString() || '未知價格'}\n`;
                            txtContent += `\n`;
                            momoSelectedProducts.push({
                                sku: momoProduct['sku'] || '無SKU',
                                title: momoProduct['title'] || '未知商品名稱',
                                image: momoProduct['image_url'] || '無圖片',
                                url: momoProduct['url'] || '無連結',
                                platform: momoProduct['platform'] || 'momo',
                                connect: '',
                                price: momoProduct['price'] || 0,
                                num: 0 // 初始值，稍後更新
                            });
                        }
                    }
                }

                txtContent += `======PCHOME商品=======\n`;
                let pchomeCount = 0;
                for (const item of selectedItems) {
                    if (item.platform === 'pchome') {
                        const pchomeProduct = pchomeProducts.find(p => String(p.id) === item.id);
                        if (pchomeProduct) {
                            const momoSku = gSku[0] || '無對應MOMO商品';
                            pchomeCount++;
                            txtContent += `sku: ${pchomeProduct['sku'] || '無SKU'}\n`;
                            txtContent += `title: ${pchomeProduct['title'] || '未知商品名稱'}\n`;
                            txtContent += `image: ${pchomeProduct['image_url'] || '無圖片'}\n`;
                            txtContent += `url: ${pchomeProduct['url'] || '無連結'}\n`;
                            txtContent += `platform: ${pchomeProduct['platform'] || 'pchome'}\n`;
                            txtContent += `connect: ${momoSku}\n`;
                            txtContent += `price: NT$${pchomeProduct['price']?.toLocaleString() || '未知價格'}\n`;
                            txtContent += `\n`;
                            selectedProducts.push({
                                sku: pchomeProduct['sku'] || '無SKU',
                                title: pchomeProduct['title'] || '未知商品名稱',
                                image: pchomeProduct['image_url'] || '無圖片',
                                url: pchomeProduct['url'] || '無連結',
                                platform: pchomeProduct['platform'] || 'pchome',
                                connect: momoSku,
                                price: pchomeProduct['price'] || 0
                            });
                        }
                    }
                }

                // 更新 momoSelectedProducts 中每個物件的 num 欄位為 PCHome 商品迴圈次數
                momoSelectedProducts.forEach(product => {
                    product.num = pchomeCount;
                });

                if (!txtContent.trim()) {
                    console.error('No content to export');
                    alert('未找到勾選的商品對應內容！');
                    return;
                }

                console.log('TXT Content:', txtContent);
                console.log('Selected Products:', selectedProducts);
                console.log('MOMO Selected Products:', momoSelectedProducts);
                // 發送勾選的商品資料到後端
                fetch('/save-to-mysql', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ products: selectedProducts, momo_products: momoSelectedProducts })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('資料成功儲存到 MySQL');
                    } else {
                        console.error('儲存到 MySQL 失敗:', data.error);
                        alert('儲存到資料庫失敗！');
                    }
                })
                .catch(error => {
                    console.error('發送資料到後端失敗:', error);
                    alert('無法連接到伺服器！');
                });

                // 創建 Blob 並下載 TXT
                const blob = new Blob([txtContent], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'selected_products.txt';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                alert('匯出成功！');
            });

            clearProductsButton.addEventListener('click', function() {
                console.log('Clear Products button clicked');
                if (!confirm('確定要清空 products_database.products 表格嗎？此操作無法復原！')) {
                    return;
                }

                fetch('/clear-products', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('products_database.products 已清空');
                        alert('products_database.products 表格已清空！');
                    } else {
                        console.error('清空 products_database.products 失敗:', data.error);
                        alert('清空 products_database.products 失敗：' + data.error);
                    }
                })
                .catch(error => {
                    console.error('清空 products_database.products 請求失敗:', error);
                    alert('無法連接到伺服器！');
                });
            });

            clearMomoButton.addEventListener('click', function() {
                console.log('Clear MOMO button clicked');
                if (!confirm('確定要清空 momo_database.momo_products 表格嗎？此操作無法復原！')) {
                    return;
                }

                fetch('/clear-momo-products', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('momo_database.momo_products 已清空');
                        alert('momo_database.momo_products 表格已清空！');
                    } else {
                        console.error('清空 momo_database.momo_products 失敗:', data.error);
                        alert('清空 momo_database.momo_products 失敗：' + data.error);
                    }
                })
                .catch(error => {
                    console.error('清空 momo_database.momo_products 請求失敗:', error);
                    alert('無法連接到伺服器！');
                });
            });

            clearPchomeButton.addEventListener('click', function() {
                console.log('Clear PCHome button clicked');
                if (!confirm('確定要清空 pchome_database.pchome_products 表格嗎？此操作無法復原！')) {
                    return;
                }

                fetch('/clear-pchome-products', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('pchome_database.pchome_products 已清空');
                        alert('pchome_database.pchome_products 表格已清空！');
                    } else {
                        console.error('清空 pchome_database.pchome_products 失敗:', data.error);
                        alert('清空 pchome_database.pchome_products 失敗：' + data.error);
                    }
                })
                .catch(error => {
                    console.error('清空 pchome_database.pchome_products 請求失敗:', error);
                    alert('無法連接到伺服器！');
                });
            });
        };
    </script>
</body>
</html>
"""

    # 儲存 HTML 檔案
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML 網頁已生成：{output_file}")

@app.route('/save-to-mysql', methods=['POST'])
def save_to_mysql():
    try:
        data = request.get_json()
        products = data.get('products', [])
        momo_products = data.get('momo_products', [])
        print("收到用於插入的商品資料：", products)
        print("收到用於插入的 MOMO 商品資料：", momo_products)

        # 連接到 products_database 資料庫
        products_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='products_database'
        )

        # 連接到 momo_database 資料庫
        momo_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='momo_database'
        )

        if products_conn.is_connected() and momo_conn.is_connected():
            products_cursor = products_conn.cursor()
            momo_cursor = momo_conn.cursor()

            # 建立 products 表格（products_database）
            create_products_table_query = """
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sku VARCHAR(100),
                title VARCHAR(255),
                image TEXT,
                url TEXT,
                platform VARCHAR(50),
                connect VARCHAR(100),
                price DECIMAL(10, 2)
            )
            """
            products_cursor.execute(create_products_table_query)
            print("表格 'products_database.products' 已建立或已存在")

            # 建立 momo_products 表格（momo_database）
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

            # 插入商品資料到 products 表格
            insert_products_query = """
            INSERT INTO products (sku, title, image, url, platform, connect, price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            for product in products:
                products_cursor.execute(insert_products_query, (
                    product['sku'],
                    product['title'],
                    product['image'],
                    product['url'],
                    product['platform'],
                    product['connect'],
                    product['price']
                ))
                print(f"已插入商品到 products_database.products：{product}")

            # 插入商品資料到 momo_products 表格
            insert_momo_query = """
            INSERT INTO momo_products (sku, title, image, url, platform, connect, price, num)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            for product in momo_products:
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
                print(f"已插入商品到 momo_database.momo_products：{product}")

            products_conn.commit()
            momo_conn.commit()
            print(f"已插入 {products_cursor.rowcount} 筆商品資料到 products_database.products")
            if momo_cursor.rowcount > 0:
                print(f"已插入 {momo_cursor.rowcount} 筆商品資料到 momo_database.momo_products")
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
        # 連接到 products_database 資料庫
        products_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='products_database'
        )

        if products_conn.is_connected():
            products_cursor = products_conn.cursor()

            # 清空 products 表格
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
        # 連接到 momo_database 資料庫
        momo_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='momo_database'
        )

        if momo_conn.is_connected():
            momo_cursor = momo_conn.cursor()

            # 清空 momo_products 表格
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
        # 連接到 pchome_database 資料庫
        pchome_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='pchome_database'
        )

        if pchome_conn.is_connected():
            pchome_cursor = pchome_conn.cursor()

            # 清空 pchome_products 表格
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

if __name__ == "__main__":
    # 初始化 pchome_database.pchome_products
    initialize_pchome_database()
    generate_comparison_html()
    app.run(debug=True, port=5000)