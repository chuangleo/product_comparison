
   # 商品比對程式使用手冊

## Date:  16:37PM CST, Wednesday, October 15, 2025
### 1) 安裝依賴
#### step1. 安裝uv(pip,一般windows方法二擇一)
- **一般windows方法(推薦)**：
   ```bash
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

- **使用pip(有python環境下可用)**：
   ```bash
   python -m pip install --upgrade uv 
   ```
#### step2. 進入product_comparison所在的路徑
   ```bash
   cd C:\你的路徑\你的路徑\你的路徑\product_comparison
   ```
#### step3. 安裝所有套件
   ```bash
   uv sync --locked 
   ```
### 2) 安裝Mysql(Windows)
   
  - 前往 [MySQL 官方網站](https://dev.mysql.com/downloads/installer/) 下載 MySQL Installer
  - 選擇 Community（免費版） → 安裝 Developer Default 套件
  - 安裝步驟：
    - 一鍵安裝包含 Server、Workbench、Shell、Connector 等
    - 選擇安裝路徑
    - 設定 root 密碼與預設連接埠（3306）
    - 完成後會自動啟用 MySQL 服務
   
   
   
   
   
   
### 3) 程式使用流程
#### step1. 運行爬蟲程式
   ```Python
 uv run .\product_scraper.py  
   ```
   - 輸入要爬蟲的關鍵字、英文名稱以及要找的數量
   ![image](https://github.com/chuangleo/product_comparison/blob/main/image/Readme1.png)

#### step2. 運行比對網頁程式
   ```Python
 uv run .\product_compare_app.py
   ```
   
- 開啟網頁(http://127.0.0.1:5000/)，並先按下三個清空表格按鈕。
![image](https://github.com/chuangleo/product_comparison/blob/main/image/Readme2.png)
- 進行標註(以左邊商品做為root去尋找於之相符的右邊商品leaf)，找完後按下匯出商品
- 在mysql_workbench中查看是否正確存取
  - 查看root data: 在mysql_workbench中輸入下面指令並框起來按下閃電符號
    ```
    USE momo_database;
    SELECT * FROM momo_products;
     ```
    ![image](https://github.com/chuangleo/product_comparison/blob/main/image/Readme3.png)

   - 查看leaf data: 在mysql_workbench中輸入下面指令並框起來按下閃電符號
     ```
      USE products_database;
      SELECT * FROM products;
     ```
     ![image](https://github.com/chuangleo/product_comparison/blob/main/image/Readme4.png)

   - 查看pchome data: 在mysql_workbench中輸入下面指令並框起來按下閃電符號
     ```
      USE pchome_database;
      SELECT * FROM pchome_products;
     ```
     ![image](https://github.com/chuangleo/product_comparison/blob/main/image/Readme5.png)

- 在完成所有標註後匯出資料
  - 在mysql_workbench中按下Server -> Data Export 會看到下面的介面
 ![image](https://github.com/chuangleo/product_comparison/blob/main/image/Readme6.png)
  - 勾選上圖勾選的database後按下start export

****
