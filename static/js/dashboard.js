document.addEventListener("DOMContentLoaded", () => {
    showSection("scanner");
    startMonitoring();
    loadCharts();
    initAttackMap();
});

/* ---------------- SECTION TOGGLE ---------------- */
function showSection(id) {
    document.querySelectorAll(".section").forEach(s => s.style.display = "none");
    document.getElementById(id).style.display = "block";

    document.querySelectorAll(".nav-tabs span").forEach(t => t.classList.remove("active-tab"));
    document.querySelector(`[onclick="showSection('${id}')"]`).classList.add("active-tab");

    if (id === "traffic") {
        setTimeout(() => attackMap.invalidateSize(), 300);
    }
}

/* ---------------- PROFILE ---------------- */
function toggleProfile() {
    document.getElementById("profileBox").classList.toggle("active");
}

/* ---------------- CHARTS ---------------- */
function loadCharts() {
    new Chart(document.getElementById("trafficChart"), {
        type: "doughnut",
        data: {
            labels: ["Safe", "Attacks"],
            datasets: [{
                data: [window.SAFE_COUNT || 1, window.ATTACK_COUNT || 1],
                backgroundColor: ["#22c55e", "#3b82f6"]
            }]
        },
        options: { plugins: { legend: { position: "bottom" } } }
    });

    fetch("/api/top_countries")
        .then(r => r.json())
        .then(d => {
            new Chart(document.getElementById("countryChart"), {
                type: "bar",
                data: {
                    labels: d.labels,
                    datasets: [{
                        data: d.counts,
                        backgroundColor: "#6366f1"
                    }]
                },
                options: {
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: "#c7d2fe" }},
                        y: { ticks: { color: "#c7d2fe" }}
                    }
                }
            });
        });
}

/* ---------------- LIVE ATTACK MAP ---------------- */
let attackMap;
let attackLayer;

const countryCoords = {
    "India": [20.59, 78.96],
    "United States": [37.09, -95.71],
    "China": [35.86, 104.19],
    "Russia": [61.52, 105.31],
    "Germany": [51.16, 10.45],
    "United Kingdom": [55.37, -3.43]
};

function initAttackMap() {
    attackMap = L.map("attackMap", { zoomControl: false }).setView([20, 0], 2);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap"
    }).addTo(attackMap);

    attackLayer = L.layerGroup().addTo(attackMap);
    updateAttackMap();
    setInterval(updateAttackMap, 5000);
}

function updateAttackMap() {
    fetch("/monitor_data")
        .then(r => r.json())
        .then(d => {
            attackLayer.clearLayers();

            const attackCount = {};

            d.logs.forEach(log => {
                if (log.label !== 0 && countryCoords[log.country]) {
                    attackCount[log.country] = (attackCount[log.country] || 0) + 1;
                }
            });

            Object.keys(attackCount).forEach(country => {
                const count = attackCount[country];
                const [lat, lng] = countryCoords[country];

                L.circleMarker([lat, lng], {
                    radius: 6 + count * 2,
                    color: "#ef4444",
                    fillColor: "#ef4444",
                    fillOpacity: 0.75
                })
                .bindPopup(`<b>${country}</b><br>${count} attacks`)
                .addTo(attackLayer);
            });
        });
}
function copyAlert() {
    const text = document.getElementById("alertText").innerText;
    navigator.clipboard.writeText(text);
    alert("🚨 Alert copied to clipboard");
}

function shareAlert() {
    const text = document.getElementById("alertText").innerText;
    if (navigator.share) {
        navigator.share({
            title: "SafeNet Security Alert",
            text: text
        });
    } else {
        alert("Sharing not supported on this browser");
    }
}
