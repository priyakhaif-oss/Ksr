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


showMessage("Added to cart successfully");


});



});



});



});







function showMessage(message){


const toast = document.createElement("div");


toast.innerHTML = message;



toast.style.position = "fixed";

toast.style.top = "90px";

toast.style.right = "20px";

toast.style.background = "#166534";

toast.style.color = "white";

toast.style.padding = "14px 24px";

toast.style.borderRadius = "10px";

toast.style.fontWeight = "600";

toast.style.zIndex = "9999";

toast.style.boxShadow = "0 8px 25px rgba(0,0,0,0.15)";

toast.style.animation = "fadeUp .4s ease";



document.body.appendChild(toast);





setTimeout(()=>{


toast.style.opacity = "0";

toast.style.transform = "translateY(-20px)";

toast.style.transition = ".3s";



setTimeout(()=>{

toast.remove();

},300);



},2500);



}
