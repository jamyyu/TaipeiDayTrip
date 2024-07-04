document.addEventListener("DOMContentLoaded", () => {
    // 避免清除瀏覽器登出
    const token = localStorage.getItem("token");
    if (!token) {
        window.location.href = "/";
    }
    // fetch to render
    userData = parseJwt(token);
    fetch("/api/booking",{
        method:"GET",
        headers:{
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        }
    })
    .then(reponse => reponse.json())
    .then(result => {
        data = result.data;
        if (data != "null"){
            localStorage.setItem("bookingData", JSON.stringify(data));
            renderBooking(data);
        }
        else{
            renderNoBooking(userData);
        }
    })
    // 點擊刪除
    const iconDelete = document.getElementById("icon-delete");
    iconDelete.addEventListener("click",() => {
        fetch("api/booking",{
            method:"DELETE",
            headers:{
                "Authorization": `Bearer ${token}`,
            }
        })
        .then(response => {return response.json()})
        .then(result => {
            if (result.ok === true){
                window.location.reload()
            }
        })
    })
})


function parseJwt(token) {
    // 直接從 token 中提取 payload 部分，解碼並解析為 JSON
    return JSON.parse(atob(token.split(".")[1]));
}

function renderBooking(data) {
    const userName = document.getElementById("user-name");
    userName.textContent = userData["name"];
    const attractionImg = document.getElementById("attraction-img");
    attractionImg.src = data["attraction"]["image"];
    const attractionName = document.getElementById("attraction-name");
    attractionName.textContent = data["attraction"]["name"];
    const bookingDate = document.getElementById("booking-date");
    bookingDate.textContent = data["date"];
    const bookingTime = document.getElementById("booking-time");
    if (data["time"] === "morning"){
        data["time"] = "早上 9 點到下午 4 點"
    }else{
        data["time"] = "下午 2 點到晚上 9 點"
    }
    bookingTime.textContent = data["time"];
    const bookingPrice = document.getElementById("booking-price");
    bookingPrice.textContent = data["price"];
    const attractionAddress = document.getElementById("attraction-address");
    attractionAddress.textContent = data["attraction"]["address"];
    const contactName = document.getElementById("contact-name");
    contactName.value = userData["name"];
    const contactEmail = document.getElementById("contact-email");
    contactEmail.value = userData["email"];
    const confirmTotal = document.getElementById("confirm-total");
    confirmTotal.textContent = data["price"];
}


function renderNoBooking(userData) {
    const mainElement = document.getElementById("main-content");
    mainElement.textContent = "";
    mainElement.style.flex = "0";

    const sectionView = document.createElement("section");
    sectionView.classList.add("view");

    const divHeadline = document.createElement("div");
    divHeadline.classList.add("headline");

    const divHello = document.createElement("div");
    divHello.classList.add("font19-700");
    divHello.textContent = "您好，";

    const divUserName = document.createElement('div');
    divUserName.id = "user-name";
    divUserName.textContent = userData["name"];
    divUserName.classList.add("font19-700");

    const divSchedule = document.createElement("div");
    divSchedule.classList.add("font19-700");
    divSchedule.textContent = "，待預定的行程如下：";

    const divNoSchedule = document.createElement("div");
    divNoSchedule.classList.add("no-schedule");
    divNoSchedule.textContent = "目前沒有任何待預定的行程";

    const footerElement = document.getElementById("footer-content");
    footerElement.style.flex = "1";
    footerElement.style.position = "relative";

    const copyright =document.querySelector(".copyright");
    copyright.style.position = "absolute";
    copyright.style.top = "40px";


    // 構建結構
    divHeadline.appendChild(divHello);
    divHeadline.appendChild(divUserName);
    divHeadline.appendChild(divSchedule);
    sectionView.appendChild(divHeadline);
    sectionView.appendChild(divNoSchedule);
    mainElement.appendChild(sectionView);
}