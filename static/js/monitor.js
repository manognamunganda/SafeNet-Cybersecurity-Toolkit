let monitorStarted = false;

function startMonitoring() {
    if (monitorStarted) return;
    monitorStarted = true;
    setInterval(loadStats, 3000);
    setInterval(loadLogs, 3000);
}

function loadStats() {
    fetch("/monitor_stats")
        .then(r => r.json())
        .then(d => {
            const t = document.getElementById("total");
            const b = document.getElementById("benign");
            const m = document.getElementById("malicious");
            if (t) t.innerText = d.total;
            if (b) b.innerText = d.benign;
            if (m) m.innerText = d.malicious;
        });
}

function loadLogs() {
    fetch("/monitor_data")
        .then(r => r.json())
        .then(d => {
            const box = document.getElementById("liveLog");
            if (!box) return;

            box.innerHTML = "";
            d.logs.forEach(l => {
                const div = document.createElement("div");
                div.className = "log-entry " + (l.label ? "malicious" : "");
                div.innerHTML = `
                    <b>${l.label ? "🚨 ATTACK" : "✅ SAFE"}</b>
                    <div class="log-meta">
                        ${l.time} | ${l.country} | ${l.org}
                    </div>
                    <div>${l.query}</div>
                `;
                box.appendChild(div);
            });
        });
}
