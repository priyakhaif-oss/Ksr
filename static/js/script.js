document.addEventListener("DOMContentLoaded", function(){


    updateCartCount();



    const forms = document.querySelectorAll(".cart-form");



    forms.forEach(function(form){



        form.addEventListener("submit", function(e){


            e.preventDefault();



            const button = form.querySelector("button");



            if(button){


                button.style.transform="scale(.95)";


                setTimeout(()=>{


                    button.style.transform="scale(1)";


                },150);


            }





            const data = new FormData(form);





            fetch("/add-cart",{


                method:"POST",


                body:data


            })



            .then(response=>response.json())



            .then(result=>{



                showMessage(
                    "Added to cart successfully"
                );



                updateCartCount();



            })



            .catch(()=>{


                showMessage(
                    "Something went wrong"
                );


            });



        });



    });



});








/* =========================
   CART COUNT
========================= */


function updateCartCount(){



    const badge = document.querySelector(
        ".cart-count"
    );



    if(!badge){

        return;

    }



    fetch("/cart-count")



    .then(response=>response.json())



    .then(data=>{


        badge.innerText = data.count;



        if(data.count > 0){


            badge.style.display="flex";


        }

        else{


            badge.style.display="none";


        }



    })



    .catch(()=>{


        badge.innerText="0";


    });



}








/* =========================
   TOAST MESSAGE
========================= */


function showMessage(message){



    const oldToast = document.querySelector(
        ".toast-message"
    );



    if(oldToast){


        oldToast.remove();


    }





    const toast = document.createElement(
        "div"
    );



    toast.className="toast-message";



    toast.innerText = message;



    document.body.appendChild(toast);






    setTimeout(()=>{



        toast.classList.add(
            "hide"
        );



        setTimeout(()=>{


            toast.remove();


        },400);



    },2200);



}








/* =========================
   PHONE VALIDATION
========================= */


function validatePhone(){



    const phone = document.getElementById(
        "phone"
    ).value;



    if(
        phone.length !== 10 ||
        isNaN(phone)
    ){


        showMessage(
            "Enter valid 10 digit mobile number"
        );


        return false;


    }



    return true;


}
