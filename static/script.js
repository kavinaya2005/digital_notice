/* ================================
   Digital Notice Board - script.js
   ================================ */

/* Auto refresh interval (milliseconds) */
const REFRESH_TIME = 3000;

/* Load notices when page opens */
document.addEventListener("DOMContentLoaded", () => {
    loadNotices();

    /* Auto refresh every 3 seconds */
    setInterval(loadNotices, REFRESH_TIME);
});

/* Fetch notices from backend */
function loadNotices() {
    fetch("/api/notices")
        .then(response => response.json())
        .then(data => {
            displayNotices(data);
        })
        .catch(error => {
            console.error("Error loading notices:", error);
        });
}

/* Display notices on UI */
function displayNotices(notices) {
    const container = document.getElementById("notices");
    if (!container) return;

    container.innerHTML = "";

    if (notices.length === 0) {
        container.innerHTML = "<p>No notices available</p>";
        return;
    }

    notices.forEach(n => {
        const card = document.createElement("div");
        card.classList.add("notice-card");

        /* Priority color */
        if (n[4]) {
            card.classList.add(n[4].toLowerCase());
        }

        /* File attachment */
        let attachment = "";
        if (n[6]) {
            attachment = `<br><a href="/uploads/${n[6]}" target="_blank">📎 View Attachment</a>`;
        }

        card.innerHTML = `
            <h3>${n[1]}</h3>
            <p>${n[2]}</p>
            <p><strong>Category:</strong> ${n[3]}</p>
            <p><strong>Priority:</strong> ${n[4]}</p>
            <p><strong>Target:</strong> ${n[5]}</p>
            ${attachment}
            <small>Posted by ${n[7]} | ${n[8]}</small>
        `;

        container.appendChild(card);
    });
}

/* ================================
   Search Notices (Optional Feature)
   ================================ */
function searchNotices() {
    const input = document.getElementById("searchBox").value.toLowerCase();
    const cards = document.querySelectorAll(".notice-card");

    cards.forEach(card => {
        const text = card.innerText.toLowerCase();
        card.style.display = text.includes(input) ? "block" : "none";
    });
}
