document.addEventListener("DOMContentLoaded", () => {
    const statusCanvas = document.getElementById("statusChart");
    const vehicleCanvas = document.getElementById("vehicleChart");

    if (statusCanvas) {
        const charging = Number(statusCanvas.dataset.charging || 0);
        const full = Number(statusCanvas.dataset.full || 0);
        const stopped = Number(statusCanvas.dataset.stopped || 0);

        new Chart(statusCanvas, {
            type: "doughnut",
            data: {
                labels: ["Charging", "Full", "Stopped"],
                datasets: [{
                    data: [charging, full, stopped],
                    backgroundColor: ["#f5c451", "#17c964", "#ff5d73"],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: { color: "#e6edf8" }
                    }
                }
            }
        });
    }

    if (vehicleCanvas) {
        const labels = JSON.parse(vehicleCanvas.dataset.labels || "[]");
        const values = JSON.parse(vehicleCanvas.dataset.values || "[]");

        new Chart(vehicleCanvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Units Charged (kWh)",
                    data: values,
                    backgroundColor: "#00d4ff",
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        ticks: { color: "#e6edf8" },
                        grid: { color: "rgba(255,255,255,0.08)" }
                    },
                    y: {
                        ticks: { color: "#e6edf8" },
                        grid: { color: "rgba(255,255,255,0.08)" }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: "#e6edf8" }
                    }
                }
            }
        });
    }
});