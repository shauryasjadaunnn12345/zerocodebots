
(function () {
  // Initialize variables
  let chart;
  let chartType = 'line';
  let intentsSortBy = 'count';
  let questionsSortBy = 'frequency';
  
  // Date range functionality
  const dateRangeBtn = document.getElementById('dateRangeBtn');
  const dateRangeFilter = document.getElementById('dateRangeFilter');
  const dateRangeSelect = document.getElementById('dateRangeSelect');
  const customDateRange = document.getElementById('customDateRange');
  const applyDateFilter = document.getElementById('applyDateFilter');
  
  dateRangeBtn.addEventListener('click', function() {
    dateRangeFilter.style.display = dateRangeFilter.style.display === 'none' ? 'flex' : 'none';
  });
  
  dateRangeSelect.addEventListener('change', function() {
    if (this.value === 'custom') {
      customDateRange.style.display = 'flex';
    } else {
      customDateRange.style.display = 'none';
    }
  });
  
  applyDateFilter.addEventListener('click', function() {
    // In a real implementation, this would trigger a data refresh with the selected date range
    const dateRange = dateRangeSelect.value;
    let startDate, endDate;
    
    if (dateRange === 'custom') {
      startDate = document.getElementById('startDate').value;
      endDate = document.getElementById('endDate').value;
    } else {
      // Calculate date range based on selection
      endDate = new Date();
      startDate = new Date();
      startDate.setDate(startDate.getDate() - parseInt(dateRange));
    }
    
    // Show loading state
    this.innerHTML = '<span class="loading"></span> Applying...';
    this.disabled = true;
    
    // Simulate API call
    setTimeout(() => {
      this.innerHTML = 'Apply';
      this.disabled = false;
      dateRangeFilter.style.display = 'none';
      
      // Show notification
      showNotification('Date filter applied successfully');
    }, 1000);
  });
  
  // Refresh data functionality
  const refreshBtn = document.getElementById('refreshData');
  refreshBtn.addEventListener('click', function() {
    const originalContent = this.innerHTML;
    this.innerHTML = '<span class="loading"></span>';
    
    // Simulate data refresh
    setTimeout(() => {
      this.innerHTML = originalContent;
      showNotification('Data refreshed successfully');
      
      // Animate progress bars
      document.querySelectorAll('.progress-inner, .bar-inner').forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
          bar.style.width = width;
        }, 100);
      });
    }, 1500);
  });
  
  // Collapsible sections
  document.querySelectorAll('.collapsible').forEach(button => {
    button.addEventListener('click', function() {
      const targetId = this.getAttribute('data-target');
      const content = document.getElementById(targetId);
      
      this.classList.toggle('collapsed');
      
      if (content.style.maxHeight) {
        content.style.maxHeight = null;
      } else {
        content.style.maxHeight = content.scrollHeight + "px";
      }
    });
  });
  
  // Initialize all collapsible sections as expanded
  document.querySelectorAll('.collapsible-content').forEach(content => {
    content.style.maxHeight = content.scrollHeight + "px";
  });
  
  // Sorting functionality for intents
  const sortIntentsBtn = document.getElementById('sortIntents');
  const sortIntentsText = document.getElementById('sortIntentsText');
  const intentBreakdown = document.getElementById('intentBreakdown');
  
  sortIntentsBtn.addEventListener('click', function() {
    intentsSortBy = intentsSortBy === 'count' ? 'alphabetical' : 'count';
    sortIntentsText.textContent = intentsSortBy;
    
    // Get all intent elements
    const intentElements = Array.from(intentBreakdown.querySelectorAll('[data-intent]'));
    
    // Sort based on current criteria
    if (intentsSortBy === 'alphabetical') {
      intentElements.sort((a, b) => {
        return a.dataset.intent.localeCompare(b.dataset.intent);
      });
    } else {
      intentElements.sort((a, b) => {
        return parseInt(b.dataset.count) - parseInt(a.dataset.count);
      });
    }
    
    // Re-append in sorted order
    const container = intentElements[0].parentNode;
    intentElements.forEach(el => container.appendChild(el));
  });
  
  // Sorting functionality for questions
  const sortQuestionsBtn = document.getElementById('sortQuestions');
  const sortQuestionsText = document.getElementById('sortQuestionsText');
  const topQuestions = document.getElementById('topQuestions');
  
  sortQuestionsBtn.addEventListener('click', function() {
    questionsSortBy = questionsSortBy === 'frequency' ? 'alphabetical' : 'frequency';
    sortQuestionsText.textContent = questionsSortBy;
    
    // Get all question elements
    const questionElements = Array.from(topQuestions.querySelectorAll('[data-question]'));
    
    // Sort based on current criteria
    if (questionsSortBy === 'alphabetical') {
      questionElements.sort((a, b) => {
        return a.dataset.question.localeCompare(b.dataset.question);
      });
    } else {
      questionElements.sort((a, b) => {
        return parseInt(b.dataset.count) - parseInt(a.dataset.count);
      });
    }
    
    // Re-append in sorted order
    const container = questionElements[0].parentNode;
    questionElements.forEach(el => container.appendChild(el));
  });
  
  // Chart functionality
  const labels = {{ chart_labels_json|default:"[]"|safe }};
  const values = {{ chart_values_json|default:"[]"|safe }};
  
  if (labels.length) {
      const canvasEl = document.getElementById('eventsChart');
      const ctx = canvasEl.getContext('2d');

    chart = new Chart(ctx, {
      type: chartType,
      data: {
        labels: labels,
        datasets: [{
          data: values,
          label: "Events",
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59,130,246,0.08)",
          fill: true,
          tension: 0.25,
          pointRadius: 0,
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        elements: {
          point: { radius: 0 }
        },
        scales: {
          y: { 
            beginAtZero: true,
            grid: { color: 'rgba(0,0,0,0.05)' }
          },
          x: {
            grid: { display: false },
            ticks: { maxTicksLimit: 12 }
          }
        },
        plugins: {
          legend: { display: false },
          zoom: {
            zoom: { wheel: { enabled: false }, pinch: { enabled: false }, mode: 'x' },
            pan: { enabled: true, mode: 'x' }
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleFont: { size: 14 },
            bodyFont: { size: 13 },
            padding: 8,
            cornerRadius: 6
          }
        },
        interaction: { intersect: false, mode: 'index' }
      }
    });
    
    // Chart type toggle
    document.getElementById('chartTypeToggle').addEventListener('click', function() {
      chartType = chartType === 'line' ? 'bar' : 'line';
      chart.config.type = chartType;
      
      if (chartType === 'bar') {
        chart.config.data.datasets[0].backgroundColor = 'rgba(59,130,246,0.6)';
        chart.config.data.datasets[0].borderColor = 'rgba(59,130,246,1)';
      } else {
        chart.config.data.datasets[0].backgroundColor = 'rgba(59,130,246,0.1)';
        chart.config.data.datasets[0].borderColor = '#3b82f6';
      }
      
      chart.update();
    });
    
    // Zoom controls
    document.getElementById('zoomIn').addEventListener('click', function() {
      chart.zoom(1.1);
    });
    
    document.getElementById('zoomOut').addEventListener('click', function() {
      chart.zoom(0.9);
    });
    
    document.getElementById('resetZoom').addEventListener('click', function() {
      chart.resetZoom();
    });
  }
  
  // Notification helper
  function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #333;
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 1000;
      transform: translateY(100px);
      opacity: 0;
      transition: all 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
      notification.style.transform = 'translateY(0)';
      notification.style.opacity = '1';
    }, 10);
    
    // Animate out and remove
    setTimeout(() => {
      notification.style.transform = 'translateY(100px)';
      notification.style.opacity = '0';
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 3000);
  }
  
  // Animate progress bars on load
  window.addEventListener('load', function() {
    document.querySelectorAll('.progress-inner, .bar-inner').forEach(bar => {
      const width = bar.style.width;
      bar.style.width = '0%';
      setTimeout(() => {
        bar.style.width = width;
      }, 100);
    });
  });
})();
