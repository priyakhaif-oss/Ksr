// KSR Dairy Foods JavaScript


// Add to cart animation

document.addEventListener(
    "DOMContentLoaded",
    function(){

        const buttons = document.querySelectorAll("button");


        buttons.forEach(
            button => {

                button.addEventListener(
                    "click",
                    function(){

                        button.innerHTML =
                        "Added ✓";


                        setTimeout(
                            ()=>{
                                button.innerHTML =
                                "Add To Cart 🛒";
                            },
                            1200
                        );

                    }
                );

            }
        );

    }
);
