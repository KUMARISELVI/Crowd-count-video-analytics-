const canvas = document.getElementById("videoCanvas");
const ctx = canvas.getContext("2d");
const drawBtn = document.getElementById("drawZoneBtn");
const zonesList = document.getElementById("zonesList");

let video = new Image();
video.src = "/video_feed";  // MJPEG stream
let zones = [];
let drawing = false;
let currentPoints = [];

// ----------------- Load Zones -----------------
async function loadZones() {
    const res = await fetch("/zones");
    zones = await res.json();
    renderZonesList();
}
loadZones();

// ----------------- Render Zones List -----------------
function renderZonesList() {
    zonesList.innerHTML = "";
    zones.forEach((z, idx) => {
        const li = document.createElement("li");
        li.innerHTML = `${z.label} <button onclick="deleteZone(${idx})">Delete</button>`;
        zonesList.appendChild(li);
    });
}

// ----------------- Delete Zone -----------------
async function deleteZone(idx) {
    await fetch(`/zones?idx=${idx}`, { method: "DELETE" });
    loadZones();
}

// ----------------- Draw Zone -----------------
drawBtn.addEventListener("click", () => {
    drawing = true;
    currentPoints = [];
    alert("Click 4 points on video to draw a zone.");
});

// ----------------- Handle Mouse Clicks -----------------
canvas.addEventListener("click", (e) => {
    if (!drawing) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    currentPoints.push([x, y]);

    if (currentPoints.length === 4) {
        const label = prompt("Enter zone label:");
        fetch("/zones", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                topleft: currentPoints[0],
                topright: currentPoints[1],
                bottomright: currentPoints[2],
                bottomleft: currentPoints[3],
                label: label
            })
        }).then(() => {
            loadZones();
            currentPoints = [];
            drawing = false;
        });
    }
});

// ----------------- Draw Loop -----------------
function drawLoop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    zones.forEach(z => {
        ctx.beginPath();
        ctx.moveTo(z.topleft[0], z.topleft[1]);
        ctx.lineTo(z.topright[0], z.topright[1]);
        ctx.lineTo(z.bottomright[0], z.bottomright[1]);
        ctx.lineTo(z.bottomleft[0], z.bottomleft[1]);
        ctx.closePath();
        ctx.strokeStyle = "green";
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.fillStyle = "green";
        ctx.fillText(z.label, z.topleft[0], z.topleft[1]-5);
    });

    requestAnimationFrame(drawLoop);
}

video.onload = drawLoop;

