from argparse import Namespace

from .common import Result, cli, meta_discover, pass_result

SERVICE = 'Meta Ad Accounts'
REQUIRED = ('META_API_VERSION', 'META_ACCESS_TOKEN')


def check(args: Namespace) -> Result:
    accounts, truncated = meta_discover('me/adaccounts', 'id,account_id,name,account_status,currency,timezone_name')
    fields = ('id', 'account_id', 'name', 'account_status', 'currency', 'timezone_name')
    return pass_result(SERVICE, {'Ad accounts': [{field: account.get(field, 'N/A') for field in fields} for account in accounts], 'Pagination truncated': truncated},
        ('Không có ad account được trả về. ' if not accounts else '') +
        'Choose the Ad Account that actually runs KinderHealth campaigns\nand set META_AD_ACCOUNT_ID in .env.')


def main() -> None:
    cli(SERVICE, 'META AD ACCOUNT DISCOVERY', REQUIRED, check)


if __name__ == '__main__':
    main()
