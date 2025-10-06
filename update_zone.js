const dropdown = document.getElementById("zoneDropdown");
const deleteBtn = document.getElementById("deleteZone");

fetch("/api/get_zones")
  .then(res => res.json())
  .then(zones => {
    zones.forEach(z => {
      const opt = document.createElement("option");
      opt.value = z.label;
      opt.textContent = z.label;
      dropdown.appendChild(opt);
    });
  });

deleteBtn.addEventListener("click", () => {
  const label = dropdown.value;
  if (!label) return;

  fetch(`/api/delete_zone/${label}`, {method: "DELETE"})
    .then(res => res.json())
    .then(data => {
      alert(`Zone ${label} deleted!`);
      location.reload();
    });
});
