(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];
  if (!$('#facebook-content-data')) return;
  let data = JSON.parse($('#facebook-content-data').textContent);
  const initial = new URLSearchParams(location.search);
  let compare = initial.get('compare') !== 'false', page = 1, pageSize = 5, pending, timer;
  const escape = (value) => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const number = (v) => new Intl.NumberFormat('vi-VN').format(v);
  const date = (v) => v.split('-').reverse().join('/');
  const range = (a, b) => `${date(a)} – ${date(b)}`;
  const presets = { '7': '2026-09-24', '30': '2026-09-01', '90': '2026-07-01', '180': '2026-04-01' };
  const sections = { kpis: 'fc-kpis', formats: 'fc-formats', topics: 'fc-topics', posts: 'fc-posts', engagement: 'fc-engagement', reach_mix: 'fc-reach', insights: 'fc-insights' };
  const params = () => ({ start: data.period.start, end: data.period.end, ...data.filters });
  function toast(text) {
    clearTimeout(timer); $('#dashboard-toast').textContent = text; $('#dashboard-toast').hidden = false;
    timer = setTimeout(() => { $('#dashboard-toast').hidden = true; }, 3500);
  }
  function saveURL() {
    const url = new URL(location.href);
    Object.entries({ ...params(), compare }).forEach(([k, v]) => v === '' ? url.searchParams.delete(k) : url.searchParams.set(k, v));
    history.replaceState(null, '', url);
  }
  function paginate() {
    const rows = $$('[data-fc-row]'), pages = Math.max(1, Math.ceil(rows.length / pageSize));
    page = Math.min(Math.max(page, 1), pages);
    rows.forEach((row, i) => { row.hidden = i < (page - 1) * pageSize || i >= page * pageSize; });
    $('#fc-page-size').value = String(pageSize);
    $('#fc-prev').disabled = page === 1; $('#fc-next').disabled = page >= pages;
    $('#fc-page-number').textContent = `${page} / ${pages}`;
    $('#fc-post-count').textContent = rows.length ? `Hiển thị ${(page - 1) * pageSize + 1}–${Math.min(page * pageSize, rows.length)} / ${rows.length} bài mẫu phù hợp` : '0 bài mẫu phù hợp';
  }
  function renderContext() {
    const p = data.period;
    $('#date-range-label').textContent = range(p.start, p.end);
    $('#comparison > span:first-child').textContent = compare ? 'Kỳ trước' : 'Không so sánh';
    $('#comparison-label').textContent = compare ? `(${range(p.previous_start, p.previous_end)})` : '';
    $('#comparison').setAttribute('aria-pressed', String(compare));
    $$('[data-fc-comparison]').forEach(el => { el.hidden = !compare; });
    const preset = p.end === '2026-09-30' && Object.keys(presets).find(key => presets[key] === p.start);
    $$('[data-period]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.period === (preset || 'custom'))));
    const f = data.filters;
    $('.fc-filter-status').hidden = !f.query && f.format === 'all' && f.topic === 'all';
    const format = $('#fc-format').querySelector(`option[value="${f.format}"]`).textContent;
    const topic = $('#fc-topic').querySelector(`option[value="${f.topic}"]`).textContent;
    $('#fc-filter-caption').textContent = `Bộ lọc bảng bài viết: ${format} · ${topic}${f.query ? ` · “${f.query}”` : ''}`;
    paginate();
  }
  async function load(changes = {}) {
    pending?.abort(); const controller = new AbortController(); pending = controller;
    $('#main-content').setAttribute('aria-busy', 'true'); $('#fc-error').hidden = true;
    try {
      const response = await fetch(`/api/v1/reports/facebook-content?${new URLSearchParams({ ...params(), ...changes })}`, { signal: controller.signal });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(typeof error.detail === 'string' ? error.detail : 'Bộ lọc không hợp lệ hoặc không tải được báo cáo.');
      }
      const next = await response.json();
      if (controller.signal.aborted) return false;
      if (Object.keys(sections).some(key => typeof next.fragments?.[key] !== 'string')) throw new Error('Dữ liệu báo cáo chưa đầy đủ.');
      data = next; page = 1;
      Object.entries(sections).forEach(([key, id]) => { document.getElementById(id).innerHTML = next.fragments[key]; });
      renderContext(); saveURL(); toast('Đã cập nhật báo cáo Facebook Content.'); return true;
    } catch (error) {
      if (error.name !== 'AbortError') {
        const message = error instanceof TypeError ? 'Không kết nối được máy chủ. Vui lòng thử lại.' : error.message;
        $('#fc-error').textContent = message; $('#fc-error').hidden = false; toast(message);
        ['#date-error', '#fc-filter-error'].forEach(s => { if ($(s).closest('dialog').open) { $(s).textContent = message; $(s).hidden = false; } });
      }
      return false;
    } finally { if (pending === controller) { pending = null; $('#main-content').setAttribute('aria-busy', 'false'); } }
  }
  function openDates() {
    $('#date-start').value = data.period.start; $('#date-end').value = data.period.end;
    $('#date-error').hidden = true; $('#date-dialog').showModal();
  }
  $('#date-range').addEventListener('click', openDates);
  $$('[data-period]').forEach(button => button.addEventListener('click', () => {
    if (button.dataset.period === 'custom') return openDates();
    load({ start: presets[button.dataset.period], end: '2026-09-30' });
  }));
  $('#date-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const start = $('#date-start').value, end = $('#date-end').value;
    if (start > end) { $('#date-error').textContent = 'Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.'; $('#date-error').hidden = false; return; }
    event.submitter.disabled = true;
    try { if (await load({ start, end })) $('#date-dialog').close(); } finally { event.submitter.disabled = false; }
  });
  $('#comparison').addEventListener('click', () => { compare = !compare; renderContext(); saveURL(); });
  $('#data-source').addEventListener('click', () => $('#source-dialog').showModal());
  $('#fc-advanced').addEventListener('click', () => {
    ['query', 'format', 'topic'].forEach(k => { $(`#fc-${k}`).value = data.filters[k]; });
    $('#fc-filter-error').hidden = true; $('#fc-filter-dialog').showModal();
  });
  $('#fc-reset').addEventListener('click', () => { $('#fc-query').value = ''; $('#fc-format').value = 'all'; $('#fc-topic').value = 'all'; });
  $('#fc-filter-form').addEventListener('submit', async event => {
    event.preventDefault(); event.submitter.disabled = true;
    try { if (await load({ query: $('#fc-query').value.trim(), format: $('#fc-format').value, topic: $('#fc-topic').value })) $('#fc-filter-dialog').close(); }
    finally { event.submitter.disabled = false; }
  });
  $('#fc-clear').addEventListener('click', () => load({ query: '', format: 'all', topic: 'all' }));
  const detailMetrics = (items) => `<dl class="fc-detail-grid">${items.map(([label, value]) => `<div><dt>${escape(label)}</dt><dd>${escape(value)}</dd></div>`).join('')}</dl>`;
  function detail(title, html) { $('#fc-detail-title').textContent = title; $('#fc-detail-content').innerHTML = html; $('#fc-detail-dialog').showModal(); }
  function topicDetail(row) { return `<section class="fc-detail-topic"><h3>${escape(row.label)}</h3>${detailMetrics([['Số bài', row.count], ['Reach', number(row.reach)], ['ER', `${number(row.er)}%`]])}<p>${escape(row.description)}</p><button type="button" class="fc-link" data-fc-topic-filter="${escape(row.key)}">Lọc bài mẫu thuộc chủ đề này →</button></section>`; }
  document.addEventListener('click', async event => {
    const close = event.target.closest('[data-close-dialog]'); if (close) close.closest('dialog').close();
    const sort = event.target.closest('[data-fc-sort]'); if (sort) await load({ sort: sort.dataset.fcSort });
    const post = event.target.closest('[data-fc-post]');
    if (post) {
      const row = data.posts.find(r => r.id === post.dataset.fcPost);
      detail(row.title, `<p>${date(row.date)} · ${escape(row.format)} · ${escape(row.topic)}</p>` + detailMetrics([['Reach', number(row.reach)], ['Engagement', number(row.engagement)], ['ER', `${number(row.er)}%`], ['Comments', number(row.comments)], ['Shares', number(row.shares)], ['Clicks', number(row.clicks)]]) + '<p>Bài viết mẫu theo thiết kế. Chưa có URL hoặc tài khoản Meta thật để mở bài gốc.</p>');
    }
    const topic = event.target.closest('[data-fc-topic]');
    if (topic) detail('Chi tiết chủ đề', topicDetail(data.topics.find(r => r.key === topic.dataset.fcTopic)));
    if (event.target.closest('#fc-topic-details')) detail('Hiệu quả theo chủ đề', data.topics.map(topicDetail).join(''));
    const filter = event.target.closest('[data-fc-topic-filter]');
    if (filter && await load({ topic: filter.dataset.fcTopicFilter, query: '', format: 'all' })) { $('#fc-detail-dialog').close(); $('#fc-posts').scrollIntoView({ block: 'start' }); }
    if (event.target.closest('#fc-prev')) { page--; paginate(); }
    if (event.target.closest('#fc-next')) { page++; paginate(); }
  });
  document.addEventListener('change', event => { if (event.target.id === 'fc-page-size') { pageSize = Number(event.target.value); page = 1; paginate(); } });
  function closeExport() { $('#export-menu').hidden = true; $('#export-report').setAttribute('aria-expanded', 'false'); }
  $('#export-report').addEventListener('click', () => {
    const open = $('#export-menu').hidden; $('#export-menu').hidden = !open; $('#export-report').setAttribute('aria-expanded', String(open));
    if (open) $('#export-pdf').focus();
  });
  document.addEventListener('click', event => { if (!event.target.closest('#export-menu, #export-report')) closeExport(); });
  $('#export-pdf').addEventListener('click', () => { closeExport(); window.print(); });
  async function download() {
    closeExport(); const state = params();
    try {
      const response = await fetch(`/api/v1/reports/facebook-content/export?${new URLSearchParams({ ...state, compare })}`);
      if (!response.ok) throw new Error('Không xuất được báo cáo. Vui lòng thử lại.');
      const url = URL.createObjectURL(await response.blob()), a = document.createElement('a');
      a.href = url; a.download = `KDH-Facebook-Content-${state.start}-${state.end}.csv`;
      document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
      toast('Đã tải CSV gồm tổng quan và toàn bộ bài mẫu phù hợp bộ lọc.');
    } catch (error) { toast(error.message); }
  }
  $('#export-csv').addEventListener('click', download); $('#fc-download').addEventListener('click', download);
  renderContext();
  const supplied = Object.fromEntries(Object.keys(params()).filter(k => initial.has(k)).map(k => [k, initial.get(k)]));
  async function restoreView() {
    if (Object.keys(supplied).length) await load(supplied);
    const link = $$('#facebook-content-submenu [data-section]').find(link => link.dataset.path === initial.get('view'));
    if (link) {
      await document.fonts.ready;
      document.getElementById(link.dataset.section)?.scrollIntoView({ block: 'start' });
    }
  }
  restoreView();
})();
