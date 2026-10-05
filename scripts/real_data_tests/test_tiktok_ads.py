import json
from argparse import Namespace

from .common import Result, cli, format_error_response, numeric_id, pass_result, request_json, require_env

BASE_URL = 'https://business-api.tiktok.com/open_api/v1.3'
SERVICE = 'TikTok Ads'
REQUIRED = ('TIKTOK_ACCESS_TOKEN', 'TIKTOK_ADVERTISER_ID')


def check(args: Namespace) -> Result:
    status, body = request_json('GET', f'{BASE_URL}/report/integrated/get/',
        headers={'Access-Token': require_env('TIKTOK_ACCESS_TOKEN')}, params={
            'advertiser_id': numeric_id(require_env('TIKTOK_ADVERTISER_ID')), 'report_type': 'BASIC',
            'data_level': 'AUCTION_ADVERTISER', 'dimensions': json.dumps(['advertiser_id', 'stat_time_day']),
            'metrics': json.dumps(['spend', 'impressions', 'clicks', 'ctr', 'cpc']),
            'start_date': args.start, 'end_date': args.end, 'page': 1, 'page_size': args.limit,
        })
    if body.get('code') != 0:
        return Result(service=SERVICE, success=False, status='FAIL', status_code=status,
                      message=format_error_response(status, body),
                      details={'HTTP STATUS': status, 'TikTok response code': body.get('code', 'N/A')})
    data = body.get('data') or {}
    rows = [{'Date': row.get('dimensions', {}).get('stat_time_day', 'N/A'),
             **{key: row.get('metrics', {}).get(key, 'N/A') for key in ('spend', 'impressions', 'clicks', 'ctr', 'cpc')}} for row in data.get('list', [])]
    return pass_result(SERVICE, {'HTTP STATUS': status, 'TikTok response code': body['code'], 'Period': f'{args.start} → {args.end}',
                               'Daily report': rows, 'Pagination': data.get('page_info', {})},
                       'API truy cập thành công.' if rows else 'API truy cập thành công nhưng kỳ được chọn không có dữ liệu.')


def main() -> None:
    cli(SERVICE, 'TIKTOK ADS REAL DATA TEST', REQUIRED, check, dates=True)


if __name__ == '__main__':
    main()
