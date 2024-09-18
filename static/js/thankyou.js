document.addEventListener("DOMContentLoaded", () => {
    renderOrderNumber();
    // 查詢訂單詳情按鈕
    const checkOrderBtn = document.getElementById("checkOrderBtn");
    checkOrderBtn.addEventListener("click", () => {
        // 從 URL 獲取 orderNumber
        const orderNumber = getQueryParam("number");

        if (orderNumber) {
            const token = localStorage.getItem("token");
            if (!token) {
                window.location.href = "/";
            }
            userData = parseJwt(token);
            fetch(`/api/orders/${orderNumber}`, {
                method:"GET",
                headers:{
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.data) {
                    renderOrderDetails(data.data);
                } else {
                    alert("沒有找到相應的訂單。");
                }
            })
            .catch(error => {
                console.error("Error fetching order details:", error);
                alert("查詢訂單失敗，請稍後再試。");
            });
        } else {
            alert("未找到訂單編號，請先確保有預訂行程。");
        }
    });
});


function parseJwt(token) {
    return JSON.parse(atob(token.split(".")[1]));
}


// 函數來從 URL 獲取查詢參數
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}


// 渲染訂單編號
function renderOrderNumber() {
    const url = window.location.href;
    const orderNumber = url.split("=")[1];
    const orderNumberDiv = document.getElementById("order-number");
    if (orderNumberDiv) {
        orderNumberDiv.textContent = orderNumber;
    }
}


// 渲染訂單詳情
function renderOrderDetails(order) {
    // 訂單詳情內容
    const orderDetailsContent = `
        <div class="order-card">
            <img src="${order.spot.image}" alt="${order.spot.name} "style="width:100%; border-radius: 5px;">
            <div class="order-spot-name">${order.spot.name}</div>
            <div class="order-date">
                <span class="info-title">日期：</span>
                <span class="info-content">${order.date}</span>
            </div>
            <div class="order-time">
                <span class="info-title">時間：</span><span class="info-content">${order.time === "morning" ? "早上 9 點到下午 4 點" : "下午 2 點到晚上 9 點"}</span>
            </div>
            <div class="order-price">
                <span class="info-title">費用：</span><span class="info-content">${order.price}</span>
            </div>
            <div class="order-address">
                <span class="info-title">地址：</span><span class="info-content">${order.spot.address}</span>
            </div>
            <hr class="order-divider">
            <div class="contact-name">
                <span class="info-title">聯絡姓名：</span><span class="info-content">${order.contact.name}</span>
            </div>
            <div class="contact-email">
                <span class="info-title">聯絡信箱：</span><span class="info-content">${order.contact.email}</span>
            </div>
            <div class="contact-phone">
                <span class="info-title">手機號碼：</span><span class="info-content">${order.contact.phone}</span>
            </div>
        </div>
    `;

    // 插入訂單詳情到彈出框
    const orderDetailsContainer = document.getElementById("orderDetailsContainer");
    orderDetailsContainer.innerHTML = orderDetailsContent;

    // 顯示彈出框和背景遮罩
    document.getElementById("overlay").classList.remove("hide");
    document.getElementById("orderDetailsModal").classList.remove("hide");
}

// 關閉彈出框
document.getElementById("closeModal").addEventListener("click", function() {
    document.getElementById("overlay").classList.add("hide");
    document.getElementById("orderDetailsModal").classList.add("hide");
});