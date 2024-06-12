document.addEventListener("DOMContentLoaded", () => {
    const homebtn = document.querySelector(".left");
    homebtn.addEventListener("click", () => {
        window.location.href = "/";
    });
});


document.addEventListener("DOMContentLoaded", () => {
    const pathParts = window.location.pathname.split("/");
    const attractionId = pathParts[pathParts.length - 1];
    if (attractionId) {
        fetchAttraction(attractionId);
    } else {
        console.error("No attraction ID provided in the URL");
    }
});


function fetchAttraction(attractionId){
    fetch((`/api/attraction/${attractionId}`))
    .then(response => response.json())
    .then(result => {
        if (result.data){
            title = result.data.name;
            cat = result.data.category;
            mrt = result.data.mrt;
            info = result.data.description;
            address = result.data.address;
            transport = result.data.transport;
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
        }
        else{
            window.location.href = "/";
        }
    })
    .catch(error => {
        console.error("Error fetching data:", error);
    });
}