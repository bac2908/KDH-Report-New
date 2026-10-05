from argparse import Namespace
from urllib.parse import quote

from .common import GOOGLE_ENV, Result, bearer, cli, pass_result, request_json, require_env
from .google_auth import get_google_access_token

SERVICE = 'Google Search Console'
REQUIRED = GOOGLE_ENV + ('GSC_PROPERTY_URL',)


def check(args: Namespace) -> Result:
    prop = require_env('GSC_PROPERTY_URL')
    _, body = request_json('POST', f'https://www.googleapis.com/webmasters/v3/sites/{quote(prop, safe="")}/searchAnalytics/query',
        headers=bearer(get_google_access_token()), json={
            'startDate': args.start, 'endDate': args.end, 'dimensions': ['query'], 'type': 'web', 'rowLimit': args.limit,
        })
    rows = [{'Keyword': row.get('keys', ['N/A'])[0], 'Clicks': row.get('clicks'), 'Impressions': row.get('impressions'),
             'CTR (ratio 0–1)': row.get('ctr'), 'Average Position': row.get('position')} for row in body.get('rows', [])]
    return pass_result(SERVICE, {'Property': prop, 'Period': f'{args.start} → {args.end}', 'Top queries': rows},
                       'API truy cập thành công.' if rows else 'API truy cập thành công nhưng kỳ được chọn không có dữ liệu.')


def main() -> None:
    cli(SERVICE, 'GOOGLE SEARCH CONSOLE REAL DATA TEST', REQUIRED, check, dates=True)


if __name__ == '__main__':
    main()
