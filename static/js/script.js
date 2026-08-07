document.addEventListener("DOMContentLoaded", function(){


    const forms = document.querySelectorAll(".cart-form");


    updateCartCount();



    forms.forEach(function(form){


        form.addEventListener("submit", function(e){


            e.preventDefault();



            const button = form.querySelector("button");



            button.classList.add("clicked");



            setTimeout(()=>{

                button.classList.remove("clicked");

            },200);





            const data = new FormData(form);





            fetch("/add-cart",{

                method:"POST",

                body:data

            })



            .then(response => response.json())



            .then(result => {



                increaseCartCount();



                showMessage("Added to cart successfully");



            })



            .catch(()=>{


                showMessage("Something went wrong");


            });



        });



    });



});






/* =========================
   CART COUNT
========================= */


function increaseCartCount(){


    let count = localStorage.getItem("cartCount");


    count = count ? parseInt(count)+1 : 1;



    localStorage.setItem(
        "cartCount",
        count
    );



    updateCartCount();


}




function updateCartCount(){



    const badge = document.querySelector(".cart-count");



    if(!badge){

        return;

    }




    let count = localStorage.getItem("cartCount");



    if(!count){

        count = 0;

    }




    badge.innerText = count;



}






/* =========================
   TOAST POPUP
========================= */


function showMessage(message){



    const oldToast = document.querySelector(".toast-message");



    if(oldToast){

        oldToast.remove();

    }





    const toast = document.createElement("div");



    toast.className="toast-message";



    toast.innerText = message;



    document.body.appendChild(toast);





    setTimeout(()=>{


        toast.classList.add("hide");



        setTimeout(()=>{


            toast.remove();


        },400);



    },2200);



}
