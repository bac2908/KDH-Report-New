from typing import Any, Dict
from typing import Literal
import csv
from datetime import date
from io import StringIO

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.services.reports import ReportService

router = APIRouter(prefix="/api/v1", tags=["reports"])
service = ReportService()


@router.get("/reports/overview")
def get_overview(start: date | None = None, end: date | None = None):
    try:
        return service.get_overview(start, end)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/reports/overview/export")
def export_overview(start: date | None = None, end: date | None = None):
    data = get_overview(start, end)
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["KDH Traffic Report", "Dữ liệu mẫu KinderHealth"])
    writer.writerow(["Từ ngày", data["period"]["start"], "Đến ngày", data["period"]["end"]])
    writer.writerow([])
    writer.writerow(["Chỉ số", "Giá trị", "Đơn vị", "Thay đổi (%)"])
    for metric in data["metrics"]:
        writer.writerow([metric["label"], metric["value"], metric["unit"], metric["delta"]])
    writer.writerow([])
    writer.writerow(["Kênh", "Leads đóng góp"])
    mix = data["charts"]["channel_mix"]
    writer.writerows(zip(mix["labels"], mix["values"]))
    writer.writerow([])
    writer.writerow(["Ngày", "Lưu lượng", "Lưu lượng kỳ trước"])
    trend = data["charts"]["trends"]["traffic"]
    writer.writerows(zip(trend["dates"], trend["values"], trend["previous"]))
    filename = f"KDH-Tong-quan-{data['period']['start']}-{data['period']['end']}.csv"
    return Response(content="\ufeff" + output.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/reports/seo")
def get_seo(start: date | None = None, end: date | None = None, period: str | None = None, channel: str | None = None):
    filters = {key: value for key, value in {"period": period, "channel": channel}.items() if value}
    try:
        return service.get_seo(start, end, filters)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/reports/seo/export")
def export_seo(start: date | None = None, end: date | None = None,
               rank: Literal['all', 'top3', 'top10', 'new', 'risers'] = 'all', query: str = ''):
    from app.integrations.mock.seo import filter_keywords

    data = get_seo(start, end)
    output = StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['KDH Traffic Report', 'SEO & Lưu lượng Website', 'Dữ liệu mẫu'])
    writer.writerow(['Từ ngày', data['period']['start'], 'Đến ngày', data['period']['end']])
    writer.writerow([])
    writer.writerow(['Chỉ số', 'Giá trị', 'Đơn vị'])
    for metric in data['metrics']:
        writer.writerow([metric['label'], metric['value'], metric['unit']])
    writer.writerow([])
    writer.writerow(['Từ khóa', 'Trang đích', 'Vị trí cũ', 'Vị trí mới', 'Thay đổi', 'Clicks', 'Hiển thị', 'CTR'])
    for row in filter_keywords(data['keywords'], rank, query):
        writer.writerow([row['keyword'], row['landing'], row['previous'], row['position'], row['previous'] - row['position'], row['clicks'], row['impressions'], row['ctr']])
    writer.writerow([])
    writer.writerow(['Trang đích', 'Users', 'Clicks', 'Leads', 'CR'])
    for row in data['landings']:
        writer.writerow([row['url'], row['users'], row['clicks'], row['leads'], row['cr']])
    filename = f"KDH-SEO-{data['period']['start']}-{data['period']['end']}.csv"
    return Response(content='\ufeff' + output.getvalue(), media_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="{filename}"'})


@router.get("/reports/facebook-ads")
@router.get("/reports/ads")
def get_facebook_ads(start: date | None = None, end: date | None = None,
                     query: str = Query(default='', max_length=200),
                     status: Literal['all', 'active', 'attention'] = 'all',
                     campaign: str = 'all', sort: Literal['cpl_asc', 'cpl_desc', 'spend_desc', 'leads_desc'] = 'cpl_asc'):
    from app.presentation import facebook_ads_fragments
    try:
        data = service.get_facebook_ads(start=start, end=end, query=query, status=status, campaign=campaign, sort=sort)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {**data, 'fragments': facebook_ads_fragments(data)}


@router.get("/reports/facebook-ads/export")
def export_facebook_ads(start: date | None = None, end: date | None = None,
                        query: str = Query(default='', max_length=200),
                        status: Literal['all', 'active', 'attention'] = 'all', campaign: str = 'all',
                        sort: Literal['cpl_asc', 'cpl_desc', 'spend_desc', 'leads_desc'] = 'cpl_asc', compare: bool = True):
    data = get_facebook_ads(start, end, query, status, campaign, sort)
    output = StringIO(newline='')
    writer = csv.writer(output)
    # User-supplied filter text must remain text when the CSV is opened in Excel.
    safe_query = "'" + query if query.lstrip().startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else query
    writer.writerow(['KDH Traffic Report', 'Facebook Ads', 'Dữ liệu mẫu — chưa kết nối Meta'])
    writer.writerow(['Từ ngày', data['period']['start'], 'Đến ngày', data['period']['end']])
    writer.writerow(['Chiến dịch', campaign, 'Trạng thái', status, 'Tìm kiếm', safe_query, 'Sắp xếp', sort])
    writer.writerow([])
    writer.writerow(['Chỉ số', 'Giá trị'] + (['Kỳ trước', 'Thay đổi (%)'] if compare else []))
    for metric in data['metrics']:
        writer.writerow([metric['label'], metric['value']] + ([data['previous'][metric['key']], metric['delta']] if compare else []))
    writer.writerow([])
    writer.writerow(['CTR = Clicks / Impressions', data['totals']['ctr'], '%'])
    writer.writerow(['CPC = Chi tiêu / Clicks', data['totals']['cpc'], 'VND'])
    writer.writerow(['CPA = Chi tiêu / Lịch hẹn', data['totals']['cpa'], 'VND'])
    writer.writerow([])
    writer.writerow(['Chiến dịch', 'ID', 'Trạng thái', 'Chi tiêu (VND)', 'Ngân sách (VND)', 'Reach', 'Impressions', 'Clicks', 'CTR (%)', 'Leads', 'CPL (VND)', 'Lịch hẹn'])
    for row in data['campaigns']:
        writer.writerow([row['name'], row['id'], row['status_label'], row['spend'], row['budget'], row['reach'], row['impressions'], row['clicks'], row['ctr'], row['leads'], row['cpl'], row['appointments']])
    writer.writerow([])
    writer.writerow(['Mẫu quảng cáo nổi bật (không phải toàn bộ quảng cáo)', 'Chiến dịch', 'Chi tiêu (VND)', 'Impressions', 'Clicks', 'Leads', 'CTR (%)', 'CPL (VND)'])
    for row in data['creatives']:
        writer.writerow([row['name'], row['campaign_id'], row['spend'], row['impressions'], row['clicks'], row['leads'], row['ctr'], row['cpl']])
    writer.writerow([])
    writer.writerow(['Vị trí hiển thị', 'Chi tiêu (VND)', 'Tỷ trọng (%)'])
    for row in data['placements']:
        writer.writerow([row['name'], row['spend'], row['percent']])
    filename = f"KDH-Facebook-Ads-{data['period']['start']}-{data['period']['end']}.csv"
    return Response(content='\ufeff' + output.getvalue(), media_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="{filename}"'})


@router.get("/reports/{report_type}")
def get_report(report_type: str, period: str | None = Query(default=None), channel: str | None = Query(default=None)):
    filters: Dict[str, Any] = {}
    if period:
        filters["period"] = period
    if channel:
        filters["channel"] = channel
    return service.get_report(report_type, filters)
