import json
import os

def generate_comparison_html(momo_file="momo_products.json", pchome_file="pchome_products.json", output_file="comparison.html"):
    """
    讀取 Momo 和 PChome 的 JSON 檔案，生成帶有勾選框的比較網頁，並支持匯出僅勾選的商品為 TXT 檔案
    
    Args:
        momo_file (str): Momo 商品 JSON 檔案路徑
        pchome_file (str): PChome 商品 JSON 檔案路徑
        output_file (str): 輸出的 HTML 檔案名稱
    """
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
        #exportButton {
            display: block;
            margin: 20px auto;
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
                            <input type="checkbox" id="momo_{momo_product['id']}" name="selected_products" value="{momo_product['id']}">
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
            print(f"Debug: raw_image_url={raw_image_url}, processed_image_url={image_url}")  # 除錯日誌
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
                            <input type="checkbox" id="pchome_{pchome_product['id']}" name="selected_products" value="{pchome_product['id']}">
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
    </div>

    <script>
        // 確保 DOM 載入後執行
        window.onload = function() {
            const exportButton = document.getElementById('exportButton');
            if (!exportButton) {
                console.error('Export button not found!');
                return;
            }

            exportButton.addEventListener('click', function() {
                console.log('Button clicked'); // 除錯日誌
                const checkboxes = document.getElementsByName('selected_products');
                if (!checkboxes || checkboxes.length === 0) {
                    console.error('No checkboxes found!');
                    alert('未找到可選商品！');
                    return;
                }

                const selectedItems = Array.from(checkboxes)
                    .filter(checkbox => checkbox.checked)
                    .map(checkbox => {
                        const [platform, id] = checkbox.id.split('_');
                        return { id: id, platform: platform };
                    });

                if (selectedItems.length === 0) {
                    console.log('No items selected');
                    alert('請先勾選至少一個商品！');
                    return;
                }

                console.log('Selected IDs:', selectedItems); // 除錯日誌
                // 內嵌 JSON 數據
                const momoProducts = """ + json.dumps(momo_products) + """;
                const pchomeProducts = """ + json.dumps(pchome_products) + """;

                // 僅輸出勾選的商品，格式為 "商品名稱-售價"
                let txtContent = '';
                const gSku = [] ;
                txtContent += `======MOMO商品=======\n`;
                for (const item of selectedItems) {
                    if (item.platform === 'momo') {
                        const momoProduct = momoProducts.find(p => String(p.id) === item.id);
                        const product = momoProduct;
                        if (momoProduct) {
                            gSku.push(momoProduct['sku']);
                            txtContent += `title: ${momoProduct['title']}\n`;
                            txtContent += `price: NT$${momoProduct['price'].toLocaleString()}\n`;
                            txtContent += `image: ${momoProduct['image_url']}\n`;
                            txtContent += `url: ${momoProduct['url']}\n`;
                            txtContent += `\n`;
                        }
                    }
                }

                txtContent += `======PCHOME商品=======\n`;
                for (const item of selectedItems) {
                    if (item.platform === 'pchome') {
                        const pchomeProduct = pchomeProducts.find(p => String(p.id) === item.id);
                        if (pchomeProduct) {
                            const momoSku = gSku[0] ;
                            txtContent += `sku: ${pchomeProduct['sku']}\n`;
                            txtContent += `title: ${pchomeProduct['title']}\n`;
                            txtContent += `image: ${pchomeProduct['image_url']}\n`;
                            txtContent += `url: ${pchomeProduct['url']}\n`;
                            txtContent += `platform: ${pchomeProduct['platform']}\n`;
                            txtContent += `connect: ${momoSku}\n`;
                            txtContent += `price: NT$${pchomeProduct['price'].toLocaleString()}\n`;
                            txtContent += `\n`;
                        }
                    }
                }

                if (!txtContent.trim()) {
                    console.error('No content to export');
                    alert('未找到勾選的商品對應內容！');
                    return;
                }

                console.log('TXT Content:', txtContent); // 除錯日誌
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
        };
    </script>
</body>
</html>
"""

    # 儲存 HTML 檔案
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML 網頁已生成：{output_file}")

if __name__ == "__main__":
    generate_comparison_html()