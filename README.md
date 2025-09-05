# 商品比對程式使用手冊

## Date:  19:28PM CST, Friday, September 5, 2025
### 1) 程式使用流程🌟
![image](https://hackmd.io/_uploads/Bkv2CV_cee.png)

### 2) 程式介紹🌟

#### 1. crawler_products.py
運行程式後在terminal輸入關鍵字及數量程式將自動從momo和pchome中抓出對應的資料儲存自.json檔中。
#### -input : 關鍵字、數量
![image](https://hackmd.io/_uploads/B1H3c2B9gl.png)
#### -output : momo、pchome商品蒐集檔。包含商品id、title、price、image、url、platform(以.json形式)
momo商品蒐集檔 : 
![image](https://hackmd.io/_uploads/S1oCWpB9eg.png)
pchome商品蒐集檔 :
![image](https://hackmd.io/_uploads/rJrWhhrqxg.png)

**備註**
正常情況下在輸入input後程式會自動開啟momo網頁抓取該頁的商品(如下圖)。
![螢幕擷取畫面 2025-09-05 190222](https://hackmd.io/_uploads/ByP0Xr_qxx.png)
但有時會發生頁面載入失敗的問題(如下兩圖)，若發生此情形請手動按重整網頁(圖中箭頭標示處)。
![螢幕擷取畫面 2025-09-05 185540](https://hackmd.io/_uploads/S1AE4SO9eg.png)
![螢幕擷取畫面 2025-09-05 185603](https://hackmd.io/_uploads/r1A4NHO5ee.png)

#### 2. compare_web.py
讀取 crawler_products.py所生成的momo商品蒐集檔、pchome商品蒐集檔來建立網頁。
#### -input :  momo、pchome商品蒐集檔
#### -output : comparison.html 
#### 3. comparison.html 
利用我們商品蒐集檔建立的網頁，可視化crawler_products.py蒐集的商品。
![image](https://hackmd.io/_uploads/rJWiwH_5ee.png)
並且藉由勾選商品後按下匯出來得到包含勾選商品title、price、image、url的文字檔selected_products.txt(如下圖)
![image](https://hackmd.io/_uploads/HyfRdrd9el.png)


