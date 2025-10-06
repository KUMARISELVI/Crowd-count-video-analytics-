const canvas = document.getElementById("previewCanvas");
const ctx = canvas.getContext("2d");
const video = document.getElementById("previewVideo");

canvas.width = video.width;
canvas.height = video.height;

function drawZones(zones) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  zones.forEach(zone => {
    ctx.strokeStyle = "blue";
    ctx.lineWidth = 2;
    const x = zone.topleft.x;
    const y = zone.topleft.y;
    const w = zone.bottomright.x - zone.topleft.x;
    const h = zone.bottomright.y - zone.topleft.y;
    ctx.strokeRect(x, y, w, h);
    ctx.fillStyle = "green";
    ctx.fillText(zone.label, x + 5, y - 5);
  });
}

fetch("/api/get_zones")
  .then(res => res.json())
  .then(data => drawZones(data));
