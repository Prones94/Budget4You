function renderSpendingChart(labels, values){
  const spendingCtx = document.getElementById('spendingChart').getContext('2d')
  new Chart(spendingCtx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets:[{
        data:values,
        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'top'
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              return context.label + ': $' + context.raw
            }
          }
        }
      }
    }
  })
}

function renderGoalChart(goalNames, currentAmounts, targetAmounts) {
  const goalCtx = document.getElementById('goalChart').getContext('2d');
  new Chart(goalCtx, {
      type: 'bar',
      data: {
          labels: goalNames,
          datasets: [
              {
                  label: 'Current Amount',
                  data: currentAmounts,
                  backgroundColor: '#36A2EB'
              },
              {
                  label: 'Target Amount',
                  data: targetAmounts,
                  backgroundColor: '#FF6384'
              }
          ]
      },
      options: {
          responsive: true,
          scales: {
              x: { title: { display: true, text: 'Goals' }},
              y: { title: { display: true, text: 'Amount' }}
          }
      }
  });
}

