
var carClassNames = JSON.parse('{{ car_class_names|safe }}');
var carCounts = JSON.parse('{{ car_counts|safe }}');
var availableCarCounts = JSON.parse('{{ available_cars_class_counts|safe }}');

// Create the Chart.js script using Django template tags
var ctx = document.getElementById('carChart').getContext('2d');
var myChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: carClassNames,
        datasets: [
            {
                label: 'Total Cars',
                data: carCounts,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            },
            {
                label: 'Available Cars (Not on Rent)',
                data: availableCarCounts,
                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }
        ]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});
