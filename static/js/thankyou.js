function renderOrderNumber(){
    const url = window.location.href;
    const orderNumber = url.split("=")[1];
    const orderNumberDiv = document.getElementById("order-number");
    orderNumberDiv.textContent = orderNumber;
}
renderOrderNumber();