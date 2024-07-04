document.addEventListener("DOMContentLoaded", () => {
    // 預約時間點擊
    const morning = document.getElementById("morning");
    const afternoon = document.getElementById("afternoon");
    const price = document.getElementById("price")
    morning.addEventListener("click", () => {
        price.textContent = "2000"
    })
    afternoon.addEventListener("click", () => {
        price.textContent = "2500"
    })
    // 處理景點ID
    const pathParts = window.location.pathname.split("/");
    const attractionId = pathParts[pathParts.length - 1];
    if (attractionId) {
        fetchAttraction(attractionId);
    } else {
        console.error("No attraction ID provided in the URL");
    }
    // 開始預約行程按鈕點擊
    const bookingForm = document.getElementById("booking-block__form");
    const signinSignup = document.querySelector(".signin-signup");
    bookingForm.addEventListener("submit", (e) => {
        e.preventDefault();
        if (signinSignup.classList.contains("hide")) {
            let currentUrl = window.location.href;
            let parts = currentUrl.split("/");
            let attractionId = parts[parts.length-1];
            const bookingDate = document.getElementById("booking-date").value;
            const bookingTime = document.querySelector('input[name="time"]:checked').value;
            const bookingPrice = document.getElementById("price").textContent;
            const token = localStorage.getItem("token");
            //console.log(attractionId,bookingDate,bookingTime,bookingPrice);
            fetch("/api/booking",{
                method:"POST",
                headers:{
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ "attractionId": attractionId, "date": bookingDate, "time": bookingTime, "price": bookingPrice })
            })
            .then(response => {return response.json()})
            .then(result => {
                if (result.ok){
                    window.location.href = "/booking";
                }
                if (result.detail[0].msg === "Value error, Date must be after today"){
                    alert("預定日期需在明日之後")
                }
            })
        } else {
            signinDialog.showModal();
        }
    })
});


function fetchAttraction(attractionId){
    fetch((`/api/attraction/${attractionId}`))
    .then(response => response.json())
    .then(result => {
        data = result.data
        if (data){
            renderAttractions(data)
        }
        else{
            window.location.href = "/";
        }
    })
    .catch(error => {
        console.error("Error fetching data:", error);
    });
}


function renderAttractions(data){
    title = data.name;
    cat = data.category;
    mrt = data.mrt;
    info = data.description;
    address = data.address;
    transport = data.transport;
    images = data.images;
    const replaceTitle = document.querySelector(".booking-block__title");
    replaceTitle.textContent = title;
    const replaceCAT = document.querySelector(".booking-block__cat");
    replaceCAT.textContent = `${cat} at ${mrt}`;
    const replaceInfo = document.querySelector(".attraction-info");
    replaceInfo.textContent = info;
    const replaceAddress = document.querySelector(".attraction-address_info");
    replaceAddress.textContent = address;
    const replaceTransport = document.querySelector(".attraction-transport_info");
    replaceTransport.textContent = transport;
    const imgBlock = document.querySelector(".img-block");
    const dots =document.querySelector(".img-block_dots");

    images.forEach((image, index) => {
        const imgElement = document.createElement("img");
        imgElement.src = image;
        if (index === 0) {
            imgElement.classList.add("active");
        }
        imgBlock.appendChild(imgElement);
        const dot = document.createElement("span");
        if (index === 0) {
            dot.classList.add("active");
        }
        dot.addEventListener("click", () => showImage(index));
        dots.appendChild(dot);
    });
}


const prevBtn = document.querySelector(".img-block_icon-prevbtn");
const nextBtn = document.querySelector(".img-block_icon-nextbtn");

prevBtn.addEventListener("click", () => showImage((currentIndex - 1 + images.length) % images.length));
nextBtn.addEventListener("click", () => showImage((currentIndex + 1) % images.length));

let currentIndex = 0

function showImage(index){
    const imgBlock = document.querySelector(".img-block");
    const images = imgBlock.querySelectorAll("img"); 
    images.forEach(image => {
        image.classList.remove("active")
    })
    
    currentIndex = index
    const newImg = images[currentIndex];
    newImg.classList.add("active");

    updateDots();
}


function updateDots(){
    const dots =document.querySelector(".img-block_dots");
    const dot = dots.querySelector(".active");
    if(dot){
        dot.classList.remove("active");
    }
    const newDot =dots.children[currentIndex];
    newDot.classList.add("active");
}