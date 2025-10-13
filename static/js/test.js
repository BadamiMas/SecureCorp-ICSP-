const sidemenu = document.querySelector("aside");
const menubtn = document.querySelector("#menu-bar");
const closebtn = document.querySelector("#close-btn");


const themeToggler = document.querySelector(".theme-toggler");

menubtn.addEventListener("click", () => {
    sidemenu.style.display = "block"
})

closebtn.addEventListener("click", () => {
    sidemenu.style.display = "none"
})


themeToggler.addEventListener("click", () => {
    document.body.classList.toggle("dark-theme-variables");
    themeToggler.querySelector("span:nth-child(1)").classList.toggle("active");
    themeToggler.querySelector("span:nth-child(2)").classList.toggle("active");
})




/* To-Do List */

const inputBox = document.getElementById('input-box');
const listContainer = document.getElementById('list');

function addTask() {
    if (inputBox.value === '') {
        alert("You must write something!");
    }
    else {
        let li = document.createElement("li");
        li.innerHTML = inputBox.value;
        listContainer.appendChild(li);
        let span = document.createElement("span");
        span.innerHTML = "\u00d7";
        li.appendChild(span);
    }
    inputBox.value = "";
    saveData();
}

listContainer.addEventListener("click", function(e) {
    if (e.target.tagName === "LI") {
        e.target.classList.toggle("checked");
        saveData();
    }
    else if (e.target.tagName === "SPAN") {
        e.target.parentElement.remove();
        saveData();
    }
}, false);

function saveData() {
    localStorage.setItem("data", listContainer.innerHTML);
}

function showTask() {
    listContainer.innerHTML = localStorage.getItem("data");
}

showTask();