from argparse import Namespace

from .common import Result, cli, meta_get, numeric_id, pass_result, require_env, sanitize

SERVICE = 'Facebook Content'
REQUIRED = ('META_API_VERSION', 'META_PAGE_ID', 'META_PAGE_ACCESS_TOKEN')


def check(args: Namespace) -> Result:
    page = numeric_id(getattr(args, 'page_id', None) or require_env('META_PAGE_ID'))
    _, body = meta_get(f'{page}/posts', require_env('META_PAGE_ACCESS_TOKEN'), {
        'fields': 'id,message,created_time,permalink_url,shares,comments.limit(0).summary(true),reactions.limit(0).summary(true)',
        'limit': args.limit,
    })
    posts = [{'Post ID': p.get('id', 'N/A'), 'Date': p.get('created_time', 'N/A'),
              'Caption': sanitize(p.get('message') or 'N/A')[:160], 'URL': p.get('permalink_url', 'N/A'),
              'Reactions': (p.get('reactions') or {}).get('summary', {}).get('total_count', 'N/A'),
              'Comments': (p.get('comments') or {}).get('summary', {}).get('total_count', 'N/A'),
              'Shares': (p.get('shares') or {}).get('count', 'N/A')} for p in body.get('data', [])]
    return pass_result(SERVICE, {'Page ID': page, 'Posts': posts, 'More available': bool(body.get('paging', {}).get('next'))},
        'Basic Facebook Page content access confirmed.\nPost/Page insights should be implemented in the next integration phase.' +
        (' Không có bài đăng trong response.' if not posts else ''))


def main() -> None:
    cli(SERVICE, 'FACEBOOK CONTENT REAL DATA TEST', REQUIRED, check, page=True, limit=5)


if __name__ == '__main__':
    main()
