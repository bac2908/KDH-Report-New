from argparse import Namespace

from .common import Result, cli, mask_secret, meta_discover, pass_result

SERVICE = 'Meta Pages'
REQUIRED = ('META_API_VERSION', 'META_ACCESS_TOKEN')


def check(args: Namespace) -> Result:
    pages, truncated = meta_discover('me/accounts', 'id,name,access_token,tasks')
    rows = [{'Name': page.get('name'), 'Page ID': page.get('id'), 'Tasks': page.get('tasks', []),
             'Masked credential': mask_secret(page['access_token']) if page.get('access_token') else 'N/A'} for page in pages]
    return pass_result(SERVICE, {'Pages accessible': rows, 'Pagination truncated': truncated},
                       'Page access confirmed.' if pages else 'Meta token valid but no manageable Page was returned.')


def main() -> None:
    cli(SERVICE, 'META PAGE ACCESS TEST', REQUIRED, check)


if __name__ == '__main__':
    main()
