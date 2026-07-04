document.addEventListener("DOMContentLoaded", () => {
    const dashboard = document.getElementById("session-dashboard");
    if (!dashboard) return;

    const sessionId = dashboard.dataset.sessionId;
    const apiUrl = dashboard.dataset.apiUrl;

    const currentBatteryPercentEl = document.getElementById("current_battery_percent");
    const currentBatteryPercentTableEl = document.getElementById("current_battery_percent_table");
    const batteryRemainingPercentEl = document.getElementById("battery_remaining_percent");
    const unitsConsumedEl = document.getElementById("units_consumed");
    const unitsLeftEl = document.getElementById("units_left");
    const amountEl = document.getElementById("amount");
    const timeLeftTextEl = document.getElementById("time_left_text");
    const statusBadgeEl = document.getElementById("status_badge");
    const statusTextEl = document.getElementById("status_text");
    const durationTextEl = document.getElementById("duration_text");
    const endTimeEl = document.getElementById("end_time");
    const lastUpdatedEl = document.getElementById("last_updated");
    const progressBar = document.getElementById("batteryProgressBar");

    let pollInterval = null;

    function setStatusBadge(status) {
        if (!statusBadgeEl) return;

        statusBadgeEl.className = "badge fs-6 px-3 py-2";

        if (status === "Charging") {
            statusBadgeEl.classList.add("bg-warning", "text-dark");
        } else if (status === "Full") {
            statusBadgeEl.classList.add("bg-success");
        } else {
            statusBadgeEl.classList.add("bg-danger");
        }

        statusBadgeEl.textContent = status;
    }

    function updateDashboard(session) {
        if (!session) return;

        const current = Number(session.current_battery_percent || 0);
        const target = Number(session.target_battery_percent || 0);
        const remainingBattery = Math.max(target - current, 0);

        if (currentBatteryPercentEl) currentBatteryPercentEl.textContent = current.toFixed(2);
        if (currentBatteryPercentTableEl) currentBatteryPercentTableEl.textContent = current.toFixed(2);
        if (batteryRemainingPercentEl) batteryRemainingPercentEl.textContent = remainingBattery.toFixed(2) + "%";
        if (unitsConsumedEl) unitsConsumedEl.textContent = Number(session.units_consumed).toFixed(4);
        if (unitsLeftEl) unitsLeftEl.textContent = Number(session.units_left).toFixed(4);
        if (amountEl) amountEl.textContent = Number(session.amount).toFixed(2);
        if (timeLeftTextEl) timeLeftTextEl.textContent = session.time_left_text;
        if (statusTextEl) statusTextEl.textContent = session.status;
        if (durationTextEl) durationTextEl.textContent = session.duration_text;
        if (lastUpdatedEl) lastUpdatedEl.textContent = session.last_updated;
        if (endTimeEl) endTimeEl.textContent = session.end_time ? session.end_time : "Charging in progress...";

        setStatusBadge(session.status);

        if (progressBar) {
            progressBar.style.width = `${current}%`;
            progressBar.textContent = `${current.toFixed(2)}%`;
            progressBar.setAttribute("aria-valuenow", current.toFixed(2));

            if (session.status !== "Charging") {
                progressBar.classList.remove("progress-bar-animated");
            }
        }

        if (session.status !== "Charging" && pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }

    async function fetchSession() {
        try {
            const res = await fetch(apiUrl);
            const data = await res.json();

            if (data.success) {
                updateDashboard(data.session);
            }
        } catch (err) {
            console.error("Error fetching session update:", err);
        }
    }

    fetchSession();
    pollInterval = setInterval(fetchSession, 3000);
});