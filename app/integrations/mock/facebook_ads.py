"""Deterministic Facebook Ads demo. All ratios derive from the same raw counts."""
from datetime import date, datetime, timedelta, timezone
import math
import unicodedata

from app.integrations.mock.overview import DEFAULT_START, DEFAULT_END, validate_range

COUNTS = ('spend', 'budget', 'reach', 'impressions', 'clicks', 'leads', 'landing_views', 'appointments')
CAMPAIGNS = [
    dict(id='893120491', name='[V1] Tiêm Chủng Mùa Hè - Lead Inbound', objective='Tạo Lead', status='active',
         spend=12500000, budget=15000000, reach=92400, impressions=600000, clicks=4520, leads=245, landing_views=2300, appointments=82),
    dict(id='893120492', name='[V2] Khám Nhi Chuyên Sâu - Retargeting', objective='Tin Nhắn / Lead', status='active',
         spend=8200000, budget=8000000, reach=58100, impressions=380000, clicks=2840, leads=160, landing_views=1450, appointments=54),
    dict(id='893120493', name='[V3] Gói Sức Khỏe Tổng Quát', objective='Tạo Lead', status='attention',
         spend=5700000, budget=6000000, reach=33700, impressions=220000, clicks=1560, leads=80, landing_views=750, appointments=26),
]
CREATIVES = [
    dict(id='video-01', campaign_id='893120491', name='Bác sĩ tư vấn dinh dưỡng cho bé', type='video', type_label='Video ngắn', image='/static/img/facebook-ads/video.jpg', spend=9200000, leads=192, clicks=3400, impressions=450000),
    dict(id='carousel-01', campaign_id='893120492', name='Gói tiêm chủng trọn gói mùa hè', type='carousel', type_label='Carousel', image='/static/img/facebook-ads/carousel.jpg', spend=7500000, leads=144, clicks=2700, impressions=340000),
    dict(id='image-01', campaign_id='893120493', name='Banner khám sức khỏe tổng quát', type='image', type_label='Hình ảnh tĩnh', image='/static/img/facebook-ads/image.jpg', spend=4500000, leads=58, clicks=1150, impressions=170000),
]


def rounded(value):
    return math.floor(value + .5)


def num(value):
    return '—' if value is None else f'{rounded(value):,}'.replace(',', '.')


def money(value):
    return '—' if value is None else num(value) + ' ₫'


def percent(value):
    return '—' if value is None else f'{value:.2f}'.replace('.', ',') + '%'


def divide(a, b, factor=1):
    return a / b * factor if b else None


def calculated(raw):
    row = dict(raw)
    row.update(ctr=divide(row['clicks'], row['impressions'], 100),
               cpc=divide(row['spend'], row['clicks']), cpl=divide(row['spend'], row['leads']),
               cr=divide(row['leads'], row['clicks'], 100))
    if 'appointments' in row:
        row.update(cpa=divide(row['spend'], row['appointments']), appointment_rate=divide(row['appointments'], row['leads'], 100),
                   landing_rate=divide(row['landing_views'], row['clicks'], 100))
    row['display'] = {key: money(value) if key in ('spend', 'budget', 'cpc', 'cpl', 'cpa') else
                      percent(value) if key in ('ctr', 'cr', 'appointment_rate', 'landing_rate') else num(value)
                      for key, value in row.items() if isinstance(value, (int, float)) or value is None}
    return row


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.casefold().replace('đ', 'd')) if not unicodedata.combining(c))


def recommendations(campaigns, totals, creatives):
    highlights, warnings, actions = [], [], []
    eligible = [c for c in campaigns if c['cpl'] is not None]
    if not campaigns:
        return dict(highlights=['Không có chiến dịch phù hợp bộ lọc.'], warnings=[], actions=['Nới bộ lọc để xem dữ liệu và đề xuất.'])
    if eligible:
        best, worst = min(eligible, key=lambda c: c['cpl']), max(eligible, key=lambda c: c['cpl'])
        highlights.append(f"{best['name']} có CPL thấp nhất: {best['display']['cpl']}, tạo {best['display']['leads']} Leads.")
        if len(eligible) > 1 and worst['cpl'] > best['cpl'] * 1.15:
            warnings.append(f"{worst['name']} có CPL {worst['display']['cpl']}, cao hơn chiến dịch tốt nhất {percent((worst['cpl'] / best['cpl'] - 1) * 100)}.")
            actions.append(f"Thử phân bổ lại tối đa 20% ngân sách {worst['name']} sang {best['name']}; theo dõi CPL và chất lượng Lead trước khi tăng thêm. Đây là đề xuất, ngân sách chưa được thay đổi.")
    if totals['appointment_rate'] is not None:
        highlights.append(f"{totals['display']['appointments']} lịch hẹn từ {totals['display']['leads']} Leads; tỷ lệ chốt lịch {totals['display']['appointment_rate']}.")
    for row in campaigns:
        if row['spend'] > row['budget']:
            warnings.append(f"{row['name']} vượt ngân sách mẫu {money(row['spend'] - row['budget'])}.")
    if creatives:
        best_ad = min((c for c in creatives if c['cpl'] is not None), key=lambda c: c['cpl'], default=None)
        if best_ad:
            highlights.append(f"Trong các mẫu quảng cáo được cung cấp, “{best_ad['name']}” đạt CPL {best_ad['display']['cpl']}.")
        actions.append('Thử biến thể nội dung và lời kêu gọi hành động; so sánh CTR, CPL và lịch hẹn trong cùng kỳ trước khi chọn mẫu tốt hơn.')
    if not warnings:
        warnings.append('Chưa phát hiện vượt ngân sách hoặc chênh lệch CPL lớn trong các chiến dịch đang chọn.')
    actions.append('Đối soát Lead với lịch hẹn thực tế. Các tỷ lệ hiện tại được tính từ bộ dữ liệu minh họa, chưa đồng bộ Meta hoặc CRM.')
    return dict(highlights=highlights, warnings=warnings, actions=actions)


