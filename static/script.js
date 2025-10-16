// 全域變數
let momoProducts = [];
let pchomeProducts = [];
let maxLength = 0;

// 初始化函數
function initializeData() {
  // 從 HTML 中的 JSON script 標籤讀取資料
  const momoDataElement = document.getElementById("momo-data");
  const pchomeDataElement = document.getElementById("pchome-data");
  const maxLengthDataElement = document.getElementById("max-length-data");

  if (momoDataElement) {
    momoProducts = JSON.parse(momoDataElement.textContent);
  }
  if (pchomeDataElement) {
    pchomeProducts = JSON.parse(pchomeDataElement.textContent);
  }
  if (maxLengthDataElement) {
    maxLength = JSON.parse(maxLengthDataElement.textContent);
  }

  updateStats();
}

// 更新統計資訊
function updateStats() {
  document.getElementById("momoCount").textContent = momoProducts.length;
  document.getElementById("pchomeCount").textContent = pchomeProducts.length;
  updateSelectedCount();
}

// 更新已選商品數量
function updateSelectedCount() {
  const checkboxes = document.getElementsByName("selected_products");
  const selectedCount = Array.from(checkboxes).filter(
    (cb) => cb.checked
  ).length;
  document.getElementById("selectedCount").textContent = selectedCount;
}

// 顯示載入動畫
function showLoading() {
  document.getElementById("loadingSpinner").style.display = "block";
}

// 隱藏載入動畫
function hideLoading() {
  document.getElementById("loadingSpinner").style.display = "none";
}

