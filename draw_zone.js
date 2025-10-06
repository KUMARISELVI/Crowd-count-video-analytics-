const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const video = document.getElementById("video");
const zoneLabel = document.getElementById("zoneLabel");
const saveBtn = document.getElementById("saveZone");

canvas.width = video.width;
canvas.height = video.height;

let drawing = false, startX, startY, endX, endY;

canvas.addEventListener("mousedown", e => {
  drawing = true;
  startX = e.offsetX;
  startY = e.offsetY;
});

canvas.addEventListener("mouseup", e => {
  drawing = false;
  endX = e.offsetX;
  endY = e.offsetY;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "blue";
  ctx.lineWidth = 2;
  ctx.strokeRect(startX, startY, endX - startX, endY - startY);
});

saveBtn.addEventListener("click", () => {
  const label = zoneLabel.value;
  if (!label) return alert("Enter zone label");

  const zone = {
    topleft: {x: startX, y: startY},
    bottomright: {x: endX, y: endY},
    label: label
  };

  fetch("/api/save_zone", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(zone)
  }).then(res => res.json())
    .then(data => {
      alert("Zone saved!");
      console.log(data);
    });
});
