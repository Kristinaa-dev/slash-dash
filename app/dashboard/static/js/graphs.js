var ctx2 = document.getElementById('cpuChart').getContext('2d')
var cpuChart = new Chart(ctx2, {
type: 'line',
data: {
    labels: [], // This will be the timestamps
    datasets: [
    {
    label: 'CPU Usage',
    data: [], // This will be the CPU usage data
    borderColor: 'rgba(75, 192, 192, 1)',
    
    fill: true,
    backgroundColor: 'rgba(75, 192, 192, 0.4)',
    
    }
    ]
},
options: {
    scales: {
    y: {
        beginAtZero: true,
        max: 100
        
    }
    }
}
});

var ctx1 = document.getElementById('diskChart').getContext('2d');
var diskChart = new Chart(ctx1, {
type: 'doughnut',
data: {
    labels: ['Used', 'Free'],
    datasets: [
    {
    label: 'Disk Usage',
    data: [{{ disk_used|default:0 }}, {{ disk_free|default:0 }}],
    backgroundColor: ['rgba(255, 99, 132, 0.2)', 'rgba(54, 162, 235, 0.2)'],
    borderColor: ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)'],
    borderWidth: 1
    }
    ]
}
});
