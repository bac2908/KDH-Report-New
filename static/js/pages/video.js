(() => {
  'use strict';
  const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
  if (!$('#video-data')) return;
  let data = JSON.parse($('#video-data').textContent), pending, toastTimer, selectedDay = 0, chartMetric = 'views';
  const channel = data.channel, api = `/api/v1/video-reports/${channel}`;
  const initial = new URLSearchParams(location.search);
  let compare = initial.get('compare') !== 'false';
  const format = n => new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(n);
  const date = s => s.split('-').reverse().join('/');
  const escape = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const presets = { '7': '2026-09-24', '30': '2026-09-01', '90': '2026-07-01', '180': '2026-04-01' };
  const params = () => ({ start: data.period.start, end: data.period.end, ...data.filters });
  function toast(message) {
    clearTimeout(toastTimer); $('#dashboard-toast').textContent = message; $('#dashboard-toast').hidden = false;
    toastTimer = setTimeout(() => { $('#dashboard-toast').hidden = true; }, 4000);
  }
  function saveURL() {
    const url = new URL(location.href);
    Object.entries({ ...params(), compare }).forEach(([key, value]) => value === '' ? url.searchParams.delete(key) : url.searchParams.set(key, value));
    history.replaceState(null, '', url);
  }
  function series() { return chartMetric === 'watch_hours' && channel === 'youtube' ? data.chart.watch_series : data.chart.series; }
  function chart() {
    const [first, second] = series(), hideSecond = channel === 'youtube' && !compare;
    const max = Math.max(...first, ...(channel === 'youtube' && !hideSecond ? second : []), 1) * 1.18;
    const maxSecond = channel === 'tiktok' ? Math.max(...second, 1) * 1.38 : max;
    const points = (values, top) => values.map((value, index) => [first.length === 1 ? 400 : 12 + index * 776 / (first.length - 1), 252 - value / top * 220]);
    const path = points => {
      let result = `M${points[0].join(',')}`;
      for (let i = 1; i < points.length; i++) {
        const a = points[i-1], b = points[i], previous = points[i-2] || a, next = points[i+1] || b;
        result += ` C${a[0]+(b[0]-previous[0])/6},${a[1]+(b[1]-previous[1])/6} ${b[0]-(next[0]-a[0])/6},${b[1]-(next[1]-a[1])/6} ${b.join(',')}`;
      }
      return result;
    };
    const a = points(first, max), b = points(second, maxSecond), color = channel === 'tiktok' ? '#15803d' : '#9e7dff';
    const lines = [32, 106, 179, 252].map(y => `<line x1="0" y1="${y}" x2="800" y2="${y}" stroke="#f0f1f8"/>`).join('');
    $('#vd-chart-svg').innerHTML = `<title id="vd-chart-title">${channel === 'tiktok' ? 'Chi tiêu và Leads; hai thang đo riêng' : chartMetric === 'views' ? 'Lượt xem theo ngày' : 'Thời gian xem theo ngày (giờ)'}</title><defs><linearGradient id="vd-gradient" x1="0" x2="0" y1="0" y2="1"><stop stop-color="#0051aa" stop-opacity=".12"/><stop offset="1" stop-color="#0051aa" stop-opacity="0"/></linearGradient></defs>${lines}<path d="${path(a)} L${a.at(-1)[0]},252 L${a[0][0]},252 Z" fill="url(#vd-gradient)"/><path d="${path(a)}" fill="none" stroke="#0051aa" stroke-width="2.6" vector-effect="non-scaling-stroke"/>${hideSecond ? '' : `<path d="${path(b)}" fill="none" stroke="${color}" stroke-width="1.8" stroke-dasharray="5 5" vector-effect="non-scaling-stroke"/>`}${first.length === 1 ? `<circle cx="400" cy="${a[0][1]}" r="4" fill="#0051aa"/>` : ''}<text x="12" y="16" fill="#727784" font-size="11">${format(Math.ceil(max))}${channel === 'tiktok' ? ' ₫' : chartMetric === 'watch_hours' ? ' giờ' : ' lượt xem'}</text>${channel === 'tiktok' ? `<text x="788" y="16" text-anchor="end" fill="#15803d" font-size="11">${Math.ceil(maxSecond)} Leads</text>` : ''}`;
    const indices = [...new Set([0, .25, .5, .75, 1].map(n => Math.round(n * (data.chart.dates.length - 1))))];
    $('#vd-chart-dates').innerHTML = indices.map(index => `<span>${date(data.chart.dates[index]).slice(0, 5)}</span>`).join('');
    $('#vd-chart-secondary').hidden = hideSecond;
    $('#vd-chart-tooltip').hidden = true;
  }
  function tooltip(index) {
    selectedDay = Math.max(0, Math.min(data.chart.dates.length - 1, index));
    const [a,b] = series(), suffix = chartMetric === 'watch_hours' ? ' giờ' : '';
    $('#vd-chart-tooltip').textContent = `${date(data.chart.dates[selectedDay])}\n${data.chart.labels[0]}: ${format(a[selectedDay])}${channel === 'tiktok' ? ' ₫' : suffix}${channel === 'tiktok' || compare ? `\n${data.chart.labels[1]}: ${format(b[selectedDay])}${channel === 'tiktok' ? '' : suffix}` : ''}`;
    $('#vd-chart-tooltip').hidden = false;
  }
  $('#vd-chart').addEventListener('pointermove', event => {
    const rect = $('#vd-chart').getBoundingClientRect();
    tooltip(Math.round((event.clientX - rect.left) / rect.width * (data.chart.dates.length - 1)));
  });
  $('#vd-chart').addEventListener('pointerleave', () => { $('#vd-chart-tooltip').hidden = true; });
  $('#vd-chart').addEventListener('focus', () => tooltip(selectedDay));
  $('#vd-chart').addEventListener('blur', () => { $('#vd-chart-tooltip').hidden = true; });
  $('#vd-chart').addEventListener('keydown', event => { if (['ArrowLeft','ArrowRight'].includes(event.key)) { event.preventDefault(); tooltip(selectedDay + (event.key === 'ArrowRight' ? 1 : -1)); } });
  $$('[data-chart-metric]').forEach(button => button.addEventListener('click', () => {
    chartMetric = button.dataset.chartMetric;
    $$('[data-chart-metric]').forEach(b => b.setAttribute('aria-pressed', String(b === button))); chart();
  }));
  function renderContext() {
    const p = data.period, range = `${date(p.start)} – ${date(p.end)}`;
    $('#date-range-label').textContent = range; $('#vd-chart-period').textContent = range;
    $('#comparison > span:first-child').textContent = compare ? 'Kỳ trước' : 'Không so sánh';
    $('#comparison-label').textContent = compare ? `(${date(p.previous_start)} – ${date(p.previous_end)})` : '';
    $('#comparison').setAttribute('aria-pressed', String(compare));
    $$('[data-video-comparison]').forEach(el => { el.hidden = !compare; });
    const preset = p.end === '2026-09-30' && Object.keys(presets).find(key => presets[key] === p.start);
    $$('[data-period]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.period === (preset || 'custom'))));
    $('#vd-filter-status').hidden = !data.filters.query && data.filters.status === 'all' && data.filters.sort === 'default';
    $('#vd-filter-status span').textContent = `${data.rows.length} kết quả${data.filters.query ? ` · “${data.filters.query}”` : ''}`;
    chart();
  }
  async function load(changes = {}) {
    pending?.abort(); const controller = new AbortController(); pending = controller;
    $('#main-content').setAttribute('aria-busy', 'true'); $('#vd-error').hidden = true;
    try {
      const response = await fetch(`${api}?${new URLSearchParams({ ...params(), ...changes })}`, { signal: controller.signal });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(typeof error.detail === 'string' ? error.detail : 'Bộ lọc hoặc khoảng ngày không hợp lệ.');
      }
      const next = await response.json();
      if (controller.signal.aborted) return false;
      if (['kpis','table','funnel','videos'].some(key => typeof next.fragments?.[key] !== 'string')) throw new Error('Báo cáo chưa đầy đủ. Vui lòng thử lại.');
      data = next;
      $('#vd-kpis').innerHTML = next.fragments.kpis; $('#vd-table').innerHTML = next.fragments.table;
      $('[data-video-fragment="funnel"]').innerHTML = next.fragments.funnel;
      if ($('#vd-videos')) $('#vd-videos').innerHTML = next.fragments.videos;
      renderContext(); saveURL(); toast('Đã cập nhật báo cáo dữ liệu mẫu.'); return true;
    } catch (error) {
      if (error.name !== 'AbortError') {
        const message = error instanceof TypeError ? 'Không kết nối được máy chủ. Vui lòng thử lại.' : error.message;
        $('#vd-error').textContent = message; $('#vd-error').hidden = false;
        ['#date-error','#vd-filter-error'].forEach(selector => { if ($(selector).closest('dialog').open) { $(selector).textContent = message; $(selector).hidden = false; } });
        toast(message);
      }
      return false;
    } finally { if (pending === controller) { pending = null; $('#main-content').setAttribute('aria-busy', 'false'); } }
  }
  function openDates() { $('#date-start').value = data.period.start; $('#date-end').value = data.period.end; $('#date-error').hidden = true; $('#date-dialog').showModal(); }
  $('#date-range').addEventListener('click', openDates);
  $$('[data-period]').forEach(button => button.addEventListener('click', () => button.dataset.period === 'custom' ? openDates() : load({ start: presets[button.dataset.period], end: '2026-09-30' })));
  $('#date-form').addEventListener('submit', async event => {
    event.preventDefault(); const button = event.submitter; button.disabled = true;
    try { if (await load({ start: $('#date-start').value, end: $('#date-end').value })) $('#date-dialog').close(); } finally { button.disabled = false; }
  });
  $('#comparison').addEventListener('click', () => { compare = !compare; renderContext(); saveURL(); });
  $('#data-source').addEventListener('click', () => $('#source-dialog').showModal());
  $$('[data-open-filter]').forEach(button => button.addEventListener('click', () => {
    $('#vd-query').value = data.filters.query; $('#vd-sort').value = data.filters.sort;
    if ($('#vd-status')) $('#vd-status').value = data.filters.status;
    $('#vd-filter-error').hidden = true; $('#vd-filter-dialog').showModal();
  }));
  $('#vd-filter-form').addEventListener('submit', async event => {
    event.preventDefault(); const button = event.submitter; button.disabled = true;
    try { if (await load({ query: $('#vd-query').value.trim(), status: $('#vd-status')?.value || 'all', sort: $('#vd-sort').value })) $('#vd-filter-dialog').close(); } finally { button.disabled = false; }
  });
  $('#vd-clear').addEventListener('click', () => load({ query: '', status: 'all', sort: 'default' }));
  document.addEventListener('click', event => {
    event.target.closest('[data-close-dialog]')?.closest('dialog').close();
    const button = event.target.closest('[data-video-detail]'); if (!button) return;
    const row = [...data.rows, ...data.videos].find(r => r.id === button.dataset.videoDetail); if (!row) return;
    $('#vd-detail-title').textContent = row.title;
    const names = { spend:'Chi tiêu (₫)', reach:'Reach', views:'Lượt xem', clicks:'Clicks', ctr:'CTR (%)', cpa:'CPA (₫)', leads:'Leads', duration:'Thời gian xem TB', completion:'Completion (%)', subscribers:'Subscribers mới' };
    $('#vd-detail-body').innerHTML = `<p>${escape(row.id)}${row.date ? ` · ${date(row.date)}` : ''}${row.audience ? ` · ${escape(row.audience)}` : ''}</p><dl class="vd-detail-grid">${Object.entries(names).filter(([key]) => key in row).map(([key,label]) => `<div><dt>${label}</dt><dd>${typeof row[key] === 'number' ? format(row[key]) : escape(row[key])}</dd></div>`).join('')}</dl><p>Dữ liệu minh họa theo thiết kế. Chưa có liên kết video hoặc chiến dịch thật.</p>`;
    $('#vd-detail-dialog').showModal();
  });
  function closeExport() { $('#export-menu').hidden = true; $('#export-report').setAttribute('aria-expanded', 'false'); }
  $('#export-report').addEventListener('click', () => { const open = $('#export-menu').hidden; $('#export-menu').hidden = !open; $('#export-report').setAttribute('aria-expanded', String(open)); if (open) $('#export-pdf').focus(); });
  document.addEventListener('click', event => { if (!event.target.closest('#export-menu, #export-report')) closeExport(); });
  $('#export-pdf').addEventListener('click', () => { closeExport(); window.print(); });
  $('#export-csv').addEventListener('click', async () => {
    closeExport(); const current = params();
    try {
      const response = await fetch(`${api}/export?${new URLSearchParams({ ...current, compare })}`);
      if (!response.ok) throw new Error('Không xuất được báo cáo. Vui lòng thử lại.');
      const url = URL.createObjectURL(await response.blob()), link = document.createElement('a');
      link.href = url; link.download = `KDH-${channel}-${current.start}-${current.end}.csv`;
      document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
      toast('Đã tải báo cáo CSV theo kỳ và bộ lọc đang chọn.');
    } catch (error) { toast(error.message); }
  });
  const planKey = 'kdh-report-new:youtube:demo-plan';
  $('#vd-plan')?.addEventListener('click', () => {
    let selected = []; try { selected = JSON.parse(localStorage.getItem(planKey) || '[]'); } catch { /* local storage can be disabled */ }
    if (!Array.isArray(selected)) selected = [];
    $$('#vd-plan-form input').forEach(input => { input.checked = selected.includes(input.name); });
    $('#vd-plan-error').hidden = true; $('#vd-plan-dialog').showModal();
  });
  $('#vd-plan-form').addEventListener('submit', event => {
    event.preventDefault();
    try {
      const selected = $$('#vd-plan-form input:checked').map(input => input.name);
      localStorage.setItem(planKey, JSON.stringify(selected)); $('#vd-plan-dialog').close();
      toast(`Đã lưu ${selected.length} lựa chọn kế hoạch trên trình duyệt này.`);
    } catch { $('#vd-plan-error').textContent = 'Trình duyệt không cho phép lưu. Vui lòng bật bộ nhớ cục bộ.'; $('#vd-plan-error').hidden = false; }
  });
  renderContext();
  (async () => {
    const supplied = Object.fromEntries(Object.keys(params()).filter(key => initial.has(key)).map(key => [key, initial.get(key)]));
    if (Object.keys(supplied).length) await load(supplied);
    const link = $$(`#${channel}-submenu [data-section]`).find(link => link.dataset.path === initial.get('view'));
    if (link) { await document.fonts.ready; document.getElementById(link.dataset.section)?.scrollIntoView({ block: 'start' }); }
  })();
})();
