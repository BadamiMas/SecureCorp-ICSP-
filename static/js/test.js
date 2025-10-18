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

/* profile popup */
const openProfile = document.getElementById("openProfile");
const profilePop = document.getElementById("profilePop");
const closeProfile = document.getElementById("closeProfile");

openProfile.addEventListener("click", () => {
    profilePop.classList.add("open");
});

closeProfile.addEventListener("click", () => {
    profilePop.classList.remove("open");
});


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



// Load Google Charts
google.charts.load("current", { packages: ['corechart'] });
google.charts.setOnLoadCallback(drawChart);

function drawChart() {
    fetch('/get_company_progress_acc')
        .then(res => res.json())
        .then(rows => {
            // Create header row
            const dataArray = [['Month', 'Cash In', 'Cash Out', { role: 'style' }]];

            rows.forEach(row => {
                // Optional: pick colors for cash in/out columns
                dataArray.push([
                    row.month,
                    row.cash_in,
                    row.cash_out,
                    null // We'll style via series below
                ]);
            });

            const data = google.visualization.arrayToDataTable([
                ['Month', 'Cash In', 'Cash Out'],
                ...rows.map(r => [r.month, r.cash_in, r.cash_out])
            ]);

            const options = {
                title: 'Cash In & Out (Last 6 Months)',
                titleTextStyle: { color: '#ffffff', fontSize: 16 },
                chartArea: { width: '80%', height: '70%' },
                backgroundColor: 'transparent',
                legend: { position: 'bottom', textStyle: { color: '#ffffff' } },
                hAxis: { textStyle: { color: '#ffffff' }, titleTextStyle: { color: '#ffffff' } },
                vAxis: { textStyle: { color: '#ffffff' }, titleTextStyle: { color: '#ffffff' } },
                series: {
                    0: { color: '#28b60c' }, // Cash In
                    1: { color: '#bb1310' }  // Cash Out
                },
                bar: { groupWidth: '60%' }
            };

            const chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));
            chart.draw(data, options);
        })
        .catch(err => console.error('Error fetching cash flow:', err));
}

// Redraw chart on window resize
window.addEventListener('resize', drawChart);
setInterval(drawChart, 60000);




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
