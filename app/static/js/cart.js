function addToCart(button){
    console.log("add to cart clicked");
const id=button.dataset.id;
const name=button.dataset.name;
const price=parseFloat(button.dataset.price);
const image=button.dataset.image;

fetch("/add_to_cart",{
    method:"POST",
    headers:{
        "Content-Type":"application/json"
},
    body:JSON.stringify({
        id:id,
        name:name,
        price:price,
        image:image
    })
}).then(response=>response.json())
.then(data=>{
    console.log(data);
    alert(data.message);
})
.catch(error=>{
    console.error("Error:",error);
    alert("An error occurred while adding to cart.");
});
}
function placeOrder(){
    fetch("/place-order",{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            payment_mode:"cash"
        })
    })
    .then(response=>response.json())
    .then(data=>{
        if(data.ok){
            window.location.href=data.redirect_url;
        } else{
            alert(data.messsage);
        }
    })
    .catch(error=>{
        console.error("Error:",error);
        alert("An error occurred while placing the order.");
    });
}