// 顯示訊息
function showMessage(message, type = "success") {
  // 移除舊訊息
  const oldMessage = document.querySelector(".message");
  if (oldMessage) {
    oldMessage.remove();
  }

  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${type}`;
  messageDiv.textContent = message;

  const container = document.querySelector(".comparison-container");
  container.insertBefore(messageDiv, container.firstChild);

  // 3秒後自動移除
  setTimeout(() => {
    if (messageDiv.parentNode) {
      messageDiv.remove();
    }
  }, 3000);
}

function renderTable(momoIndex = "all") {
  const tableBody = document.getElementById("tableBody");
  tableBody.innerHTML = "";

  const filteredMomoProducts =
    momoIndex === "all" ? momoProducts : [momoProducts[momoIndex - 1]];

  for (let i = 0; i < maxLength; i++) {
    const momoProduct =
      filteredMomoProducts[0] && momoIndex !== "all"
        ? filteredMomoProducts[0]
        : filteredMomoProducts[i] || null;
    const pchomeProduct = pchomeProducts[i] || null;

    let rowHtml = "<tr>";

    // Momo 商品
    if (momoProduct) {
      const title = momoProduct.title
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&apos;");
      const imageUrl =
        momoProduct.image_url ||
        "https://via.placeholder.com/300x200?text=No+Image";
      rowHtml += `
                <td>
                    <div class="product-card" id="momo-card-${
                      momoProduct.id
                    }" onclick="toggleProductSelection('momo', ${
        momoProduct.id
      }, event)">
                        <div class="product-content">
                            <div class="image-container">
                                <a href="${
                                  momoProduct.url
                                }" target="_blank" rel="noopener" class="image-link" onclick="event.stopPropagation()">
                                    <img src="${imageUrl}" alt="${title}" class="product-image" 
                                         onerror="this.src='https://via.placeholder.com/300x200?text=圖片載入失敗'">
                                    <div class="image-overlay">
                                        <div class="buy-overlay">
                                            <i class="fas fa-shopping-cart"></i>
                                            <span>立即購買</span>
                                        </div>
                                    </div>
                                </a>
                            </div>
                            <h3 class="product-title" title="${title}">${title}</h3>
                            <p class="product-price">NT$${momoProduct.price.toLocaleString()}</p>
                        </div>
                        <div class="checkbox-container">
                            <input type="checkbox" id="momo_${
                              momoProduct.id
                            }" name="selected_products" value="${
        momoProduct.id
      }" data-platform="momo" style="display: none;">
                            <label for="momo_${
                              momoProduct.id
                            }" style="display: none;">
                                <i class="fas fa-check"></i> 選取
                            </label>
                        </div>
                    </div>
                </td>
            `;
    } else {
      rowHtml += `<td><div class="empty-card">
                    <i class="fas fa-box-open"></i><br>無對應商品
                  </div></td>`;
    }

    // PChome 商品
    if (pchomeProduct) {
      const title = pchomeProduct.title
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&apos;");
      const rawImageUrl = pchomeProduct.image_url;
      let imageUrl =
        rawImageUrl && rawImageUrl.startsWith("http")
          ? rawImageUrl
          : "https://cs.ecimg.tw" + (rawImageUrl || "");
      if (!imageUrl || !imageUrl.startsWith("http")) {
        imageUrl = "https://via.placeholder.com/300x200?text=No+Image";
      }
      rowHtml += `
                <td>
                    <div class="product-card" id="pchome-card-${
                      pchomeProduct.id
                    }" onclick="toggleProductSelection('pchome', ${
        pchomeProduct.id
      }, event)">
                        <div class="product-content">
                            <div class="image-container">
                                <a href="${
                                  pchomeProduct.url
                                }" target="_blank" rel="noopener" class="image-link" onclick="event.stopPropagation()">
                                    <img src="${imageUrl}" alt="${title}" class="product-image"
                                         onerror="this.src='https://via.placeholder.com/300x200?text=圖片載入失敗'">
                                    <div class="image-overlay">
                                        <div class="buy-overlay">
                                            <i class="fas fa-shopping-cart"></i>
                                            <span>立即購買</span>
                                        </div>
                                    </div>
                                </a>
                            </div>
                            <h3 class="product-title" title="${title}">${title}</h3>
                            <p class="product-price">NT$${pchomeProduct.price.toLocaleString()}</p>
                        </div>
                        <div class="checkbox-container">
                            <input type="checkbox" id="pchome_${
                              pchomeProduct.id
                            }" name="selected_products" value="${
        pchomeProduct.id
      }" data-platform="pchome" style="display: none;">
                            <label for="pchome_${
                              pchomeProduct.id
                            }" style="display: none;">
                                <i class="fas fa-check"></i> 選取
                            </label>
                        </div>
                    </div>
                </td>
            `;
    } else {
      rowHtml += `<td><div class="empty-card">
                    <i class="fas fa-box-open"></i><br>無對應商品
                  </div></td>`;
    }

    // 新增 Uncertainty Level 輸入欄位
    rowHtml += `<td class="uncertainty-cell">`;
    if (pchomeProduct) {
      rowHtml += `<input type="number" class="uncertainty-input" 
                         min="1" max="100"
                         id="uncertainty_${pchomeProduct.id}"
                         placeholder="1-100"
                         onchange="validateUncertainty(this)">`;
    } else {
      rowHtml += `-`;
    }
    rowHtml += `</td>`;

    rowHtml += "</tr>";
    tableBody.innerHTML += rowHtml;
  }

  updateSelectedCount();
}

// 新的產品選擇切換函數
function toggleProductSelection(platform, productId, event) {
  event.preventDefault();

  const checkbox = document.getElementById(`${platform}_${productId}`);
  const card = document.getElementById(`${platform}-card-${productId}`);

  if (checkbox && card) {
    // 切換 checkbox 狀態
    checkbox.checked = !checkbox.checked;

    // 更新卡片視覺狀態
    if (checkbox.checked) {
      card.classList.add("selected");
    } else {
      card.classList.remove("selected");
    }

    // 更新統計數字
    updateSelectedCount();

    // 添加點擊反饋效果
    card.style.transform = "scale(0.98)";
    setTimeout(() => {
      card.style.transform = "";
    }, 150);
  }
}

// 切換卡片選中狀態（舊函數，保留向後兼容）
function toggleCardSelection(checkbox) {
  const cardId =
    checkbox.getAttribute("data-platform") + "-card-" + checkbox.value;
  const card = document.getElementById(cardId);
  if (card) {
    if (checkbox.checked) {
      card.classList.add("selected");
    } else {
      card.classList.remove("selected");
    }
  }
}

function handleExport() {
  console.log("Export button clicked");
  showLoading();

  const checkboxes = document.getElementsByName("selected_products");
  if (!checkboxes || checkboxes.length === 0) {
    console.error("No checkboxes found!");
    hideLoading();
    showMessage("未找到可選商品！", "error");
    return;
  }

  const selectedItems = Array.from(checkboxes)
    .filter((checkbox) => checkbox.checked)
    .map((checkbox) => ({
      id: checkbox.value,
      platform: checkbox.getAttribute("data-platform"),
    }));

  if (selectedItems.length === 0) {
    console.log("No items selected");
    hideLoading();
    showMessage("請先勾選至少一個商品！", "error");
    return;
  }

  console.log("Selected IDs:", selectedItems);
  let txtContent = "";
  const gSku = [];
  const selectedProducts = [];
  const momoSelectedProducts = [];
  txtContent += `======MOMO商品=======\n`;

  for (const item of selectedItems) {
    if (item.platform === "momo") {
      const momoProduct = momoProducts.find((p) => String(p.id) === item.id);
      if (momoProduct) {
        gSku.push(momoProduct["sku"] || "無SKU");
        txtContent += `sku: ${momoProduct["sku"] || "無SKU"}\n`;
        txtContent += `title: ${momoProduct["title"] || "未知商品名稱"}\n`;
        txtContent += `image: ${momoProduct["image_url"] || "無圖片"}\n`;
        txtContent += `url: ${momoProduct["url"] || "無連結"}\n`;
        txtContent += `platform: ${momoProduct["platform"] || "momo"}\n`;
        txtContent += `query: ${momoProduct["query"] || "無關鍵字"}\n`;
        txtContent += `price: NT$${
          momoProduct["price"]?.toLocaleString() || "未知價格"
        }\n`;
        txtContent += `\n`;
        momoSelectedProducts.push({
          sku: momoProduct["sku"] || "無SKU",
          title: momoProduct["title"] || "未知商品名稱",
          image: momoProduct["image_url"] || "無圖片",
          url: momoProduct["url"] || "無連結",
          platform: momoProduct["platform"] || "momo",
          connect: "root",
          price: momoProduct["price"] || 0,
          num: 0, // 初始值，稍後更新
          query: momoProduct["query"] || ""
        });
      }
    }
  }

  txtContent += `======PCHOME商品=======\n`;
  let pchomeCount = 0;
  for (const item of selectedItems) {
    if (item.platform === "pchome") {
      const pchomeProduct = pchomeProducts.find(
        (p) => String(p.id) === item.id
      );
      if (pchomeProduct) {
        const momoSku = gSku[0] || "無對應MOMO商品";
        pchomeCount++;
        txtContent += `sku: ${pchomeProduct["sku"] || "無SKU"}\n`;
        txtContent += `title: ${pchomeProduct["title"] || "未知商品名稱"}\n`;
        txtContent += `image: ${pchomeProduct["image_url"] || "無圖片"}\n`;
        txtContent += `url: ${pchomeProduct["url"] || "無連結"}\n`;
        txtContent += `platform: ${pchomeProduct["platform"] || "pchome"}\n`;
        txtContent += `connect: ${momoSku}\n`;
        txtContent += `query: ${pchomeProduct["query"] || "無關鍵字"}\n`;
        txtContent += `price: NT$${
          pchomeProduct["price"]?.toLocaleString() || "未知價格"
        }\n`;
        txtContent += `\n`;
        // 獲取 uncertainty level 值
        const uncertaintyInput = document.getElementById(`uncertainty_${item.id}`);
        const uncertaintyLevel = uncertaintyInput ? (parseInt(uncertaintyInput.value) || 0) : 0;
        
        selectedProducts.push({
          sku: pchomeProduct["sku"] || "無SKU",
          title: pchomeProduct["title"] || "未知商品名稱",
          image: pchomeProduct["image_url"] || "無圖片",
          url: pchomeProduct["url"] || "無連結",
          platform: pchomeProduct["platform"] || "pchome",
          connect: momoSku,
          price: pchomeProduct["price"] || 0,
          uncertainty_problem: uncertaintyLevel,
          query: pchomeProduct["query"] || ""
        });
      }
    }
  }

  // 更新 momoSelectedProducts 中每個物件的 num 欄位為 PCHome 商品迴圈次數
  momoSelectedProducts.forEach((product) => {
    product.num = pchomeCount;
  });

  if (!txtContent.trim()) {
    console.error("No content to export");
    hideLoading();
    showMessage("未找到勾選的商品對應內容！", "error");
    return;
  }

  console.log("TXT Content:", txtContent);
  console.log("Selected Products:", selectedProducts);
  console.log("MOMO Selected Products:", momoSelectedProducts);

  // 發送勾選的商品資料到後端
  fetch("/save-to-mysql", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      products: selectedProducts,
      momo_products: momoSelectedProducts,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        console.log("資料成功儲存到 MySQL");
        // 創建 Blob 並下載 TXT
        const blob = new Blob([txtContent], { type: "text/plain" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "selected_products.txt";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        hideLoading();
        showMessage(`匯出成功！已匯出 ${selectedItems.length} 個商品`);
      } else {
        console.error("儲存到 MySQL 失敗:", data.error);
        hideLoading();
        showMessage("儲存到資料庫失敗！", "error");
      }
    })
    .catch((error) => {
      console.error("發送資料到後端失敗:", error);
      hideLoading();
      showMessage("無法連接到伺服器！", "error");
    });
}

function handleClearProducts() {
  console.log("Clear Products button clicked");
  if (
    !confirm("確定要清空 products_database.products 表格嗎？此操作無法復原！")
  ) {
    return;
  }

  showLoading();
  fetch("/clear-products", {
    method: "POST",
  })
    .then((response) => response.json())
    .then((data) => {
      hideLoading();
      if (data.success) {
        console.log("products_database.products 已清空");
        showMessage("products_database.products 表格已清空！");
      } else {
        console.error("清空 products_database.products 失敗:", data.error);
        showMessage(
          "清空 products_database.products 失敗：" + data.error,
          "error"
        );
      }
    })
    .catch((error) => {
      hideLoading();
      console.error("清空 products_database.products 請求失敗:", error);
      showMessage("無法連接到伺服器！", "error");
    });
}

function handleClearMomo() {
  console.log("Clear MOMO button clicked");
  if (
    !confirm("確定要清空 momo_database.momo_products 表格嗎？此操作無法復原！")
  ) {
    return;
  }

  showLoading();
  fetch("/clear-momo-products", {
    method: "POST",
  })
    .then((response) => response.json())
    .then((data) => {
      hideLoading();
      if (data.success) {
        console.log("momo_database.momo_products 已清空");
        showMessage("momo_database.momo_products 表格已清空！");
      } else {
        console.error("清空 momo_database.momo_products 失敗:", data.error);
        showMessage(
          "清空 momo_database.momo_products 失敗：" + data.error,
          "error"
        );
      }
    })
    .catch((error) => {
      hideLoading();
      console.error("清空 momo_database.momo_products 請求失敗:", error);
      showMessage("無法連接到伺服器！", "error");
    });
}

function handleClearPchome() {
  console.log("Clear PCHome button clicked");
  if (
    !confirm(
      "確定要清空並重新載入 pchome_database.pchome_products 表格嗎？\n\n執行內容：\n1. 清空資料庫\n2. 清空 JSON 檔案\n3. 從 pchome_products.json 重新載入資料\n4. 更新 JSON 檔案"
    )
  ) {
    return;
  }

  showLoading();
  fetch("/clear-pchome-products", {
    method: "POST",
  })
    .then((response) => response.json())
    .then((data) => {
      hideLoading();
      if (data.success) {
        const insertedCount = data.inserted || 0;
        console.log(`pchome_database.pchome_products 已清空並重新載入 ${insertedCount} 筆資料`);
        showMessage(`成功！已清空並重新載入 ${insertedCount} 筆 PChome 商品資料！`);
      } else {
        console.error("處理 pchome_database.pchome_products 失敗:", data.error);
        showMessage(
          "處理 pchome_database.pchome_products 失敗：" + data.error,
          "error"
        );
      }
    })
    .catch((error) => {
      hideLoading();
      console.error("處理 pchome_database.pchome_products 請求失敗:", error);
      showMessage("無法連接到伺服器！", "error");
    });
}

function handleDeleteLabeled() {
  console.log("Delete Labeled button clicked");
  
  // 顯示模態對話框
  openDeleteModal();
}

function openDeleteModal() {
  const modal = document.getElementById('deleteModal');
  const totalProducts = document.getElementById('totalProducts');
  const productNumber = document.getElementById('productNumber');
  
  // 更新商品總數
  if (totalProducts) {
    totalProducts.textContent = momoProducts.length;
  }
  
  // 設置商品編號輸入框的最大值
  if (productNumber) {
    productNumber.max = momoProducts.length;
    productNumber.placeholder = `請輸入商品編號 (1-${momoProducts.length})`;
  }
  
  // 清空輸入框
  if (productNumber) productNumber.value = '';
  const productSku = document.getElementById('productSku');
  if (productSku) productSku.value = '';
  
  // 重置為預設選項（商品編號）
  const numberRadio = document.querySelector('input[name="deleteMethod"][value="number"]');
  if (numberRadio) {
    numberRadio.checked = true;
    toggleDeleteMethod();
  }
  
  // 顯示模態對話框
  if (modal) {
    modal.style.display = 'block';
    // 聚焦到輸入框
    setTimeout(() => {
      if (productNumber) productNumber.focus();
    }, 100);
  }
}

function closeDeleteModal() {
  const modal = document.getElementById('deleteModal');
  if (modal) {
    modal.style.display = 'none';
  }
}

function toggleDeleteMethod() {
  const selectedMethod = document.querySelector('input[name="deleteMethod"]:checked').value;
  const numberSection = document.getElementById('numberInputSection');
  const skuSection = document.getElementById('skuInputSection');
  
  if (selectedMethod === 'number') {
    numberSection.style.display = 'block';
    skuSection.style.display = 'none';
    document.getElementById('productNumber').focus();
  } else {
    numberSection.style.display = 'none';
    skuSection.style.display = 'block';
    document.getElementById('productSku').focus();
  }
}

function confirmDelete() {
  const selectedMethod = document.querySelector('input[name="deleteMethod"]:checked').value;
  let momoSku = null;
  let momoProduct = null;
  
  if (selectedMethod === 'number') {
    // 方法 1: 使用商品編號
    const productNumber = document.getElementById('productNumber').value.trim();
    
    if (!productNumber) {
      showMessage('❌ 請輸入商品編號！', 'error');
      return;
    }
    
    const index = parseInt(productNumber) - 1;
    
    if (isNaN(index) || index < 0 || index >= momoProducts.length) {
      showMessage(`❌ 無效的商品編號！請輸入 1 到 ${momoProducts.length} 之間的數字`, 'error');
      return;
    }
    
    momoProduct = momoProducts[index];
    momoSku = momoProduct.sku;
    
    // 關閉模態對話框
    closeDeleteModal();
    
    // 顯示商品資訊確認
    if (!confirm(
      `📦 確認要刪除以下商品？\n\n` +
      `🔢 商品編號：第 ${index + 1} 項\n` +
      `🏷️ SKU：${momoSku}\n` +
      `📝 商品名稱：${momoProduct.title.substring(0, 50)}${momoProduct.title.length > 50 ? '...' : ''}\n` +
      `💰 價格：NT$ ${momoProduct.price.toLocaleString()}\n\n` +
      `⚠️ 此操作將會：\n` +
      `1. 刪除該 MOMO 商品\n` +
      `2. 刪除所有連結到該 MOMO 商品的 PChome 商品\n` +
      `3. 更新 JSON 檔案\n\n` +
      `❗ 此操作無法復原！`
    )) {
      return;
    }
    
  } else {
    // 方法 2: 使用 MOMO SKU
    const inputSku = document.getElementById('productSku').value.trim();
    
    if (!inputSku) {
      showMessage('❌ 請輸入 MOMO SKU！', 'error');
      return;
    }
    
    momoSku = inputSku;
    
    // 嘗試找到對應的商品以顯示詳細資訊
    momoProduct = momoProducts.find(p => p.sku === momoSku);
    
    // 關閉模態對話框
    closeDeleteModal();
    
    if (momoProduct) {
      // 找到商品，顯示詳細確認
      const productIndex = momoProducts.indexOf(momoProduct) + 1;
      if (!confirm(
        `📦 確認要刪除以下商品？\n\n` +
        `🔢 商品編號：第 ${productIndex} 項\n` +
        `🏷️ SKU：${momoSku}\n` +
        `📝 商品名稱：${momoProduct.title.substring(0, 50)}${momoProduct.title.length > 50 ? '...' : ''}\n` +
        `💰 價格：NT$ ${momoProduct.price.toLocaleString()}\n\n` +
        `⚠️ 此操作將會：\n` +
        `1. 刪除該 MOMO 商品\n` +
        `2. 刪除所有連結到該 MOMO 商品的 PChome 商品\n` +
        `3. 更新 JSON 檔案\n\n` +
        `❗ 此操作無法復原！`
      )) {
        return;
      }
    } else {
      // 未找到商品，簡單確認
      if (!confirm(
        `⚠️ 確認要刪除 MOMO SKU「${momoSku}」及其所有相關的標註商品嗎？\n\n` +
        `（注意：在目前顯示的商品列表中未找到此 SKU，但仍會嘗試從資料庫刪除）\n\n` +
        `❗ 此操作無法復原！`
      )) {
        return;
      }
    }
  }
  
  // 執行刪除
  console.log(`準備刪除 MOMO SKU: ${momoSku}`);
  showLoading();
  
  fetch("/delete-labeled-product", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      momo_sku: momoSku
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      hideLoading();
      if (data.success) {
        console.log("刪除成功：", data);
        showMessage(
          `✅ 成功！${data.message}\n` +
          `- 刪除了 ${data.deleted.momo_products} 筆 MOMO 商品\n` +
          `- 刪除了 ${data.deleted.products} 筆 PChome 商品`
        );
      } else {
        console.error("刪除失敗:", data.error);
        showMessage("❌ 刪除失敗：" + data.error, "error");
      }
    })
    .catch((error) => {
      hideLoading();
      console.error("刪除請求失敗:", error);
      showMessage("❌ 無法連接到伺服器！", "error");
    });
}

// 自動勾選第一個商品
function autoSelectFirstProduct() {
  // 延遲執行，確保 DOM 更新完成
  setTimeout(() => {
    const checkboxes = document.getElementsByName("selected_products");
    if (checkboxes && checkboxes.length > 0) {
      const firstCheckbox = checkboxes[0];
      if (firstCheckbox && !firstCheckbox.checked) {
        // 自動勾選第一個商品
        firstCheckbox.checked = true;
        
        // 更新對應的卡片視覺狀態
        const cardId = firstCheckbox.getAttribute("data-platform") + "-card-" + firstCheckbox.value;
        const card = document.getElementById(cardId);
        if (card) {
          card.classList.add("selected");
        }
        
        // 更新統計數字
        updateSelectedCount();
      }
    }
  }, 100);
}

// 確保 DOM 載入後執行
window.onload = function () {
  // 初始化資料
  initializeData();

  // 初始渲染表格
  renderTable();

  // 監聽下拉選單變化
  const momoIndexSelect = document.getElementById("momoIndexSelect");
  if (momoIndexSelect) {
    momoIndexSelect.addEventListener("change", function () {
      const selectedIndex = this.value;
      renderTable(selectedIndex);
      // 自動勾選第一個商品
      autoSelectFirstProduct();
    });
  }

  // 綁定按鈕事件
  const exportButton = document.getElementById("exportButton");
  const clearProductsButton = document.getElementById("clearProductsButton");
  const clearMomoButton = document.getElementById("clearMomoButton");
  const clearPchomeButton = document.getElementById("clearPchomeButton");
  const deleteLabeledButton = document.getElementById("deleteLabeled");

  if (!exportButton) {
    console.error("Export button not found!");
    return;
  }
  if (!clearProductsButton) {
    console.error("Clear Products button not found!");
    return;
  }
  if (!clearMomoButton) {
    console.error("Clear MOMO button not found!");
    return;
  }
  if (!clearPchomeButton) {
    console.error("Clear PCHome button not found!");
    return;
  }
  if (!deleteLabeledButton) {
    console.error("Delete Labeled button not found!");
    return;
  }

  exportButton.addEventListener("click", handleExport);
  clearProductsButton.addEventListener("click", handleClearProducts);
  clearMomoButton.addEventListener("click", handleClearMomo);
  clearPchomeButton.addEventListener("click", handleClearPchome);
  deleteLabeledButton.addEventListener("click", handleDeleteLabeled);

  // 綁定刪除方法切換事件
  const deleteMethodRadios = document.getElementsByName('deleteMethod');
  deleteMethodRadios.forEach(radio => {
    radio.addEventListener('change', toggleDeleteMethod);
  });
  
  // 綁定模態對話框的鍵盤事件
  const modal = document.getElementById('deleteModal');
  if (modal) {
    // 點擊模態背景關閉
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        closeDeleteModal();
      }
    });
    
    // ESC 鍵關閉模態對話框
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && modal.style.display === 'block') {
        closeDeleteModal();
      }
    });
  }
  
  // 綁定輸入框的 Enter 鍵
  const productNumber = document.getElementById('productNumber');
  const productSku = document.getElementById('productSku');
  
  if (productNumber) {
    productNumber.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        confirmDelete();
      }
    });
  }
  
  if (productSku) {
    productSku.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        confirmDelete();
      }
    });
  }

  // 初始隱藏載入動畫
  hideLoading();
};
