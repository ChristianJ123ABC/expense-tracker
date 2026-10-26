//Sources

//chart.js graphs
//https://www.chartjs.org/docs/latest/charts/doughnut.html#pie
//https://tobiasahlin.com/blog/chartjs-charts-to-get-you-started/
//https://www.w3schools.com/ai/ai_chartjs.asp
//https://www.chartjs.org/docs/latest/getting-started/
//https://www.chartjs.org/docs/latest/configuration/subtitle.html
//https://stackoverflow.com/questions/51348585/parsing-values-from-external-json-file-with-chart-js



//Parses the data from /dashboard and displays it

var categoryCanvas = document.getElementById("categoryChart");
if (categoryCanvas) {   
    new Chart(categoryCanvas, {
        type: "doughnut",
        data: {
            labels: JSON.parse(categoryCanvas.dataset.names),
            datasets: [{ data: JSON.parse(categoryCanvas.dataset.totals) }]
        },
        options:{
            maintainAspectRatio: false,
            plugins:{
                title: { display: true, text: "Spending by Category"},
                subtitle: {display: true, text: "Current Month"}
            }
        }
    });
}

var monthCanvas = document.getElementById("monthChart");
new Chart(monthCanvas, {
    type: "bar",
    data: {
        labels: [JSON.parse(monthCanvas.dataset.label)],
        datasets: [
            { label: "Income (" + JSON.parse(monthCanvas.dataset.currency) + ")",   data: [JSON.parse(monthCanvas.dataset.income)] },
            { label: "Expenses (" + JSON.parse(monthCanvas.dataset.currency) + ")", data: [JSON.parse(monthCanvas.dataset.expenses)] }
        ]
    },
    options:{
        maintainAspectRatio: false,
        plugins:{
            title: { display: true, text: "Income vs Expenses"},
            subtitle: { display: true, text: JSON.parse(monthCanvas.dataset.label)}
        }
    }
});