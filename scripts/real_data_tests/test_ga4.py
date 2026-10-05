from argparse import Namespace
from typing import Any

from .common import APIError, GOOGLE_ENV, Result, bearer, cli, numeric_id, pass_result, request_json, require_env
from .google_auth import get_google_access_token

SERVICE = 'Google Analytics 4'
REQUIRED = GOOGLE_ENV + ('GA4_PROPERTY_ID',)


def rows(body: dict[str, Any], dimension: str, metrics: list[str]) -> list[dict[str, str]]:
    return [{dimension: row['dimensionValues'][0]['value'], **dict(zip(metrics, [v['value'] for v in row['metricValues']]))} for row in body.get('rows', [])]


def check(args: Namespace) -> Result:
    prop = numeric_id(require_env('GA4_PROPERTY_ID').removeprefix('properties/'))
    headers = bearer(get_google_access_token())
    url = f'https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport'
    def report(dimension: str, metrics: list[str]) -> dict[str, Any]:
        _, data = request_json('POST', url, headers=headers, json={
            'dateRanges': [{'startDate': args.start, 'endDate': args.end}],
            'dimensions': [{'name': dimension}], 'metrics': [{'name': metric} for metric in metrics],
            'limit': str(args.limit),
            'orderBys': [{'dimension': {'dimensionName': 'date'}}] if dimension == 'date' else [{'metric': {'metricName': 'sessions'}, 'desc': True}],
        })
        return data
    metrics = ['activeUsers', 'sessions', 'screenPageViews', 'eventCount']
    details: dict[str, Any] = {'GA4 Property': prop, 'Period': f'{args.start} → {args.end}', 'Daily report': rows(report('date', metrics), 'Date', metrics)}
    try:
        channels = ['activeUsers', 'sessions']
        details['Top channel groups'] = rows(report('sessionDefaultChannelGroup', channels), 'Channel', channels)
    except APIError as exc:
        details['Channel warning'] = str(exc)
    except (KeyError, TypeError, IndexError):
        details['Channel warning'] = 'Response channel không đúng cấu trúc; report theo ngày vẫn thành công.'
    message = 'GA4 connection OK. Lead/Booking event has not been configured or identified yet.'
    if not details['Daily report']:
        message += ' API truy cập thành công nhưng kỳ được chọn không có dữ liệu.'
    return pass_result(SERVICE, details, message)


def main() -> None:
    cli(SERVICE, 'GOOGLE ANALYTICS 4 REAL DATA TEST', REQUIRED, check, dates=True)


if __name__ == '__main__':
    main()
