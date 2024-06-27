let observer = null;
const loadedPages = new Set(); 


document.addEventListener("DOMContentLoaded", () => {
    //載入第0頁圖片
    fetchAttractions(0, "");
});


function fetchAttractions(page, keyword) {
    fetch(`/api/attractions?page=${page}&keyword=${keyword}`)
        .then(response => {return response.json()})
        .then(result => {
            const nextPage = result.nextPage;
            const filteredAttractionList = [];
            const attractionsList = result.data;
            attractionsList.forEach(attraction => {
                const imgURL = attraction.images[0];
                filteredAttractionList.push({id :attraction.id, name: attraction.name, mrt: attraction.mrt, cat: attraction.category, img: imgURL});
            });
            renderAttractions(filteredAttractionList);
            return nextPage;
        })
        .then(nextPage => {
            if (nextPage !== null) {
                observeFooter(nextPage, keyword);
            }
        })
        .catch(error => {
            console.error("Error fetching data:", error);
        });
}


function renderAttractions(filteredAttractionList) {
    const attractionView = document.getElementById("attraction-view");
    const attractionBlock = document.createElement("div");
    attractionBlock.className = "attraction-block";
    attractionView.appendChild(attractionBlock);
    for (let i = 1; i <= filteredAttractionList.length; i++) {
        const link = document.createElement("a");
        link.setAttribute("href", `/attraction/${filteredAttractionList[i - 1].id}`);
        attractionBlock.appendChild(link);

        const attraction = document.createElement("div");
        attraction.className = `a${i} attraction`;
        link.appendChild(attraction);

        const imgElement = document.createElement("img");
        imgElement.src = filteredAttractionList[i - 1].img;
        imgElement.alt = "attraction-image";
        attraction.appendChild(imgElement);

        const attractionTitle = document.createElement("div");
        attractionTitle.className = "attraction-title";
        attractionTitle.textContent = filteredAttractionList[i - 1].name;
        attraction.appendChild(attractionTitle);

        const attractionSubtitle = document.createElement("div");
        attractionSubtitle.className = "attraction-subtitle";
        attraction.appendChild(attractionSubtitle);

        const MRT = document.createElement("div");
        MRT.className = "mrt";
        MRT.textContent = filteredAttractionList[i - 1].mrt;
        attractionSubtitle.appendChild(MRT);

        const CAT = document.createElement("div");
        CAT.className = "category";
        CAT.textContent = filteredAttractionList[i - 1].cat;
        attractionSubtitle.appendChild(CAT);
    }
}


function observeFooter(nextPage, keyword) {
    const footer = document.querySelector("footer");
    observer = new IntersectionObserver((entries) => {
        const entry = entries[0];
        if (entry.isIntersecting && !loadedPages.has(nextPage)) {
            loadedPages.add(nextPage);
            fetch(`/api/attractions?page=${nextPage}&keyword=${keyword}`)
                .then(response => {return response.json()})
                .then(result => {
                    nextPage = result.nextPage;
                    const filteredAttractionList = [];
                    const attractionsList = result.data;
                    attractionsList.forEach(attraction => {
                        const imgURL = attraction.images[0];
                        filteredAttractionList.push({id :attraction.id, name: attraction.name, mrt: attraction.mrt, cat: attraction.category, img: imgURL});
                    });
                    renderAttractions(filteredAttractionList);
                    if (nextPage === null) {
                        observer.disconnect();
                    }
                })
                .catch(error => {
                    console.error("Error fetching data:", error);
            });
        }
    }, {rootMargin: "100px"}); //rootMargin 正值為外擴，負值為內縮
    observer.observe(footer);
}


function clearAttractions() {
    const attractionView = document.getElementById("attraction-view");
    attractionView.innerHTML = "";
}


function searchData() {
    const keyword = document.getElementById("search-input").value;
    clearAttractions();
    if (observer) {
        observer.disconnect();
    }
    loadedPages.clear(); 
    fetchAttractions(0, keyword);
}


document.addEventListener("DOMContentLoaded", function getMRT() {
    fetch("/api/mrts")
    .then(response => {
        return response.json();
    })
    .then(result => {
        let mrts = result.data
        const mrtList = document.querySelector(".mrt-list")
        if (mrtList.children.length > 0) {
            return;
        }
        mrts.forEach(mrt => {
            const mrtName = document.createElement("div");
            mrtName.className = "mrt-name";
            mrtName.textContent = mrt;
            mrtName.addEventListener("click", clickMRT);
            mrtList.appendChild(mrtName)
        })
    })
    .catch(error => console.error("Error fetching MRT data:", error));
})


let scrollPosition = 0; //紀錄當前滾動位置

function getScrollAmount() {
    const windowWidth = window.innerWidth;
    if (windowWidth > 1200) {
        return 800; // 大螢幕
    } else if (windowWidth > 600) {
        return 345; // 中螢幕
    } else {
        return 216; // 小螢幕
    }
}

function scrollList(direction) {
    const list = document.querySelector(".mrt-list");
    const listWidth = list.scrollWidth; // 列表總寬度
    const blockWidth = list.parentElement.offsetWidth; //列表可視區域的寬度
    const scrollAmount = getScrollAmount(); // 根據視窗尺寸動態獲取滾動量

    scrollPosition += direction * scrollAmount;
    
    // 確保滾動不會超出內容範圍
    if (scrollPosition < 0) {
        scrollPosition = 0;
    } else if (scrollPosition > listWidth - blockWidth) {
        scrollPosition = listWidth - blockWidth;
    }

    list.style.transform = `translateX(${-scrollPosition}px)`;
}


function clickMRT(event){
    const mrtName = event.target.textContent;
    const keyword = document.getElementById("search-input");
    keyword.value = mrtName;
    clearAttractions();
    if (observer) {
        observer.disconnect();
    }
    loadedPages.clear();
    fetchAttractions(0, mrtName);
}