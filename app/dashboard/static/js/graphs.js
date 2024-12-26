console.log("Hello from graphs.js");


// Data from Django context
var data = {{ data|safe }};
console.log(data);
var maxDataPoints = 10 * 60; // 10 minutes worth of data if updated every second

// Initialize the combined percentage chart
var percentChart = createCombinedPercentChart(
	'percentChart', 
	data.cpu_usage.timestamps, 
	data.cpu_usage.values, 
	data.memory_usage.values
);

// Initialize the other charts
var networkChart = createChartBytes(
	'networkChart', 'Network I/O (MB)', data.network_io.timestamps, data.network_io.values, 'Bytes'
);
var diskChart = createChartBytes(
	'diskChart', 'Disk I/O (MB)', data.disk_io.timestamps, data.disk_io.values, 'Bytes'
);

// Function to create a combined chart for CPU and Memory usage percentages
function createCombinedPercentChart(canvasId, dataLabels, cpuDataValues, memoryDataValues) {
	var ctx = document.getElementById(canvasId).getContext('2d');
	return new Chart(ctx, {
		type: 'line',
		data: {
			labels: dataLabels,
			datasets: [
				{
					label: 'CPU Usage (%)',
					data: cpuDataValues,
					backgroundColor: 'rgba(34, 129, 197, 0.1)', // Light color fill
					borderColor: 'rgba(34, 129, 197, 1)',     // Border color
					borderWidth: 2,
					fill: false,
					tension: 0.1,
					pointRadius: 0
				},
				{
					label: 'Memory Usage (%)',
					data: memoryDataValues,
					backgroundColor: 'rgba(216, 112, 255, 0.1)', // Light color fill
					borderColor: 'rgba(216, 112, 255, 1)',     // Border color
					borderWidth: 2,
					fill: false,
					tension: 0.1,
					pointRadius: 0
				}
			]
		},
		options: {
			plugins: {
				title: { display: false, text: 'CPU and Memory Usage (%)' },
				legend: { display: true }
			},
		scales: {
			x: { 
				display: true, 
				title: { display: false, text: 'Time' },
				grid: {
					color: (context) => context.index === 0 ? 'white': 'rgba(255,255,255,0.1)',
					borderDash: [5, 5], // Dashed grid lines
				},
			},
			y: { 
				title: { display: false, text: 'Usage (%)' }, 
				min: 0, 
				max:100, 
				grid: {
					color: (context) => context.index === 0 ? 'white' : 'rgba(255,255,255,0.1)', // White for the first vertical line
					borderDash: [5, 5], // Dashed grid lines
				},
			},
		}
		}
	});
}

// Function to fetch the latest data and update charts
function updateChart() {
	fetch('{% url "latest_data" %}')
		.then(response => response.json())
		.then(latestData => {
			// Update the combined percent chart
			updatePercentChartData(
				percentChart, 
				latestData.cpu_usage.timestamp, 
				latestData.cpu_usage.value, 
				latestData.memory_usage.value
			);

			// Update other charts
			updateChartData(networkChart, latestData.network_io.timestamp, latestData.network_io.value);
			updateChartData(diskChart, latestData.disk_io.timestamp, latestData.disk_io.value);
		})
		.catch(error => console.error('Error fetching latest data:', error));
}

// Function to update the combined percent chart data
function updatePercentChartData(chart, newTimestamp, newCpuValue, newMemoryValue) {
	chart.data.labels.push(newTimestamp);
	chart.data.datasets[0].data.push(newCpuValue);
	chart.data.datasets[1].data.push(newMemoryValue);

	// Remove oldest data point if exceeding max data points
	if (chart.data.labels.length > maxDataPoints) {
		chart.data.labels.shift();
		chart.data.datasets[0].data.shift();
		chart.data.datasets[1].data.shift();
	}

	chart.update();
}

// Function to update chart data for single datasets
function updateChartData(chart, newTimestamp, newValue) {
	chart.data.labels.push(newTimestamp);
	chart.data.datasets[0].data.push(newValue);

	// Remove oldest data point if exceeding max data points
	if (chart.data.labels.length > maxDataPoints) {
		chart.data.labels.shift();
		chart.data.datasets[0].data.shift();
	}

	chart.update();
}

// Update the chart every minute (60000 milliseconds)
setInterval(updateChart, 60000);
