(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];
  const dataElement = $('#overview-data');
  if (!dataElement) return;
  let data = JSON.parse(dataElement.textContent);
  let metric = 'traffic';
  let compare = true;
  let toastTimer;
  let pending;
  const names = { traffic: 'Lưu lượng', reach: 'Tiếp cận', leads: 'Leads', spend: 'Chi phí' };
  const number = new Intl.NumberFormat('vi-VN');
  const dateText = (iso) => iso.split('-').reverse().join('/');
  const esc = (value) => String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
  const rangeText = (start, end) => `${dateText(start)} – ${dateText(end)}`;

  function toast(message) {
    const element = $('#dashboard-toast');
    clearTimeout(toastTimer);
    element.textContent = message;
    element.hidden = false;
    toastTimer = setTimeout(() => { element.hidden = true; }, 4500);
  }

  function renderChart() {
    const container = $('#trend-chart');
    const series = data.charts.trends[metric];
    const width = container.clientWidth;
    if (!width) return;
    const height = container.clientHeight;
    const left = metric === 'spend' ? 48 : 36;
    const right = width - 20;
    const bottom = height - 40;
    const top = 25;
    const maximum = Math.max(...series.values, ...(compare ? series.previous : []), 1);
    const magnitude = 10 ** Math.floor(Math.log10(maximum / 4));
    const step = metric === 'traffic' ? 750 : Math.ceil(maximum / 4 / magnitude) * magnitude;
    const ceiling = step * 4;
    const x = (i) => series.values.length === 1 ? (left + right) / 2 : left + (right - left) * i / (series.values.length - 1);
    const y = (v) => bottom - v / ceiling * (bottom - top);
    const path = (values) => values.map((value, i) => `${i ? 'L' : 'M'}${x(i).toFixed(2)},${y(value).toFixed(2)}`).join(' ');
    const tickText = (v) => metric === 'spend' ? `${number.format(v / 1000000)}tr` : number.format(v);
    let svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}"><defs><linearGradient id="trend-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#0051aa" stop-opacity=".18"/><stop offset="100%" stop-color="#0051aa" stop-opacity="0"/></linearGradient></defs>`;
    for (let i = 1; i <= 4; i++) {
      const v = i * step;
      svg += `<line x1="${left}" x2="${right}" y1="${y(v)}" y2="${y(v)}" stroke="#f2f3ff"/><text x="${left - 8}" y="${y(v) + 4}" fill="#727784" font-family="Inter, sans-serif" font-size="10" text-anchor="end">${tickText(v)}</text>`;
    }
    svg += `<path d="${path(series.values)} L${x(series.values.length - 1)},${bottom} L${x(0)},${bottom} Z" fill="url(#trend-fill)"/>`;
    if (compare) svg += `<path d="${path(series.previous)}" fill="none" stroke="#a8b4d0" stroke-dasharray="3 4" stroke-width="1.5"/>`;
    svg += `<path d="${path(series.values)}" fill="none" stroke="#0051aa" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`;
    series.labels.forEach((label, i) => {
      svg += `<text x="${x(i)}" y="${height - 8}" fill="#727784" font-family="Inter, sans-serif" font-size="10" text-anchor="middle">${esc(label)}</text>`;
      if (i >= series.values.length - 2) svg += `<circle cx="${x(i)}" cy="${y(series.values[i])}" r="4" fill="white" stroke="#0051aa" stroke-width="2"/>`;
    });
    if (series.values.length > 2 && metric === 'traffic' && data.period.days === 30) {
      const i = series.values.length - 2;
      const boxX = Math.min(right - 105, Math.max(left, x(i) - 52));
      svg += `<rect x="${boxX}" y="${y(series.values[i]) - 35}" width="105" height="24" rx="6" fill="#131b2e"/><text x="${boxX + 52.5}" y="${y(series.values[i]) - 19}" fill="white" font-family="Inter, sans-serif" font-size="10" text-anchor="middle">+28% Tựu trường</text>`;
    }
    series.values.forEach((value, i) => {
      svg += `<circle class="chart-hit" data-point="${i}" cx="${x(i)}" cy="${y(value)}" r="12" fill="transparent" tabindex="0" role="button" aria-label="${esc(series.labels[i])}: ${number.format(value)}"/>`;
    });
    container.innerHTML = svg + '</svg><div class="chart-tooltip" hidden></div>';
    container.setAttribute('role', 'group');
    container.setAttribute('aria-label', `Xu hướng ${names[metric].toLowerCase()}, ${rangeText(data.period.start, data.period.end)}${compare ? ', so với kỳ trước' : ''}`);
    const tooltip = container.querySelector('.chart-tooltip');
    function showPoint(i) {
      tooltip.textContent = `${series.labels[i]} · ${names[metric]}: ${number.format(series.values[i])}${metric === 'spend' ? ' ₫' : ''}${compare ? ` | Kỳ trước: ${number.format(series.previous[i])}` : ''}`;
      tooltip.hidden = false;
      const half = tooltip.offsetWidth / 2;
      tooltip.style.left = `${Math.max(half, Math.min(width - half, x(i)))}px`;
      tooltip.style.top = `${Math.max(45, y(series.values[i]) - 8)}px`;
    }
    container.querySelectorAll('[data-point]').forEach((point) => {
      const show = () => showPoint(Number(point.dataset.point));
      point.addEventListener('pointerenter', show);
      point.addEventListener('focus', show);
      point.addEventListener('click', show);
      point.addEventListener('blur', () => { tooltip.hidden = true; });
    });
    container.onpointerleave = () => { tooltip.hidden = true; };
  }

  function render() {
    $$('[data-field]').forEach((element) => {
      if (data.fields[element.dataset.field] !== undefined) element.textContent = data.fields[element.dataset.field];
    });
    const period = data.period;
    $('#date-range-label').textContent = rangeText(period.start, period.end);
    $('#comparison-label').textContent = compare ? `(${rangeText(period.previous_start, period.previous_end)})` : '';
    $('#comparison > span:first-child').textContent = compare ? 'Kỳ trước' : 'Không so sánh';
    $('#comparison').setAttribute('aria-pressed', String(compare));
    $('#period-description').textContent = `Tổng hợp hiệu quả Marketing đa kênh của KinderHealth trong kỳ báo cáo (${rangeText(period.start, period.end)}${compare ? ' so với kỳ trước' : ''}).`;
    $('#current-legend').textContent = period.start === '2026-09-01' && period.end === '2026-09-30' ? 'Tháng 9/2026 (Kỳ hiện tại)' : `${rangeText(period.start, period.end)} (Kỳ hiện tại)`;
    $('#previous-legend').textContent = period.start === '2026-09-01' && period.end === '2026-09-30' ? 'Tháng 8/2026 (Kỳ trước)' : 'Kỳ trước';
    $('#previous-legend').parentElement.hidden = !compare;
    $$('#kpi-grid [data-field$="_previous"], #kpi-grid .font-metric-delta').forEach((el) => { el.hidden = !compare; });
    let note = $('#sample-period-note');
    if (!note) {
      note = document.createElement('p');
      note.id = 'sample-period-note';
      note.className = 'sample-period-note';
      note.textContent = 'Số liệu kỳ đang chọn được mô phỏng. Nhận định và kế hoạch bên dưới tham chiếu mẫu tháng 9/2026.';
      $('#insights').before(note);
    }
    note.hidden = period.start === '2026-09-01' && period.end === '2026-09-30';
    renderChart();
  }

  async function loadPeriod(start, end, selected = 'custom') {
    if (pending) pending.abort();
    const controller = new AbortController();
    pending = controller;
    $('#main-content').setAttribute('aria-busy', 'true');
    try {
      const query = new URLSearchParams({ start, end });
      const response = await fetch(`/api/v1/reports/overview?${query}`, { signal: controller.signal });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(typeof error.detail === 'string' ? error.detail : 'Khoảng thời gian không hợp lệ.');
      }
      data = await response.json();
      $$('#period-switcher button').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.period === selected)));
      render();
      const url = new URL(window.location.href);
      url.searchParams.set('start', start);
      url.searchParams.set('end', end);
      history.replaceState(null, '', url);
      toast('Đã cập nhật báo cáo với dữ liệu mẫu.');
      return true;
    } catch (error) {
      if (error.name !== 'AbortError') toast(error.message || 'Không tải được báo cáo. Vui lòng thử lại.');
      return false;
    } finally {
      if (pending === controller) {
        pending = null;
        $('#main-content').setAttribute('aria-busy', 'false');
      }
    }
  }

  function openDates() {
    $('#date-start').value = data.period.start;
    $('#date-end').value = data.period.end;
    $('#date-error').hidden = true;
    $('#date-dialog').showModal();
  }
  $('#date-range').addEventListener('click', openDates);
  $$('#period-switcher button').forEach((button) => button.addEventListener('click', () => {
    if (button.dataset.period === 'custom') return openDates();
    const end = '2026-09-30';
    const start = { '7': '2026-09-24', '30': '2026-09-01', '90': '2026-07-01', '180': '2026-04-01' }[button.dataset.period];
    loadPeriod(start, end, button.dataset.period);
  }));
  $('#date-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const start = $('#date-start').value;
    const end = $('#date-end').value;
    if (start > end) {
      $('#date-error').textContent = 'Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.';
      $('#date-error').hidden = false;
      return;
    }
    const button = $('#date-form button[type="submit"]');
    button.disabled = true;
    try { if (await loadPeriod(start, end)) $('#date-dialog').close(); }
    finally { button.disabled = false; }
  });
  $$('[data-close-dialog]').forEach((button) => button.addEventListener('click', () => button.closest('dialog').close()));
  $('#data-source').addEventListener('click', () => $('#source-dialog').showModal());
  $('#comparison').addEventListener('click', () => { compare = !compare; render(); });
  $$('#metric-switcher button').forEach((button) => button.addEventListener('click', () => {
    metric = button.dataset.metric;
    $$('#metric-switcher button').forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
    renderChart();
  }));
  $('#peak-detail').addEventListener('click', () => {
    const series = data.charts.trends[metric];
    const peak = Math.max(...series.values);
    const index = series.values.indexOf(peak);
    $('#peak-description').textContent = `Trong bộ dữ liệu mẫu, ngày ${dateText(series.dates[index])} có ${names[metric].toLowerCase()} cao nhất: ${number.format(peak)}${metric === 'spend' ? ' ₫' : ''}. Kỳ trước tại cùng vị trí: ${number.format(series.previous[index])}.`;
    $('#peak-dialog').showModal();
  });

  function closeExport() { $('#export-menu').hidden = true; $('#export-report').setAttribute('aria-expanded', 'false'); }
  $('#export-report').addEventListener('click', () => {
    const open = $('#export-menu').hidden;
    $('#export-menu').hidden = !open;
    $('#export-report').setAttribute('aria-expanded', String(open));
    if (open) $('#export-pdf').focus();
  });
  document.addEventListener('click', (event) => {
    if (!event.target.closest('#export-report, #export-menu')) closeExport();
  });
  function printReport(planOnly = false) {
    closeExport();
    document.body.classList.toggle('print-plan', planOnly);
    window.print();
  }
  window.addEventListener('afterprint', () => document.body.classList.remove('print-plan'));
  $('#export-pdf').addEventListener('click', () => printReport());
  $('#print-plan').addEventListener('click', () => printReport(true));
  $('#export-csv').addEventListener('click', async () => {
    closeExport();
    try {
      const query = new URLSearchParams({ start: data.period.start, end: data.period.end });
      const response = await fetch(`/api/v1/reports/overview/export?${query}`);
      if (!response.ok) throw new Error('Không xuất được báo cáo. Vui lòng thử lại.');
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement('a');
      link.href = url;
      link.download = `KDH-Tong-quan-${data.period.start}-${data.period.end}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      toast('Đã xuất báo cáo CSV. Bạn có thể mở bằng Excel.');
    } catch (error) { toast(error.message); }
  });


  new ResizeObserver(renderChart).observe($('#trend-chart'));
  render();
  const query = new URLSearchParams(location.search);
  if (query.has('start') && query.has('end')) loadPeriod(query.get('start'), query.get('end'));
})();
