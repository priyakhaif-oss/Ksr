// KSR Dairy Foods JavaScript


document.addEventListener("DOMContentLoaded", function(){


    // Add to cart button animation

    const buttons = document.querySelectorAll("button");


    buttons.forEach(function(button){


        button.addEventListener("click", function(){


            const oldText = button.innerHTML;


            button.innerHTML = "Added ✓";


            button.style.transform = "scale(0.95)";



            setTimeout(function(){


                button.innerHTML = oldText;


                button.style.transform = "scale(1)";


            },1200);



        });


    });



    // Smooth scroll for Order Now button

    const orderBtn = document.querySelector(".order-btn");


    if(orderBtn){


        orderBtn.addEventListener("click", function(e){


            const target = document.querySelector("#products");


            if(target){


                e.preventDefault();


                target.scrollIntoView({

                    behavior:"smooth"

                });


            }


        });


    }



});
