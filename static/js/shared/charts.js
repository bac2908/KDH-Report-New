function ensureChart(elementId) {
  const container = document.getElementById(elementId);
  if (!container) return null;
  return echarts.init(container);
}

function renderRevenueTrend(chartData) {
  const chart = ensureChart('revenue-chart');
  if (!chart) return;

  const option = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: chartData.labels || [] },
    yAxis: { type: 'value' },
    series: [{
      data: chartData.values || [],
      type: 'line',
      smooth: true,
      areaStyle: {},
      itemStyle: { color: '#2d6cdf' },
    }],
  };
  chart.setOption(option);
}

function renderChannelMix(chartData) {
  const chart = ensureChart('channel-chart');
  if (!chart) return;

  const option = {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: '70%',
      data: (chartData.labels || []).map((label, index) => ({
        name: label,
        value: (chartData.values || [])[index] || 0,
      })),
    }],
  };
  chart.setOption(option);
}

function renderReportChart(series) {
  const chart = ensureChart('report-chart');
  if (!chart) return;

  const option = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: series.labels || [] },
    yAxis: { type: 'value' },
    series: [{
      data: series.values || [],
      type: 'bar',
      itemStyle: { color: '#1cbf7a' },
    }],
  };
  chart.setOption(option);
}

window.dashboardCharts = {
  renderOverview: function (charts) {
    renderRevenueTrend(charts.revenue_trend || { labels: [], values: [] });
    renderChannelMix(charts.channel_mix || { labels: [], values: [] });
  },
  renderReportChart,
};
