document.addEventListener("DOMContentLoaded", function(){


const forms = document.querySelectorAll(".cart-form");



forms.forEach(function(form){


form.addEventListener("submit", function(e){


e.preventDefault();



const button = form.querySelector("button");



button.style.transform = "scale(0.95)";



setTimeout(()=>{

button.style.transform = "scale(1)";

},150);





let data = new FormData(form);





fetch("/add-cart", {

    method:"POST",

    body:data

})



.then(response => response.json())



.then(result => {


showMessage("Added to cart successfully");


})



.catch(()=>{


showMessage("Something went wrong");


});



});



});



});






function showMessage(message){



const oldToast = document.querySelector(".toast-message");


if(oldToast){

    oldToast.remove();

}




const toast = document.createElement("div");



toast.className = "toast-message";

toast.innerText = message;



document.body.appendChild(toast);





setTimeout(()=>{


toast.classList.add("hide");



setTimeout(()=>{


toast.remove();


},400);



},2200);



}
