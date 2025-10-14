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


/* Fetch Total Employees */

function loadTotalEmployees() {
    fetch('/get_total_employees')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-employees').innerText = data.total_employees;
        })
        .catch(error => console.error('Error loading total employees:', error));
}

loadTotalEmployees();
setInterval(loadTotalEmployees, 600000); // Refresh every 10min (60 seconds = 60000 milliseconds)


/* Fetch Attendance Log */

// ===== Attendance Log =====
function formatTime(date) {
    return date.toLocaleString(); // e.g., 10/13/2025, 9:42:18 AM
}

function setLoginTime() {
    const today = new Date().toDateString();
    const data = JSON.parse(localStorage.getItem("attendance")) || {};

    // If today's date is new, record login
    if (data.date !== today) {
        data.date = today;
        data.login = formatTime(new Date());
        data.logout = null;
        localStorage.setItem("attendance", JSON.stringify(data));
    }

    displayAttendance();
}

function setLogoutTime() {
    const data = JSON.parse(localStorage.getItem("attendance"));
    if (data) {
        data.logout = formatTime(new Date());
        localStorage.setItem("attendance", JSON.stringify(data));
    }
    displayAttendance();
}

function displayAttendance() {
    const data = JSON.parse(localStorage.getItem("attendance"));
    const today = new Date().toDateString();

    if (!data || data.date !== today) {
        localStorage.removeItem("attendance");
        document.getElementById("login-time").innerText = "-";
        document.getElementById("logout-time").innerText = "-";
        document.getElementById("active-hours").innerText = "0";
        return;
    }

    document.getElementById("login-time").innerText = data.login || "-";
    document.getElementById("logout-time").innerText = data.logout || "-";
    calculateActiveTime();
}

// Record login when dashboard loads
window.addEventListener("load", setLoginTime);

// Record logout when tab closes or user logs out
window.addEventListener("beforeunload", setLogoutTime);



/* Fetch Active Hours */

function calculateActiveTime() {
    const data = JSON.parse(localStorage.getItem("attendance"));
    if (!data || !data.login) {
        document.getElementById("active-hours").innerText = "0";
        return;
    }

    const loginTime = new Date(data.login);
    const logoutTime = data.logout ? new Date(data.logout) : new Date(); // if not logged out, use current time

    const diffMs = logoutTime - loginTime; // difference in milliseconds
    const diffHrs = diffMs / (1000 * 60 * 60); // convert to hours

    // Show up to 2 decimal places
    document.getElementById("active-hours").innerText = diffHrs.toFixed(2);
}

setInterval(calculateActiveTime, 60000); // Update active hours every min



// Define the chart function
function drawVisualization() {
  const data = google.visualization.arrayToDataTable([
    ['Month', 'Cash Flow (SGD)', 'Recruitment (People)', 'Average'],
    ['Jan',  12000, 3, 615],
    ['Feb',  15000, 5, 682],
    ['Mar',  8000, 2, 623],
    ['Apr',  18000, 6, 609],
    ['May',  14000, 4, 570]
  ]);

  const options = {
    vAxes: {
      0: { title: 'Cash Flow (SGD)', textStyle: { color: '#333' } },
      1: { title: 'Recruitment (People)', textStyle: { color: '#333' } }
    },
    hAxis: { title: 'Month' },
    seriesType: 'bars',
    series: {
      0: { targetAxisIndex: 0, color: '#2962ff' }, // cash flow (bar)
      1: { type: 'line', targetAxisIndex: 1, color: '#00c853' } // recruitment (line)
    },
    backgroundColor: 'transparent',
    chartArea: { width: '80%', height: '70%' },
    legend: { position: 'bottom' }
  };

  const chart = new google.visualization.ComboChart(
    document.getElementById('chart_div')
  );
  chart.draw(data, options);
}

// Load Google Charts
google.charts.load('current', { packages: ['corechart'] });
google.charts.setOnLoadCallback(drawVisualization);

// Window resize
window.addEventListener('resize', drawVisualization);
setInterval(drawVisualization, 60000);
