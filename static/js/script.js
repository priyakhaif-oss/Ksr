// KSR Dairy Foods JavaScript


document.addEventListener("DOMContentLoaded", function(){


    const buttons = document.querySelectorAll("button");


    buttons.forEach(function(button){


        button.addEventListener("click", function(){


            showMessage("🥛 Product added to cart successfully! 🛒");


        });


    });



});



// Pretty Toast Message

function showMessage(message){


    const toast = document.createElement("div");


    toast.innerHTML = message;


    toast.style.position = "fixed";
    toast.style.top = "80px";
    toast.style.right = "20px";
    toast.style.background = "#16a34a";
    toast.style.color = "white";
    toast.style.padding = "15px 25px";
    toast.style.borderRadius = "30px";
    toast.style.fontSize = "16px";
    toast.style.fontWeight = "bold";
    toast.style.boxShadow = "0 10px 25px rgba(0,0,0,0.2)";
    toast.style.zIndex = "9999";
    toast.style.animation = "slideIn .3s ease";


    document.body.appendChild(toast);



    setTimeout(function(){


        toast.remove();


    },2500);



}
