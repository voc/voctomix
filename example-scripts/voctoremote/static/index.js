document.querySelectorAll(".button").forEach((form)=>{
    form.addEventListener("submit",(event)=>{
        fetch(form.getAttribute("action"),{
            method: "POST",
            redirect: "manual",
            body: new FormData(form)
        });
        event.preventDefault();
    });
});
