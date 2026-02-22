function addToCart(button){

    const id = button.dataset.id;
    const name = button.dataset.name;
    const price = button.dataset.price;
    const image = button.dataset.image;

    fetch('/add_to_cart', {
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
    .then(response => {
        if (!response.ok) {
            throw new Error("Server error");
        }
        return response.json();
    })
    .then(data => {
        console.log("Server response:", data);
        alert(data.message || "Added to cart");
    })
    .catch(error => {
        console.error("Error:", error);
        alert("Something went wrong");
    });

}