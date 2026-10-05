import json
from argparse import Namespace

from .common import Result, cli, meta_get, normalize_ad_account, pass_result, require_env

SERVICE = 'Facebook Ads'
REQUIRED = ('META_API_VERSION', 'META_ACCESS_TOKEN', 'META_AD_ACCOUNT_ID')
FIELDS = ('account_id', 'account_name', 'campaign_id', 'campaign_name', 'impressions', 'reach', 'clicks', 'spend', 'ctr', 'cpc', 'cpm', 'frequency', 'actions')
CANDIDATES = ('lead', 'contact', 'form', 'schedule', 'appointment', 'messaging', 'conversion')


def check(args: Namespace) -> Result:
    account = normalize_ad_account(require_env('META_AD_ACCOUNT_ID'))
    _, body = meta_get(f'{account}/insights', require_env('META_ACCESS_TOKEN'), {
        'level': 'campaign', 'fields': ','.join(FIELDS), 'limit': args.limit,
        'time_range': json.dumps({'since': args.start, 'until': args.end}),
    })
    campaigns = []
    for row in body.get('data', []):
        item = {key: row.get(key, 'N/A') for key in FIELDS if key != 'actions'}
        actions = [{'action_type': action.get('action_type', 'N/A'), 'value': action.get('value', 'N/A')} for action in row.get('actions', [])]
        item['Actions'] = actions
        item['POSSIBLE CONVERSION ACTIONS'] = [action for action in actions if any(word in action['action_type'].lower() for word in CANDIDATES)]
        campaigns.append(item)
    return pass_result(SERVICE, {'Ad Account': account, 'Period': f'{args.start} → {args.end}', 'Campaigns': campaigns,
                               'More available': bool(body.get('paging', {}).get('next')), 'Currency': 'Đơn vị tiền tệ của ad account; không mặc định VND.'},
        ('API truy cập thành công nhưng kỳ được chọn không có dữ liệu.\n' if not campaigns else '') +
        'These are candidates only. KinderHealth must define which action\ncounts as a business Lead.')


def main() -> None:
    cli(SERVICE, 'META ADS REAL DATA TEST', REQUIRED, check, dates=True)


if __name__ == '__main__':
    main()
