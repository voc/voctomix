document.querySelectorAll("a.button[href]").forEach((anchor)=>{
    anchor.addEventListener("click",(event)=>{
        event.preventDefault();
        fetch(anchor.getAttribute("href"));
    });
});
