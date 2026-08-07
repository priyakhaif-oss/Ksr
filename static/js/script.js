document.addEventListener("DOMContentLoaded", function(){


const forms = document.querySelectorAll(".cart-form");


forms.forEach(function(form){


form.addEventListener("submit", function(e){


e.preventDefault();


let data = new FormData(form);


fetch("/add-cart", {

method:"POST",

body:data

})


.then(response => response.json())


.then(result => {


showMessage("🥛 Added to cart successfully! 🛒");


});



});


});



});



function showMessage(message){


const toast = document.createElement("div");


toast.innerHTML = message;


toast.style.position="fixed";
toast.style.top="80px";
toast.style.right="20px";
toast.style.background="#16a34a";
toast.style.color="white";
toast.style.padding="15px 25px";
toast.style.borderRadius="30px";
toast.style.fontWeight="bold";
toast.style.zIndex="9999";


document.body.appendChild(toast);



setTimeout(()=>{

toast.remove();

},2500);


}
