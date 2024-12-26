async function fetchDockerStats() {
	try {
		const response = await fetch("/get-docker-stats/");
		if (!response.ok) {
			throw new Error("Network response was not ok");
		}
		const data = await response.json();
		updateTable(data);
	} catch (error) {
		console.error("Error fetching Docker stats:", error);
	}
}

function updateTable(containers) {
	const tableBody = document.getElementById("docker-table-body");
	tableBody.innerHTML = ""; // Clear existing rows

	containers.forEach((container) => {
		const row = document.createElement("tr");

		// Name
		const nameCell = document.createElement("td");
		nameCell.textContent = container.name;
		nameCell.classList.add("cont-name");
		row.appendChild(nameCell);

		// Status
		const statusCell = document.createElement("td");
		statusCell.classList.add("status", "text-left");
		const statusDiv = document.createElement("div");
		statusDiv.classList.add("info-button");
		if (container.status === "running") {
			statusDiv.classList.add("running");
		} else if (container.status === "stopped") {
			statusDiv.classList.add("stopped");
		} else if (container.status === "paused") {
			statusDiv.classList.add("paused");
		} else {
			statusDiv.classList.add("unknown");
		}
		statusDiv.textContent =
			container.status.charAt(0).toUpperCase() +
			container.status.slice(1);
		statusCell.appendChild(statusDiv);
		row.appendChild(statusCell);

		// Ports
		const portsCell = document.createElement("td");
		portsCell.textContent = container.ports;
		row.appendChild(portsCell);

		// Uptime
		const uptimeCell = document.createElement("td");
		uptimeCell.textContent = container.uptime;
		row.appendChild(uptimeCell);

		// CPU Usage
		const cpuCell = document.createElement("td");
		cpuCell.textContent = container.cpu_usage;
		row.appendChild(cpuCell);

		// Memory Usage
		const memoryCell = document.createElement("td");
		memoryCell.textContent = container.memory_usage;
		row.appendChild(memoryCell);

		// Image
		const imageCell = document.createElement("td");
		imageCell.textContent = container.image;
		row.appendChild(imageCell);

		// Actions
		const actionsCell = document.createElement("td");
		actionsCell.classList.add("text-right");
		// Add action buttons as needed
		actionsCell.innerHTML = `
          <a href="/docker-action/start/${container.id}/">Start</a> |
          <a href="/docker-action/stop/${container.id}/">Stop</a>
        `;
		row.appendChild(actionsCell);

		tableBody.appendChild(row);
	});
}

// Initial fetch
fetchDockerStats();

// Auto-refresh every 5 seconds
setInterval(fetchDockerStats, 5000);
