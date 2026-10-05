from datetime import date, datetime, timezone


DEFAULT_START = date(2026, 9, 1)
DEFAULT_END = date(2026, 9, 30)


BASE_METRICS = {
    "total_posts": 48,
    "reach": 318_400,
    "engagement": 34_190,
    "followers_new": 850,
    "link_clicks": 4_120,
}


FORMATS = [
    {
        "key": "reels",
        "label": "Reels ngắn (30-45s)",
        "count": 18,
        "avg_reach": 14_200,
        "er": 14.2,
    },
    {
        "key": "long_video",
        "label": "Video chuyên gia dài",
        "count": 8,
        "avg_reach": 9_800,
        "er": 9.5,
    },
    {
        "key": "carousel",
        "label": "Carousel (Ảnh ghép/Infographic)",
        "count": 14,
        "avg_reach": 6_500,
        "er": 8.8,
    },
    {
        "key": "photo",
        "label": "Photo đơn / Album",
        "count": 8,
        "avg_reach": 3_400,
        "er": 5.1,
    },
]


TOPICS = [
    {
        "key": "pediatric",
        "label": "Kiến thức sức khỏe nhi khoa",
        "count": 18,
        "reach": 142_500,
        "er": 12.4,
        "description": (
            "Chủ đề thu hút nhiều câu hỏi tư vấn "
            "trực tiếp từ phụ huynh nhất."
        ),
    },
    {
        "key": "nutrition",
        "label": "Dinh dưỡng trẻ em",
        "count": 12,
        "reach": 98_200,
        "er": 11.1,
        "description": (
            "Dẫn đầu về lượt chia sẻ nhờ nội dung "
            "trực quan, dễ ứng dụng."
        ),
    },
    {
        "key": "vaccination",
        "label": "Tiêm chủng trọn gói",
        "count": 10,
        "reach": 54_100,
        "er": 8.4,
        "description": (
            "Tạo ra lượng click đặt lịch khám "
            "và tương tác inbox cao."
        ),
    },
    {
        "key": "review",
        "label": "Câu chuyện khách hàng & Review",
        "count": 8,
        "reach": 23_600,
        "er": 7.9,
        "description": (
            "Xây dựng niềm tin thương hiệu "
            "và uy tín phòng khám."
        ),
    },
]
TOP_POSTS = [
    {
        "id": "post-001",
        "title": (
            "Bác sĩ hướng dẫn xử lý sốt tại nhà "
            "cho trẻ đúng cách"
        ),
        "topic": "Sức khỏe nhi khoa",
        "topic_key": "pediatric",
        "date": "2026-09-12",
        "format": "Reels (35s)",
        "format_key": "reels",
        "reach": 45_200,
        "engagement": 5_810,
        "comments": 340,
        "shares": 890,
        "clicks": 412,
    },
    {
        "id": "post-002",
        "title": (
            "Top 4 lưu ý quan trọng khi tiêm "
            "vaccine 6 trong 1"
        ),
        "topic": "Tiêm chủng trọn gói",
        "topic_key": "vaccination",
        "date": "2026-09-18",
        "format": "Carousel",
        "format_key": "carousel",
        "reach": 32_800,
        "engagement": 4_120,
        "comments": 215,
        "shares": 650,
        "clicks": 580,
    },
    {
        "id": "post-003",
        "title": (
            "Review phòng khám nhi khoa chuẩn "
            "5 sao KinderHealth"
        ),
        "topic": "Review khách hàng",
        "topic_key": "review",
        "date": "2026-09-22",
        "format": "Video dài",
        "format_key": "long_video",
        "reach": 28_400,
        "engagement": 3_100,
        "comments": 180,
        "shares": 410,
        "clicks": 320,
    },
    {
        "id": "post-004",
        "title": (
            "Thực đơn dinh dưỡng tăng sức "
            "đề kháng cho bé từ 1-3 tuổi"
        ),
        "topic": "Dinh dưỡng trẻ em",
        "topic_key": "nutrition",
        "date": "2026-09-25",
        "format": "Carousel",
        "format_key": "carousel",
        "reach": 24_100,
        "engagement": 2_950,
        "comments": 145,
        "shares": 720,
        "clicks": 290,
    },
    {
        "id": "post-005",
        "title": (
            "Hỏi đáp trực tuyến: Giải đáp mọi "
            "thắc mắc về lịch tiêm chủng"
        ),
        "topic": "Tiêm chủng trọn gói",
        "topic_key": "vaccination",
        "date": "2026-09-28",
        "format": "Livestream",
        "format_key": "livestream",
        "reach": 19_500,
        "engagement": 2_410,
        "comments": 520,
        "shares": 190,
        "clicks": 410,
    },
]
ENGAGEMENT_BREAKDOWN = [
    {
        "key": "reactions",
        "label": "Thả cảm xúc (Reactions)",
        "value": 22_450,
    },
    {
        "key": "comments",
        "label": "Bình luận tư vấn (Comments)",
        "value": 4_820,
    },
    {
        "key": "shares",
        "label": "Chia sẻ lan tỏa (Shares)",
        "value": 2_800,
    },
    {
        "key": "link_clicks",
        "label": "Click liên kết / Đặt lịch",
        "value": 4_120,
    },
]
def calculate_percent(value, total):
    if not total:
        return 0

    return round(value / total * 100, 1)


