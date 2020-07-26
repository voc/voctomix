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

function changeColor (id) {
  Array.from(document.querySelectorAll('.button > input[type="submit"]')).map(function(button) {
    if (button == id) {
      button.style.backgroundColor = "green";
    } else {
      button.style.backgroundColor = "blue";
    }
  })
}
