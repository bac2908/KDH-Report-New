(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];
  const initial = $('#facebook-ads-data');
  if (!initial) return;
  let data = JSON.parse(initial.textContent);
  let pending, toastTimer;
  const initialParams = new URLSearchParams(location.search);
  let compare = initialParams.get('compare') !== 'false';
  const escape = (value) => String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
  const date = (iso) => iso.split('-').reverse().join('/');
  const range = (start, end) => `${date(start)} – ${date(end)}`;
  const presets = { '7': '2026-09-24', '30': '2026-09-01', '90': '2026-07-01', '180': '2026-04-01' };
  const targets = {
    'fb-tong-quan-hieu-qua': 'fb-summary', 'fb-hieu-qua-chien-dich': 'fb-campaigns',
    'fb-doi-tuong-va-phan-phoi': 'fb-audience', 'fb-hieu-qua-noi-dung-quang-cao': 'fb-creatives',
    'chuyen-doi-va-chi-phi': 'fb-funnel', 'fb-tang-truong-va-phan-tich': 'fb-insights',
  };
  const sections = { kpis: 'fb-kpis', campaigns: 'fb-campaign-rows', funnel: 'fb-funnel-body', audience: 'fb-audience-body', creatives: 'fb-creatives-grid', insights: 'fb-insights' };
  const analysisHeadings = { highlights: 'Điểm nổi bật', warnings: 'Vấn đề cần chú ý', actions: 'Hành động đề xuất' };
  const params = () => ({ start: data.period.start, end: data.period.end, ...data.filters });
  const metricsMarkup = (items) => `<dl class="fb-detail-metrics">${items.map(([label, value]) => `<div><dt>${escape(label)}</dt><dd>${escape(value)}</dd></div>`).join('')}</dl>`;

  function toast(message) {
    clearTimeout(toastTimer);
    $('#dashboard-toast').textContent = message;
    $('#dashboard-toast').hidden = false;
    toastTimer = setTimeout(() => { $('#dashboard-toast').hidden = true; }, 4200);
  }
  function saveURL() {
    const url = new URL(location.href);
    Object.entries(params()).forEach(([key, value]) => value ? url.searchParams.set(key, value) : url.searchParams.delete(key));
    url.searchParams.set('compare', String(compare));
    history.replaceState(null, '', url);
  }
  function renderContext() {
    const p = data.period, f = data.filters;
    const period = range(p.start, p.end);
    $('#date-range-label').textContent = period;
    $('#fb-period-caption').textContent = `Dữ liệu mẫu · ${period} (${p.days} ngày)`;
    $('#comparison > span:first-child').textContent = compare ? 'Kỳ trước' : 'Không so sánh';
    $('#comparison-label').textContent = compare ? `(${range(p.previous_start, p.previous_end)})` : '';
    $('#comparison').setAttribute('aria-pressed', String(compare));
    $$('[data-fb-comparison]').forEach((element) => { element.hidden = !compare; });
    const selected = p.end === '2026-09-30' ? Object.keys(presets).find((key) => presets[key] === p.start) : undefined;
    $$('#period-switcher button').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.period === (selected || 'custom'))));
    const labels = [];
    if (f.campaign !== 'all') labels.push(data.campaign_options.find((row) => row.id === f.campaign)?.name || f.campaign);
    if (f.status !== 'all') labels.push(f.status === 'active' ? 'Đang hoạt động' : 'Cần tối ưu');
    if (f.query) labels.push(`Tìm kiếm: “${f.query}”`);
    $('#fb-filter-caption').textContent = labels.length ? `${data.campaigns.length} chiến dịch · ${labels.join(' · ')}` : 'Tất cả chiến dịch';
    $('#fb-clear').hidden = !labels.length;
    $('#fb-sort span:last-child').textContent = ({ cpl_asc: 'CPL: thấp → cao', cpl_desc: 'CPL: cao → thấp', spend_desc: 'Chi tiêu: cao → thấp', leads_desc: 'Leads: cao → thấp' })[f.sort];
    $('#fb-campaign-table th:nth-child(7)').setAttribute('aria-sort', f.sort === 'cpl_asc' ? 'ascending' : f.sort === 'cpl_desc' ? 'descending' : 'none');
  }
  async function load(changes = {}) {
    pending?.abort();
    const controller = new AbortController();
    pending = controller;
    $('#main-content').setAttribute('aria-busy', 'true');
    $('#fb-error').hidden = true;
    try {
      const response = await fetch(`/api/v1/reports/facebook-ads?${new URLSearchParams({ ...params(), ...changes })}`, { signal: controller.signal });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(typeof error.detail === 'string' ? error.detail : 'Không tải được báo cáo. Vui lòng kiểm tra bộ lọc hoặc thử lại.');
      }
      const next = await response.json();
      if (controller.signal.aborted) return false;
      // Do not commit new state until every fragment is available.
      if (Object.keys(sections).some((key) => typeof next.fragments?.[key] !== 'string')) throw new Error('Dữ liệu báo cáo chưa đầy đủ. Vui lòng thử lại.');
      data = next;
      Object.entries(sections).forEach(([key, id]) => { document.getElementById(id).innerHTML = data.fragments[key]; });
      renderContext();
      saveURL();
      toast('Đã cập nhật báo cáo Facebook Ads theo bộ lọc.');
      return true;
    } catch (error) {
      if (error.name !== 'AbortError') {
        const message = error.message || 'Không tải được báo cáo. Vui lòng thử lại.';
        $('#fb-error').textContent = message;
        $('#fb-error').hidden = false;
        ['#date-error', '#fb-filter-error'].forEach((selector) => {
          if ($(selector).closest('dialog').open) { $(selector).textContent = message; $(selector).hidden = false; }
        });
        toast(message);
      }
      return false;
    } finally {
      if (pending === controller) { pending = null; $('#main-content').setAttribute('aria-busy', 'false'); }
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
    load({ start: presets[button.dataset.period], end: '2026-09-30' });
  }));
  $('#date-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const start = $('#date-start').value, end = $('#date-end').value;
    if (start > end) {
      $('#date-error').textContent = 'Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.';
      $('#date-error').hidden = false;
      return;
    }
    const button = event.submitter;
    button.disabled = true;
    try { if (await load({ start, end })) $('#date-dialog').close(); }
    finally { button.disabled = false; }
  });
  $('#comparison').addEventListener('click', () => { compare = !compare; renderContext(); saveURL(); });
  $('#data-source').addEventListener('click', () => $('#source-dialog').showModal());
  $('#fb-advanced').addEventListener('click', () => {
    ['query', 'campaign', 'status'].forEach((key) => { $(`#fb-${key}`).value = data.filters[key]; });
    $('#fb-filter-error').hidden = true;
    $('#fb-filter-dialog').showModal();
  });
  $('#fb-reset').addEventListener('click', () => {
    $('#fb-query').value = ''; $('#fb-campaign').value = 'all'; $('#fb-status').value = 'all';
    $('#fb-filter-error').hidden = true;
  });
  $('#fb-filter-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = event.submitter;
    button.disabled = true;
    try {
      if (await load({ query: $('#fb-query').value.trim(), campaign: $('#fb-campaign').value, status: $('#fb-status').value })) $('#fb-filter-dialog').close();
    } finally { button.disabled = false; }
  });
  $('#fb-clear').addEventListener('click', () => load({ query: '', campaign: 'all', status: 'all' }));
  $('#fb-sort').addEventListener('click', () => load({ sort: data.filters.sort === 'cpl_asc' ? 'cpl_desc' : 'cpl_asc' }));

  function detail(title, content) {
    $('#fb-detail-title').textContent = title;
    $('#fb-detail-content').innerHTML = content;
    $('#fb-detail-dialog').showModal();
  }
  document.addEventListener('click', (event) => {
    const close = event.target.closest('[data-close-dialog]');
    if (close) close.closest('dialog').close();
    const campaign = event.target.closest('[data-campaign-detail]');
    if (campaign) {
      const row = data.campaigns.find((item) => item.id === campaign.dataset.campaignDetail);
      if (!row) return;
      detail(row.name, `<p>ID: ${escape(row.id)} · ${escape(row.status_label)} · ${escape(range(data.period.start, data.period.end))}</p>` + metricsMarkup([
        ['Chi tiêu', row.display.spend], ['Ngân sách mẫu', row.display.budget], ['Reach', row.display.reach],
        ['Hiển thị', row.display.impressions], ['Clicks', row.display.clicks], ['CTR', row.display.ctr],
        ['Leads', row.display.leads], ['CPL', row.display.cpl], ['Lịch hẹn', row.display.appointments],
      ]) + '<p class="fb-small">Dữ liệu minh họa. CTR = Clicks / Hiển thị; CPL = Chi tiêu / Leads. Không thay đổi chiến dịch thực tế.</p>');
    }
    const creative = event.target.closest('[data-creative-detail]');
    if (creative) {
      const row = data.creatives.find((item) => item.id === creative.dataset.creativeDetail);
      if (!row) return;
      detail(row.name, `<p>${escape(row.type_label)} · ${escape(range(data.period.start, data.period.end))}</p><img class="fb-detail-image" src="${escape(row.image)}" alt="${escape(row.name)}">` + metricsMarkup([
        ['Chi tiêu', row.display.spend], ['Hiển thị', row.display.impressions], ['Clicks', row.display.clicks],
        ['CTR', row.display.ctr], ['Leads', row.display.leads], ['CPL', row.display.cpl],
      ]) + '<p class="fb-small">Ảnh minh họa mẫu nội dung; không có tệp video hoặc bộ ảnh carousel gốc để phát.</p>');
    }
  });
  function filterLibrary() {
    const type = $('#fb-creative-type').value;
    let visible = 0;
    $$('#fb-library-content [data-creative-type]').forEach((card) => {
      card.hidden = type !== 'all' && card.dataset.creativeType !== type;
      if (!card.hidden) visible++;
    });
    $('#fb-library-empty').hidden = visible > 0;
  }
  $('#fb-library').addEventListener('click', () => {
    $('#fb-library-content').innerHTML = [...$('#fb-creatives-grid').querySelectorAll('article')].map((card) => card.outerHTML).join('') + '<p id="fb-library-empty" class="fb-empty" hidden>Không có mẫu quảng cáo phù hợp bộ lọc.</p>';
    $('#fb-creative-type').value = 'all';
    filterLibrary();
    $('#fb-library-dialog').showModal();
  });
  $('#fb-creative-type').addEventListener('change', filterLibrary);
  function analysisMarkup() {
    return metricsMarkup(data.metrics.map((metric) => [metric.label, metric.text])) + Object.entries(analysisHeadings).map(([key, title]) => `<section><h3>${title}</h3><ul>${data.insights[key].map((text) => `<li>${escape(text)}</li>`).join('') || '<li>Chưa có dữ liệu để đánh giá.</li>'}</ul></section>`).join('');
  }
  $('#fb-optimize').addEventListener('click', () => {
    $('#fb-analysis-period').textContent = `${range(data.period.start, data.period.end)} · ${$('#fb-filter-caption').textContent}`;
    $('#fb-analysis-content').innerHTML = analysisMarkup();
    $('#fb-analysis-dialog').showModal();
  });
  function download(blob, filename) {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url; anchor.download = filename;
    document.body.appendChild(anchor); anchor.click(); anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  $('#fb-analysis-download').addEventListener('click', () => {
    const lines = ['KDH — BÁO CÁO TỐI ƯU FACEBOOK ADS', $('#fb-analysis-period').textContent, data.analysis_notice, '', ...data.metrics.map((m) => `${m.label}: ${m.text}`)];
    Object.entries(analysisHeadings).forEach(([key, title]) => lines.push('', title, ...data.insights[key].map((text) => `• ${text}`)));
    download(new Blob(['\ufeff' + lines.join('\r\n')], { type: 'text/plain;charset=utf-8' }), `KDH-Facebook-Ads-Phan-tich-${data.period.start}-${data.period.end}.txt`);
  });
  function closeExport() { $('#export-menu').hidden = true; $('#export-report').setAttribute('aria-expanded', 'false'); }
  $('#export-report').addEventListener('click', () => {
    const open = $('#export-menu').hidden;
    $('#export-menu').hidden = !open;
    $('#export-report').setAttribute('aria-expanded', String(open));
    if (open) $('#export-pdf').focus();
  });
  document.addEventListener('click', (event) => { if (!event.target.closest('#export-menu, #export-report')) closeExport(); });
  function clearPrint() { document.body.classList.remove('fb-print-analysis'); $('.fb-print-only')?.remove(); }
  window.addEventListener('afterprint', clearPrint);
  function print(analysis = false) {
    closeExport(); clearPrint();
    if (analysis) {
      const paper = document.createElement('article');
      paper.className = 'fb-print-only';
      paper.innerHTML = `<h1>Báo cáo tối ưu Facebook Ads</h1><p>${escape($('#fb-analysis-period').textContent)}</p><p>${escape(data.analysis_notice)}</p>${analysisMarkup()}`;
      $('#main-content').appendChild(paper);
      document.body.classList.add('fb-print-analysis');
    }
    $$('dialog[open]').reverse().forEach((dialog) => dialog.close());
    window.print();
  }
  $('#export-pdf').addEventListener('click', () => print());
  $('#fb-analysis-print').addEventListener('click', () => print(true));
  $('#export-csv').addEventListener('click', async () => {
    closeExport();
    const snapshot = params();
    try {
      const response = await fetch(`/api/v1/reports/facebook-ads/export?${new URLSearchParams({ ...snapshot, compare })}`);
      if (!response.ok) throw new Error('Không xuất được báo cáo. Vui lòng thử lại.');
      download(await response.blob(), `KDH-Facebook-Ads-${snapshot.start}-${snapshot.end}.csv`);
      toast('Đã xuất CSV theo kỳ, chiến dịch và bộ lọc hiện tại.');
    } catch (error) { toast(error.message); }
  });

  function selectView(view, scroll = true) {
    if (!Object.hasOwn(targets, view)) view = 'fb-tong-quan-hieu-qua';
    $$('#dashboard-sidebar a[data-path]').forEach((link) => {
      if (!Object.hasOwn(targets, link.dataset.path)) return;
      if (link.dataset.path === view) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
    if (scroll) document.getElementById(targets[view]).scrollIntoView({ block: 'start', behavior: 'smooth' });
  }
  renderContext();
  selectView(initialParams.get('view'), false);
  async function restore() {
    const supplied = Object.fromEntries(Object.keys(params()).filter((key) => initialParams.has(key)).map((key) => [key, initialParams.get(key)]));
    if (Object.keys(supplied).length) await load(supplied);
    if (Object.hasOwn(targets, initialParams.get('view'))) {
      await document.fonts.ready;
      selectView(initialParams.get('view'));
    }
  }
  restore();
})();
