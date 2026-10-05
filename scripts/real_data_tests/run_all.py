from . import test_facebook_content, test_ga4, test_gsc, test_meta_ad_accounts, test_meta_ads, test_meta_pages, test_tiktok_ads
from .common import execute, load_environment, parser, print_result, section

CHECKS = (test_gsc, test_ga4, test_meta_pages, test_facebook_content, test_meta_ad_accounts, test_meta_ads, test_tiktok_ads)


def main() -> None:
    arg_parser = parser('KDH real data verification', dates=True)
    args = arg_parser.parse_args()
    if args.start > args.end:
        arg_parser.error('--start phải nhỏ hơn hoặc bằng --end')
    load_environment()
    results = []
    for module in CHECKS:
        section(module.SERVICE)
        result = execute(module.SERVICE, module.REQUIRED, module.check, args)
        results.append(result)
        print_result(result)
    section('KDH REAL DATA CONNECTION SUMMARY')
    for result in results:
        print(f"{result['service']:<26} {result['status']}")
    print(f"{'CRM / Booking':<26} NOT CONFIGURED")
    raise SystemExit(1 if any(r['status'] == 'FAIL' for r in results) else 2 if any(r['status'] == 'SKIP' for r in results) else 0)


if __name__ == '__main__':
    main()
