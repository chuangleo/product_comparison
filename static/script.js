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
          query: momoProduct["query"] || "",
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
        const uncertaintyInput = document.getElementById(
          `uncertainty_${item.id}`
        );
        const uncertaintyLevel = uncertaintyInput
          ? parseInt(uncertaintyInput.value) || 0
          : 0;

        selectedProducts.push({
          sku: pchomeProduct["sku"] || "無SKU",
          title: pchomeProduct["title"] || "未知商品名稱",
          image: pchomeProduct["image_url"] || "無圖片",
          url: pchomeProduct["url"] || "無連結",
          platform: pchomeProduct["platform"] || "pchome",
          connect: momoSku,
          price: pchomeProduct["price"] || 0,
          uncertainty_problem: uncertaintyLevel,
          query: pchomeProduct["query"] || "",
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
      "確定要清空 pchome_database.pchome_products 表格嗎？此操作無法復原！"
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
      if (data.success) {
        console.log("pchome_database.pchome_products 已清空");
        showMessage("pchome_database.pchome_products 表格已清空！");
        // 重新初始化 pchome_database 以恢復數據
        return fetch("/initialize-pchome", {
          method: "POST",
        });
      } else {
        console.error("清空 pchome_database.pchome_products 失敗:", data.error);
        hideLoading();
        showMessage(
          "清空 pchome_database.pchome_products 失敗：" + data.error,
          "error"
        );
        throw new Error(data.error);
      }
    })
    .then((response) => response.json())
    .then((data) => {
      hideLoading();
      if (data.success) {
        console.log("pchome_database.pchome_products 已重新初始化");
        showMessage("pchome_database.pchome_products 表格已重新初始化！");
      } else {
        console.error(
          "重新初始化 pchome_database.pchome_products 失敗:",
          data.error
        );
        showMessage(
          "重新初始化 pchome_database.pchome_products 失敗：" + data.error,
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
        const cardId =
          firstCheckbox.getAttribute("data-platform") +
          "-card-" +
          firstCheckbox.value;
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

  exportButton.addEventListener("click", handleExport);
  clearProductsButton.addEventListener("click", handleClearProducts);
  clearMomoButton.addEventListener("click", handleClearMomo);
  clearPchomeButton.addEventListener("click", handleClearPchome);

  // 搜索功能初始化
  initializeSearch();

  // 初始隱藏載入動畫
  hideLoading();
};

// 搜索功能相關變數
let filteredPchomeProducts = [];
let currentSearchTerm = "";

// 初始化搜索功能
function initializeSearch() {
  const searchInput = document.getElementById("searchInput");
  const clearSearchButton = document.getElementById("clearSearchButton");

  if (!searchInput || !clearSearchButton) {
    console.error("搜索元素未找到");
    return;
  }

  // 初始化時顯示所有商品
  filteredPchomeProducts = [...pchomeProducts];
  updateSearchStats();

  // 搜索輸入事件
  searchInput.addEventListener("input", function () {
    currentSearchTerm = this.value.trim();
    performSearch();
    toggleClearButton();
  });

  // 清除搜索按鈕事件
  clearSearchButton.addEventListener("click", function () {
    searchInput.value = "";
    currentSearchTerm = "";
    clearSearch();
    toggleClearButton();
    searchInput.focus();
  });

  // Enter 鍵搜索
  searchInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      performSearch();
    }
  });
}

// 執行搜索
function performSearch() {
  if (!currentSearchTerm) {
    clearSearch();
    return;
  }

  const searchTermLower = currentSearchTerm.toLowerCase();
  const tableBody = document.getElementById("tableBody");
  const rows = tableBody.getElementsByTagName("tr");

  let visibleCount = 0;

  // 遍歷所有表格行
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const pchomeCells = row.getElementsByTagName("td");

    if (pchomeCells.length >= 2) {
      const pchomeCell = pchomeCells[1]; // PChome 商品在第二欄
      const titleElement = pchomeCell.querySelector(".product-title");

      if (titleElement) {
        const title = titleElement.textContent || titleElement.innerText;
        const titleMatch = title.toLowerCase().includes(searchTermLower);

        // 檢查是否有 SKU 匹配（如果有的話）
        const skuMatch = false; // 暫時先不檢查 SKU，因為它沒有直接顯示在頁面上

        if (titleMatch || skuMatch) {
          row.style.display = "";
          visibleCount++;
          // 高亮搜索關鍵字
          titleElement.innerHTML = highlightSearchTerm(
            title,
            currentSearchTerm
          );
        } else {
          row.style.display = "none";
        }
      } else {
        // 如果沒有商品標題（空行），也隱藏
        row.style.display = "none";
      }
    }
  }

  updateSearchStats(visibleCount);
}

// 清除搜索
function clearSearch() {
  filteredPchomeProducts = [...pchomeProducts];
  currentSearchTerm = "";

  const tableBody = document.getElementById("tableBody");
  const rows = tableBody.getElementsByTagName("tr");

  // 顯示所有行並清除高亮
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    row.style.display = "";

    // 清除高亮效果
    const titleElements = row.querySelectorAll(".product-title");
    titleElements.forEach((titleElement) => {
      const title = titleElement.textContent || titleElement.innerText;
      // 移除 mark 標籤，只保留純文字
      titleElement.innerHTML = title.replace(
        /<mark[^>]*>(.*?)<\/mark>/gi,
        "$1"
      );
    });
  }

  updateSearchStats(rows.length);
}

// 更新搜索統計資訊
function updateSearchStats(visibleCount = null) {
  const searchResults = document.getElementById("searchResults");
  if (!searchResults) return;

  if (currentSearchTerm && visibleCount !== null) {
    const totalCount = pchomeProducts.length;
    searchResults.innerHTML = `搜索 "<span class="highlight">${currentSearchTerm}</span>" 找到 <span class="highlight">${visibleCount}</span> / ${totalCount} 個商品`;
  } else {
    searchResults.innerHTML = "顯示全部商品";
  }
}

// 切換清除按鈕顯示狀態
function toggleClearButton() {
  const clearButton = document.getElementById("clearSearchButton");
  const searchInput = document.getElementById("searchInput");

  if (!clearButton || !searchInput) return;

  if (searchInput.value.trim()) {
    clearButton.classList.add("visible");
  } else {
    clearButton.classList.remove("visible");
  }
}

// 高亮搜索關鍵字
function highlightSearchTerm(text, searchTerm) {
  if (!searchTerm || !text) return text;

  const regex = new RegExp(`(${searchTerm})`, "gi");
  return text.replace(
    regex,
    '<mark style="background: #fff3cd; padding: 1px 2px; border-radius: 2px;">$1</mark>'
  );
}