def facebook_ads_payload(start: date | None = None, end: date | None = None, query='', status='all', campaign='all', sort='cpl_asc'):
    start, end = start or DEFAULT_START, end or DEFAULT_END
    validate_range(start, end)
    if status not in ('all', 'active', 'attention') or sort not in ('cpl_asc', 'cpl_desc', 'spend_desc', 'leads_desc'):
        raise ValueError('Bộ lọc không hợp lệ.')
    if campaign not in ['all'] + [c['id'] for c in CAMPAIGNS]:
        raise ValueError('Chiến dịch không tồn tại trong dữ liệu mẫu.')
    days = (end - start).days + 1
    ratio = days / 30
    selected = [c for c in CAMPAIGNS if (status == 'all' or c['status'] == status)
                and (campaign == 'all' or c['id'] == campaign)
                and normalize(query.strip()) in normalize(c['name'] + ' ' + c['id'])]
    campaigns = [calculated({**c, **{key: rounded(c[key] * ratio) for key in COUNTS}}) for c in selected]
    for row in campaigns:
        row['status_label'] = 'Đang hoạt động' if row['status'] == 'active' else 'Cần tối ưu'
        row['performance'] = 'Hiệu suất cao' if row['cpl'] is not None and row['cpl'] < 52000 else 'Cần tối ưu' if row['status'] == 'attention' else 'Ổn định'
    key, direction = sort.rsplit('_', 1)
    campaigns.sort(key=lambda c: (c[key] is None, (-c[key] if direction == 'desc' else c[key]) if c[key] is not None else 0))
    totals = calculated({key: sum(row[key] for row in campaigns) for key in COUNTS})
    factors = dict(spend=.958, budget=1, reach=1.123, impressions=1.08, clicks=1.004, leads=1.184, landing_views=1.12, appointments=1.15)
    previous = calculated({key: sum(rounded(c[key] * ratio / factors[key]) for c in selected) for key in COUNTS})
    metrics = []
    for key, label, icon in [('spend', 'Tổng Chi tiêu', 'payments'), ('reach', 'Lượt Tiếp Cận', 'visibility'),
                              ('clicks', 'Click Liên Kết', 'ads_click'), ('leads', 'Leads Thành Công', 'person_add'),
                              ('cpl', 'Chi Phí / Lead (CPL)', 'trending_down'), ('cr', 'Tỷ Lệ Chuyển Đổi', 'percent')]:
        current, prior = totals[key], previous[key]
        delta = (current / prior - 1) * 100 if prior and current is not None else None
        metrics.append(dict(key=key, label=label, icon=icon, value=current, text=totals['display'][key], delta=delta,
                            delta_text=percent(abs(delta)) if delta is not None else '—', arrow='↑' if delta is not None and delta >= 0 else '↓',
                            favorable=delta is not None and (delta <= 0 if key in ('spend', 'cpl') else delta >= 0),
                            note='CTR: ' + totals['display']['ctr'] if key == 'clicks' else 'Leads / Clicks' if key == 'cr' else 'so với kỳ trước'))
    selected_ids = {row['id'] for row in campaigns}
    creatives = [calculated({**c, **{key: rounded(c[key] * ratio) for key in ('spend', 'leads', 'clicks', 'impressions')}})
                 for c in CREATIVES if c['campaign_id'] in selected_ids]
    weights = [58, 22, 14, 6]
    amounts = [int(totals['spend'] * w / 100) for w in weights]
    amounts[-1] += totals['spend'] - sum(amounts)
    placements = [dict(name=name, percent=w if totals['spend'] else 0, spend=amount, text=money(amount), color=color)
                  for name, w, amount, color in zip(['Facebook Feed (Bảng tin chính)', 'Instagram Feed', 'Facebook & Instagram Reels', 'Stories & Khác'],
                                                    weights, amounts, ['#0051aa', '#9e7dff', '#e62f83', '#727784'])]
    insights = recommendations(campaigns, totals, creatives)
    return dict(report_type='facebook-ads', data_source='mock', generated_at=datetime.now(timezone.utc).isoformat(),
                period=dict(start=start.isoformat(), end=end.isoformat(), days=days,
                            previous_start=(start - timedelta(days=days)).isoformat(), previous_end=(start - timedelta(days=1)).isoformat()),
                filters=dict(query=query.strip(), status=status, campaign=campaign, sort=sort),
                campaign_options=[dict(id=c['id'], name=c['name']) for c in CAMPAIGNS],
                campaigns=campaigns, totals=totals, previous=previous, metrics=metrics, creatives=creatives, placements=placements,
                insights=insights, analysis_method='rules',
                analysis_notice='Phân tích tự động theo quy tắc trên dữ liệu mẫu; chưa sử dụng mô hình AI hoặc kết nối Meta Marketing API.')
