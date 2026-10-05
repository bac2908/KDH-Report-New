"""Deterministic demo reports from the supplied TikTok and YouTube designs."""
from copy import deepcopy
from datetime import date, timedelta
import math
import unicodedata

from app.integrations.mock.overview import DEFAULT_START, DEFAULT_END, validate_range

CAMPAIGNS = [
    dict(id='TK-V1', title='Khám Nhi Mùa Hè - Video Viral', audience='Phụ huynh có con 1–5 tuổi (HCM)', spend=8500000, reach=110000, views=95000, clicks=3200, leads=165, status='high', status_label='Hiệu quả cao'),
    dict(id='TK-V2', title='Tiêm Chủng Trọn Gói - Review Bác Sĩ', audience='Mẹ bầu & trẻ sơ sinh', spend=6200000, reach=85000, views=68000, clicks=2100, leads=110, status='stable', status_label='Ổn định'),
    dict(id='TK-V3', title='Gói Khám Dinh Dưỡng - Trẻ Em', audience='Trẻ biếng ăn / chậm tăng cân', spend=3800000, reach=50800, views=35400, clicks=1120, leads=40, status='optimize', status_label='Cần tối ưu CPL'),
]
TIKTOK_VIDEOS = [
    dict(id='Video 01', title='Bác sĩ hướng dẫn chăm sóc bé sốt tại nhà', views=74200, duration='18s', completion=42.5, ctr=3.1, leads=98, badge='🏆 Nhiều Lead nhất', color='blue'),
    dict(id='Video 02', title='Review phòng khám nhi KinderHealth quận 1', views=58100, duration='22s', completion=48.2, ctr=2.8, leads=72, badge='🎬 Giữ chân tốt nhất', color='purple'),
    dict(id='Video 03', title='Top 3 loại vaccine cần thiết cho trẻ dưới 1 tuổi', views=42000, duration='14s', completion=31.0, ctr=1.9, leads=45, badge='Tiềm năng', color='gray'),
]
YOUTUBE_VIDEOS = [
    dict(id='YT-01', title='Bác sĩ hướng dẫn xử lý sốt xuất huyết tại nhà đúng cách', date='2026-09-12', views=28400, duration='4:12', ctr=8.2, subscribers=340, image='video-1.jpg'),
    dict(id='YT-02', title='4 lưu ý quan trọng khi tiêm chủng vaccine 6 trong 1 cho bé', date='2026-09-05', views=22100, duration='3:50', ctr=7.5, subscribers=215, image='video-2.jpg'),
    dict(id='YT-03', title='Review phòng khám chuẩn 5 sao KinderHealth Quận 1', date='2026-09-18', views=18900, duration='2:45', ctr=6.9, subscribers=180, image='video-3.jpg'),
    dict(id='YT-04', title='Thực đơn dinh dưỡng tăng đề kháng mùa giao mùa cho trẻ', date='2026-09-22', views=15600, duration='4:05', ctr=6.1, subscribers=125, image='video-4.jpg'),
]


