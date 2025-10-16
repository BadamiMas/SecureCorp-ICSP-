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


// POPUP //

const openBtn = document.getElementById("openPop");
const closeBtn = document.getElementById("closePop");
const pop = document.getElementById("pop");

openBtn.addEventListener("click", () => {
    pop.classList.add("open");
})

closeBtn.addEventListener("click", () => {
    pop.classList.remove("open");
})


// FILE UPLOAD //

window.addEventListener("load", () => {
    const input = document.getElementById("upload");
    const filewrapper = document.getElementById("filewrapper");

    input.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const fileName = file.name;
        const filetype = fileName.split('.').pop().toUpperCase();
        fileshow(fileName, filetype);
    })

    function fileshow (filename, filetype) {
        const showfileboxElem = document.createElement("div");
        showfileboxElem.classList.add("showfilebox");

        const leftElem = document.createElement("div");
        leftElem.classList.add("left");

        const fileTypeElem = document.createElement("span");
        fileTypeElem.classList.add("filetype");
        fileTypeElem.innerHTML = filetype;

        const filetitleElem = document.createElement("h3");
        filetitleElem.innerHTML = filename;

        leftElem.append(fileTypeElem, filetitleElem);

        const rightElem = document.createElement("div");
        rightElem.classList.add("right");

        const crossElem = document.createElement("span");
        crossElem.innerHTML = "&#215;";
        crossElem.addEventListener("click", () => {
            showfileboxElem.remove();
        })

        rightElem.append(crossElem);
        showfileboxElem.append(leftElem, rightElem);
        filewrapper.append(showfileboxElem);
    }
})


// RESET //

const clearBtn = document.getElementById("clearBtn");
clearBtn.addEventListener("click", () => {
    // clear key input
    document.getElementById("input-box").value = "";

    // reset file input
    const uploadInput = document.getElementById("upload");
    uploadInput.value = "";

    // remove file previews
    const fileWrapper = document.getElementById("filewrapper");
    const showFiles = fileWrapper.querySelectorAll(".showfilebox");
    showFiles.forEach(el => el.remove());

    // optionally reset label text
    document.getElementById("fileLabelText").innerText = "Click to Upload";
});



// LOGOUT //

let logoutTimer;
function resetTimer() {
  clearTimeout(logoutTimer);
  logoutTimer = setTimeout(() => {
    window.location.href = "/logout";
  }, 600000); // 1 min inactivity
}

window.addEventListener("load", resetTimer);
window.addEventListener("mousemove", resetTimer);
window.addEventListener("keypress", resetTimer);
