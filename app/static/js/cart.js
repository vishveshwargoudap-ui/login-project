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