def _fold(value: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', value.casefold().replace('đ', 'd')) if not unicodedata.combining(c))


def _ratio(a: float, b: float) -> float:
    return round(a / b * 100, 2) if b else 0


def _allocate(total: int, weights: list[float]) -> list[int]:
    raw = [total * weight / sum(weights) for weight in weights]
    result = [int(value) for value in raw]
    for index in sorted(range(len(raw)), key=lambda i: raw[i] - result[i], reverse=True)[:total - sum(result)]:
        result[index] += 1
    return result


def _metric(key: str, label: str, value: int | float | str, icon: str, delta: str, unit: str = '', secondary: str = '', source: str = '', assessment: str = '') -> dict:
    return dict(key=key, label=label, value=value, icon=icon, delta=delta, unit=unit, secondary=secondary, source=source, assessment=assessment)


def video_payload(channel: str, start: date | None = None, end: date | None = None,
                  query: str = '', status: str = 'all', sort: str = 'default') -> dict:
    if channel not in ('tiktok', 'youtube'):
        raise ValueError('Kênh video không được hỗ trợ.')
    start, end = start or DEFAULT_START, end or DEFAULT_END
    validate_range(start, end)
    if len(query) > 200 or status not in ('all', 'high', 'stable', 'optimize') or sort not in ('default', 'views', 'leads', 'spend', 'subscribers'):
        raise ValueError('Bộ lọc báo cáo không hợp lệ.')
    if channel == 'youtube' and (status != 'all' or sort in ('leads', 'spend')):
        raise ValueError('Bộ lọc này chỉ áp dụng cho TikTok Ads.')
    if channel == 'tiktok' and sort == 'subscribers':
        raise ValueError('Bộ lọc subscribers chỉ áp dụng cho YouTube.')
    days = (end - start).days + 1
    scale = lambda value: round(value * days / 30)
    period = dict(start=start.isoformat(), end=end.isoformat(), days=days,
                  previous_start=(start - timedelta(days=days)).isoformat(), previous_end=(start - timedelta(days=1)).isoformat())
    if channel == 'tiktok':
        campaigns = deepcopy(CAMPAIGNS)
        for row in campaigns:
            for key in ('spend', 'reach', 'views', 'clicks', 'leads'):
                row[key] = scale(row[key])
            row['ctr'] = _ratio(row['clicks'], row['reach'])
            row['cpa'] = round(row['spend'] / row['leads']) if row['leads'] else 0
        totals = {key: sum(row[key] for row in campaigns) for key in ('spend', 'reach', 'views', 'clicks', 'leads')}
        totals.update(impressions=scale(748500), views_6s=scale(84500))
        totals['ctr'] = _ratio(totals['clicks'], totals['reach'])
        totals['cpa'] = round(totals['spend'] / totals['leads']) if totals['leads'] else 0
        metrics = [
            _metric('spend', 'Tổng chi tiêu (Spend)', totals['spend'], 'payments', '+6,4%', '₫'),
            _metric('reach', 'Lượt tiếp cận (Reach)', totals['reach'], 'visibility', '+21,2%'),
            _metric('clicks', 'Lượt click & CTR', totals['clicks'], 'ads_click', '+0,4 điểm % CTR', secondary=f"{totals['ctr']}%"),
            _metric('views', 'Lượt xem video & 6s', totals['views'], 'play_circle', '+15,8%', secondary=f"{totals['views_6s']/1000:.1f}K 6s"),
            _metric('leads', 'Khách hàng tiềm năng', totals['leads'], 'group_add', '+14,5%', 'Leads'),
            _metric('cpa', 'Chi phí / Lead (CPA)', totals['cpa'], 'trending_down', '−4,1% (Tối ưu tốt)', '₫'),
        ]
        videos = deepcopy(TIKTOK_VIDEOS)
        for row in videos:
            row['views'], row['leads'] = scale(row['views']), scale(row['leads'])
        rows = [r for r in campaigns if (status == 'all' or r['status'] == status) and _fold(query) in _fold(f"{r['id']} {r['title']} {r['audience']}")]
        funnel = [dict(label=label, value=totals[key], percent=_ratio(totals[key], totals['impressions']), color=color)
                  for key, label, color in [('impressions', 'Lượt hiển thị (Impressions)', 'blue'), ('views', 'Lượt xem video (Video Views)', 'blue'), ('views_6s', 'Lượt xem 6 giây (6s Views)', 'blue'), ('clicks', 'Lượt click liên kết (Clicks)', 'purple'), ('leads', 'Leads thành công (Leads)', 'green')]]
        chart_keys, chart_labels = ['spend', 'leads'], ['Chi tiêu (₫)', 'Leads']
        chart_totals = [totals['spend'], totals['leads']]
    else:
        totals = dict(views=scale(124500), watch_hours=scale(4850), subscribers=scale(920), impressions=scale(850400), ctr=6.8, duration='3:45', clicks=scale(4120), visits=scale(3280), leads=scale(245), appointments=scale(98))
        metrics = [
            _metric('views', 'Tổng lượt xem (Views)', totals['views'], 'visibility', '+21,5%', source='Nguồn: YouTube · mẫu', assessment='Ổn định'),
            _metric('watch_hours', 'Thời gian xem (Watch Time)', totals['watch_hours'], 'schedule', '+18,2%', 'giờ', source='Tổng thời lượng phát', assessment='Tích cực'),
            _metric('subscribers', 'Subscribers mới', totals['subscribers'], 'group_add', '+24,6%', 'sub', source='Người đăng ký kênh', assessment='Tăng tốc'),
            _metric('impressions', 'Lượt hiển thị (Impressions)', totals['impressions'], 'bolt', '+14,8%', source='YouTube Search & Browse', assessment='Mở rộng'),
            _metric('ctr', 'CTR Thumbnail', totals['ctr'], 'ads_click', '+0,8 điểm %', '%', source='Tỷ lệ nhấp hiển thị', assessment='Hiệu quả cao'),
            _metric('duration', 'Thời lượng xem TB', totals['duration'], 'timelapse', '+12,4%', 'phút', source='Tương tác sâu', assessment='Chất lượng'),
        ]
        videos = deepcopy(YOUTUBE_VIDEOS)
        rows = [r for r in videos if start.isoformat() <= r['date'] <= end.isoformat() and _fold(query) in _fold(r['title'])]
        steps = [('views','Lượt xem video','Khán giả tiếp cận nội dung'), ('clicks','Click CTA mô tả','Nhấp vào link đặt lịch'), ('visits','Truy cập website','Đích đến landing page'), ('leads','Leads khám bệnh','Đăng ký tư vấn / dịch vụ'), ('appointments','Lịch hẹn thực tế','Đến khám tại phòng khám')]
        funnel = [dict(label=label, value=totals[key], percent=100 if i == 0 else _ratio(totals[key], totals[steps[i-1][0]]), description=desc, color=['blue','blue','blue','purple','pink'][i]) for i, (key,label,desc) in enumerate(steps)]
        chart_keys, chart_labels = ['views', 'previous_views'], ['Kỳ hiện tại', 'Kỳ trước']
        chart_totals = [totals['views'], round(totals['views'] / 1.215)]
    if sort != 'default':
        rows.sort(key=lambda row: row[sort], reverse=True)
    dates = [(start + timedelta(days=i)).isoformat() for i in range(days)]
    weights = [1.0 + .65 * i / max(1, days - 1) + .23 * math.sin(i / max(1, days - 1) * math.pi * (4 if channel == 'tiktok' else 3)) for i in range(days)]
    chart = dict(dates=dates, keys=chart_keys, labels=chart_labels, series=[_allocate(total, weights if i == 0 else [w * (1 + .1 * math.cos(j)) for j,w in enumerate(weights)]) for i,total in enumerate(chart_totals)])
    if channel == 'youtube':
        chart['watch_series'] = [_allocate(totals['watch_hours'], weights), _allocate(round(totals['watch_hours'] / 1.182), weights)]
    return dict(channel=channel, data_source='mock', period=period, filters=dict(query=query, status=status, sort=sort),
                metrics=metrics, totals=totals, rows=rows, videos=videos, funnel=funnel, chart=chart,
                notice='Dữ liệu mẫu theo thiết kế KinderHealth · Chưa kết nối API hoặc CRM. Kỳ khác được mô phỏng; video tiêu biểu là các mẫu độc lập.')
