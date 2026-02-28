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

        if (data.ok) {
            window.location.href = data.redirect_url;
        }else {
            alert(data.message);
        }
    })
    .catch(err => {
        console.error(err);
        alert("Error placing order");
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("placeOrderBtn");
    console.log("Button:", btn);

    if (btn) {
        btn.addEventListener("click", placeOrder);
    }
});

document.addEventListener("DOMContentLoaded",function(){
    const qtyButton=document.querySelectorAll(".qty-btn");

    qtyButton.forEach(btn=>{btn.addEventListener("click",function(){
        const productld=this.dataset.id;
        const action=this.dataset.action;

        fetch("/update-cart",{
            method:"POST",
            headers:{"content-Type":"application/json"},
            body:JSON.stringify({
                product_id:productld,
                action:action
            })

        })
        .then(res => res.json())
        .then(data => {
            if(data.ok){
                location.reload();
            }else{
                alert("Error updating cart");
            }
        })
        .catch(err =>{
            console.error(err);
            alert("error updation cart");
        });
       });
    });
});
document.addEventListener("DOMContentLoaded",
function(){
     console.log("cart.js loaded");
});


window.removeFromCart = function(id) {
    fetch("/remove_from_cart", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `id=${id}`
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            location.reload();
        }
    })
    .catch(err => console.error(err));
};