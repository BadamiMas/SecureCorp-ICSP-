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
    updatePendingCount();
}

function updatePendingCount() {
    const pendingTasks = listContainer.querySelectorAll("li:not(.checked)").length;
    document.getElementById("pending-count").innerText = pendingTasks;
}

function showTask() {
    listContainer.innerHTML = localStorage.getItem("data");
}

showTask();
updatePendingCount();


// FILE UPLOAD //

window.addEventListener("load", () => {
    const input = document.getElementById("upload");
    const labelText = document.getElementById("fileLabelText");

    input.addEventListener("change", (e) => {
        if(e.target.files.length > 0) {
            let fileName = e.target.files[0].name;
            labelText.textContent = fileName;
        } else {
            labelText.textContent = "Click to Upload";
        }
    })
})





// LOGOUT //

let logoutTimer;
function resetTimer() {
  clearTimeout(logoutTimer);
  logoutTimer = setTimeout(() => {
    window.location.href = "/logout";
  }, 600000); // 1 min inactivity
}

window.onload = resetTimer;
window.onmousemove = resetTimer;
window.onkeypress = resetTimer;
