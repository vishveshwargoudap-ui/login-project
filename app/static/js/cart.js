function addToCart(button) {
    console.log("add to cart clicked");

    const id = button.dataset.id;
    const name = button.dataset.name;
    const price = parseFloat(button.dataset.price);
    const image = button.dataset.image;

    fetch("/add_to_cart", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            id: id,
            name: name,
            price: price,
            image: image
        })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
    })
    .catch(error => {
        console.error(error);
        alert("Error adding to cart");
    });
}

console.log("cart.js loaded");

function placeOrder() {
    console.log("Place order clicked");

    fetch("/place-order", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ payment_mode: "cash" })
    })
    .then(res => res.json())
    .then(data => {
        console.log(data);
    })
    .catch(err => {
        console.error(err);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("placeOrderBtn");
    console.log("Button:", btn);

    if (btn) {
        btn.addEventListener("click", placeOrder);
    }
});