function addTocart(button){
    const id = button.dataset.id;
    const name=button.dataset.name;
    const price=button.dataset.price;
    const image=button.dataset.image;

    if(!id || !name || !price || !image){
        console.error('missing product data');
        return;
    }

    fetch('/add_to_cart',{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            id:id,
            name:name,
            price:parseFloat(price),
            image:image
        })  
    })
    .then(responce=>responce.json())
    .then(data=>{
        alert(data.message);
    })
    .catch(error=>{
        console.error("Error",error);
    })
}