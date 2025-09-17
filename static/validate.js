// 驗證 uncertainty level 輸入
function validateUncertainty(input) {
    const value = parseInt(input.value);
    if (isNaN(value) || value < 1 || value > 100) {
        input.setCustomValidity('請輸入1到100之間的數字');
        input.reportValidity();
        input.value = '';
    } else {
        input.setCustomValidity('');
    }
}