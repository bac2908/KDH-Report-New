"""Mock-backed TikTok/YouTube pages, JSON updates and CSV exports."""
import csv
from datetime import date
from io import StringIO
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response

from app.routes.pages import templates
from app.presentation import video_fragments
from app.services.reports import ReportService

router = APIRouter(tags=['video reports'])
Channel = Literal['tiktok', 'youtube']


def payload(channel: str, start: date | None = None, end: date | None = None, query: str = '', status: str = 'all', sort: str = 'default') -> dict:
    try:
        return ReportService().get_video(channel, start=start, end=end, query=query, status=status, sort=sort)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get('/report/tiktok-ads')
@router.get('/report/tiktok')
async def tiktok_page(request: Request):
    return templates.TemplateResponse(request=request, name='pages/tiktok/index.html', context={
        'title': 'TikTok Ads & Hiệu quả video', 'active_report': 'tiktok', 'video': payload('tiktok')})


@router.get('/report/youtube')
async def youtube_page(request: Request):
    return templates.TemplateResponse(request=request, name='pages/youtube/index.html', context={
        'title': 'YouTube & Hiệu quả video', 'active_report': 'youtube', 'video': payload('youtube')})


# A dedicated API prefix leaves the existing report routes unchanged.
@router.get('/api/v1/video-reports/{channel}')
def get_video(channel: Channel, start: date | None = None, end: date | None = None,
              query: str = Query('', max_length=200), status: str = 'all', sort: str = 'default'):
    data = payload(channel, start, end, query, status, sort)
    return {**data, 'fragments': video_fragments(data)}


def _cell(value: object) -> object:
    return "'" + value if isinstance(value, str) and (value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n'))) else value


@router.get('/api/v1/video-reports/{channel}/export')
def export_video(channel: Channel, start: date | None = None, end: date | None = None,
                 query: str = Query('', max_length=200), status: str = 'all', sort: str = 'default', compare: bool = True):
    data = payload(channel, start, end, query, status, sort)
    output = StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['KDH Traffic Report', channel, data['notice']])
    writer.writerow(['Từ ngày', data['period']['start'], 'Đến ngày', data['period']['end']])
    writer.writerow(['Tìm kiếm', _cell(query), 'Trạng thái', status, 'Sắp xếp', sort])
    writer.writerow(['Chỉ số', 'Giá trị', 'Đơn vị'] + (['Thay đổi so kỳ trước (mẫu)'] if compare else []))
    for metric in data['metrics']:
        writer.writerow([metric['label'], metric['value'], metric['unit']] + ([_cell(metric['delta'])] if compare else []))
    keys = ['id', 'title', 'spend', 'reach', 'views', 'clicks', 'ctr', 'leads', 'cpa', 'status_label'] if channel == 'tiktok' else ['id', 'title', 'date', 'views', 'duration', 'ctr', 'subscribers']
    writer.writerow([])
    writer.writerow(keys)
    writer.writerows([_cell(row[key]) for key in keys] for row in data['rows'])
    writer.writerow([])
    writer.writerow(['Ngày', *data['chart']['labels'][:2 if channel == 'tiktok' or compare else 1]])
    writer.writerows([day, *[series[i] for series in data['chart']['series'][:2 if channel == 'tiktok' or compare else 1]]] for i, day in enumerate(data['chart']['dates']))
    if channel == 'youtube':
        writer.writerow([])
        writer.writerow(['Ngày', 'Thời gian xem (giờ)'] + (['Kỳ trước (giờ)'] if compare else []))
        writer.writerows([day, data['chart']['watch_series'][0][i]] + ([data['chart']['watch_series'][1][i]] if compare else []) for i, day in enumerate(data['chart']['dates']))
    writer.writerow([])
    writer.writerow(['Phễu mẫu', 'Số lượt'])
    writer.writerows([step['label'], step['value']] for step in data['funnel'])
    name = f"KDH-{channel}-{data['period']['start']}-{data['period']['end']}.csv"
    return Response('\ufeff' + output.getvalue(), media_type='text/csv; charset=utf-8', headers={'Content-Disposition': f'attachment; filename="{name}"'})
