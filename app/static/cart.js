function addToCart(id, name, price, image) {
    const cartItems = JSON.parse(localStorage.getItem("cartItems") || "[]");
    const existing = cartItems.find(item => item.id === id);

    if (existing) {
        existing.qty += 1;
    } else {
        cartItems.push({ id, name, price, image, qty: 1 });
    }

    localStorage.setItem("cartItems", JSON.stringify(cartItems));
    alert(name + " added to cart");
}