def enrich_post(post):
    item = dict(post)

    item["er"] = (
        round(
            item["engagement"]
            / item["reach"]
            * 100,
            1,
        )
        if item["reach"]
        else 0
    )

    return item
def facebook_content_payload(start=None, end=None, query='', content_format='all', topic='all', sort='all'):
    from datetime import timedelta
    from app.integrations.mock.overview import validate_range
    import unicodedata

    start, end = start or DEFAULT_START, end or DEFAULT_END
    validate_range(start, end)
    if content_format not in ['all', 'livestream'] + [r['key'] for r in FORMATS]:
        raise ValueError('Định dạng không hợp lệ.')
    if topic not in ['all'] + [r['key'] for r in TOPICS]:
        raise ValueError('Chủ đề không hợp lệ.')
    sorts = dict(all=None, reach_desc='reach', engagement_desc='engagement', shares_desc='shares', clicks_desc='clicks')
    if sort not in sorts:
        raise ValueError('Thứ tự không hợp lệ.')
    days = (end - start).days + 1
    ratio = days / 30
    scale = lambda value: int(value * ratio + .5)
    def normalize(value):
        return ''.join(c for c in unicodedata.normalize('NFD', value.casefold().replace('đ', 'd')) if not unicodedata.combining(c))
    def allocate(values, total):
        raw = [v / sum(values) * total for v in values]
        result = [int(v) for v in raw]
        for i in sorted(range(len(values)), key=lambda i: raw[i] - result[i], reverse=True)[:total-sum(result)]:
            result[i] += 1
        return result

    metrics = {key: scale(value) for key, value in BASE_METRICS.items()}
    metrics['engagement_rate'] = round(metrics['engagement'] / metrics['reach'] * 100, 2)
    metrics['ctr'] = round(metrics['link_clicks'] / metrics['reach'] * 100, 2)
    previous = dict(total_posts=scale(44), reach=scale(276389), engagement=scale(31338), followers_new=scale(717), link_clicks=scale(3900))
    previous['engagement_rate'] = round(previous['engagement'] / previous['reach'] * 100, 2)
    deltas = {key: round((metrics[key] / value - 1) * 100, 2) if value else None for key, value in previous.items()}
    posts = [enrich_post(p) for p in TOP_POSTS if start <= date.fromisoformat(p['date']) <= end]
    posts = [p for p in posts if normalize(query.strip()) in normalize(p['title'] + ' ' + p['topic'])
             and (content_format == 'all' or p['format_key'] == content_format)
             and (topic == 'all' or p['topic_key'] == topic)]
    if sorts[sort]:
        posts.sort(key=lambda p: p[sorts[sort]], reverse=True)
    formats = []
    for row, count in zip(FORMATS, allocate([r['count'] for r in FORMATS], metrics['total_posts'])):
        formats.append({**row, 'count': count, 'percent': calculate_percent(count, metrics['total_posts'])})
    topics = [{**row, 'count': count, 'reach': reach} for row, count, reach in zip(
        TOPICS, allocate([r['count'] for r in TOPICS], metrics['total_posts']),
        allocate([r['reach'] for r in TOPICS], metrics['reach']))]
    counts = allocate([r['value'] for r in ENGAGEMENT_BREAKDOWN[:3]], metrics['engagement'] - metrics['link_clicks']) + [metrics['link_clicks']]
    breakdown = [{**row, 'value': value, 'percent': calculate_percent(value, metrics['engagement'])} for row, value in zip(ENGAGEMENT_BREAKDOWN, counts)]
    organic = scale(212500)
    paid = metrics['reach'] - organic
    return dict(
        report_type='facebook-content', data_source='mock', generated_at=datetime.now(timezone.utc).isoformat(),
        period=dict(start=start.isoformat(), end=end.isoformat(), days=days,
                    previous_start=(start-timedelta(days=days)).isoformat(), previous_end=(start-timedelta(days=1)).isoformat()),
        metrics=metrics, previous=previous, deltas=deltas, formats=formats, topics=topics, posts=posts,
        sample_count=len(TOP_POSTS), engagement_breakdown=breakdown,
        reach_mix=dict(organic=organic, paid=paid, organic_percent=calculate_percent(organic, metrics['reach']), paid_percent=calculate_percent(paid, metrics['reach'])),
        insights=dict(
            highlights=['Reels tư vấn của Bác sĩ là định dạng nổi bật trong mẫu thiết kế, với mức tăng trưởng reach tham chiếu +42%.', 'Các bài viết dinh dưỡng có nội dung trực quan, dễ ứng dụng và được chia sẻ nhiều.'],
            warnings=['Mẫu thiết kế ghi nhận tương tác của bài viết dẫn link ngoài giảm nhẹ. Thử đặt liên kết trong bình luận ghim và so sánh kết quả trước khi áp dụng rộng.'],
            actions=['Tăng sản lượng Reels ngắn 30–45 giây từ Bác sĩ nhi khoa.', 'Đẩy mạnh minigame kiến thức dinh dưỡng để tăng chia sẻ.', 'Tối ưu CTA dẫn về landing page đặt lịch khám nhi.']),
        filters=dict(query=query.strip(), format=content_format, topic=topic, sort=sort),
        notice='Tổng quan theo dữ liệu mẫu 48 bài tháng 9/2026; các kỳ khác mô phỏng theo số ngày. Bảng chi tiết chỉ có 5 bài gốc, lọc theo ngày đăng thực tế trong mẫu. Bộ lọc nội dung chỉ áp dụng cho bảng bài viết.',
    )
