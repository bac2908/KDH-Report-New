async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function renderKpis(metrics) {
  const grid = document.getElementById('kpi-grid');
  if (!grid) return;

  grid.innerHTML = metrics.map((metric) => {
    const value = metric.unit === '$' ? `$${metric.value.toLocaleString()}` : metric.value.toLocaleString();
    const deltaClass = metric.delta >= 0 ? 'up' : 'down';
    const deltaText = `${Math.abs(metric.delta)}%`;
    return `
      <article class="kpi-card">
        <div class="label">${metric.label}</div>
        <div class="value">${value}</div>
        <div class="delta ${deltaClass}">${deltaText} vs last month</div>
      </article>
    `;
  }).join('');
}

async function loadOverview() {
  try {
    const data = await fetchJson('/api/v1/reports/overview');
    renderKpis(data.metrics || []);
    window.dashboardCharts.renderOverview(data.charts || {});
  } catch (error) {
    console.error('Failed to load overview data', error);
  }
}

async function loadReport(reportType) {
  try {
    const data = await fetchJson(`/api/v1/reports/${reportType}`);
    const summaryRoot = document.getElementById('report-summary');
    if (summaryRoot) {
      summaryRoot.innerHTML = `
        <h3>${data.data?.summary?.title || reportType}</h3>
        <p>Status: ${data.data?.summary?.status || 'healthy'}</p>
      `;
    }
    window.dashboardCharts.renderReportChart(data.data?.series || { labels: [], values: [] });
  } catch (error) {
    console.error('Failed to load report data', error);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const config = window.dashboardConfig || { reportType: 'overview' };
  if (config.reportType === 'overview') {
    loadOverview();
    return;
  }
  loadReport(config.reportType);
});
