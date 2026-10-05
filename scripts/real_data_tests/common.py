from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Callable, TypedDict
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
TIMEOUT = 30.0
GOOGLE_ENV = ('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GOOGLE_REFRESH_TOKEN')
_secrets: set[str] = set()
_sensitive = re.compile(r'token|secret|authorization|password|api[_-]?key', re.I)


class Result(TypedDict):
    service: str
    success: bool
    status: str
    status_code: int | None
    message: str
    details: dict[str, Any]


class APIError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(redact(message))
        self.status_code = status_code


def register_secret(value: str) -> str:
    if value:
        _secrets.add(value)
    return value


def load_environment() -> None:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    load_dotenv(ROOT / '.env', override=False)
    for name, value in os.environ.items():
        if _sensitive.search(name):
            register_secret(value)


def optional_env(name: str) -> str | None:
    value = os.environ.get(name, '').strip()
    if value and _sensitive.search(name):
        register_secret(value)
    return value or None


def require_env(name: str) -> str:
    value = optional_env(name)
    if value is None:
        raise RuntimeError(f'Thiếu {name} trong .env')
    return value


def mask_secret(secret: str) -> str:
    return secret[:6] + '...' + secret[-4:] if len(secret) > 10 else '[REDACTED]'


def redact(value: str, *, keep_urls: bool = False) -> str:
    for secret in sorted(_secrets, key=len, reverse=True):
        value = value.replace(secret, '[REDACTED]').replace(quote(secret, safe=''), '[REDACTED]')
    def clean_url(match: re.Match[str]) -> str:
        if not keep_urls:
            return '[URL omitted]'
        try:
            url = urlsplit(match.group())
            # Preserve usable post links, never userinfo, arbitrary queries or fragments.
            query = urlencode([(k, v) for k, v in parse_qsl(url.query) if k in ('id', 'story_fbid') and v.isdecimal()])
            return urlunsplit((url.scheme, url.hostname or '', url.path, query, ''))
        except ValueError:
            return '[URL omitted]'
    value = re.sub(r'https?://[^\s<>"\']+', clean_url, value)
    value = re.sub(r'(?i)Bearer\s+\S+', 'Bearer [REDACTED]', value)
    value = re.sub(r'(?i)((?:[\w-]*(?:token|secret|password|api_key)[\w-]*)\s*[=:]\s*)[^\s,;]+', r'\1[REDACTED]', value)
    return re.sub(r'[\x00-\x08\x0b-\x1f\x7f]', '', value)


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {redact(str(k)): '[REDACTED]' if _sensitive.search(str(k)) else sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    return redact(value, keep_urls=True) if isinstance(value, str) else value


def safe_json_print(value: Any) -> None:
    print(json.dumps(sanitize(value), ensure_ascii=False, indent=2))


def section(title: str) -> None:
    print('\n' + '=' * 48 + '\n' + redact(title) + '\n' + '=' * 48)


def format_error_response(status: int, payload: dict[str, Any]) -> str:
    error = payload.get('error', payload)
    if isinstance(error, dict):
        code = error.get('code', error.get('status', 'unknown'))
        message = error.get('message', error.get('error_description', 'API từ chối request'))
    else:
        code, message = error, payload.get('error_description', 'OAuth error')
    hint = {
        401: 'Kiểm tra token, thời hạn và authentication.',
        403: 'Kiểm tra quyền tài khoản, quyền property và OAuth scope/API đã bật.',
        404: 'Kiểm tra ID và property URL có trùng chính xác nguồn thật không.',
    }.get(status, 'Kiểm tra quyền, phiên bản API và các field được hỗ trợ.')
    return redact(f'HTTP {status}; code={code}; {message}. {hint}')


def request_json(method: str, url: str, **kwargs: Any) -> tuple[int, dict[str, Any]]:
    try:
        response = httpx.request(method, url, timeout=TIMEOUT, follow_redirects=False, **kwargs)
    except httpx.RequestError:
        raise APIError('Không kết nối được API (timeout/DNS/TLS/network). URL và credential được ẩn.') from None
    try:
        payload = response.json()
    except ValueError:
        raise APIError('API trả nội dung không phải JSON; không in response thô.', response.status_code) from None
    if not isinstance(payload, dict):
        raise APIError('API trả cấu trúc JSON không hợp lệ.', response.status_code)
    # Register any returned credentials before formatting even an error envelope.
    def remember(node: Any) -> None:
        if isinstance(node, dict):
            for key, val in node.items():
                if _sensitive.search(key) and isinstance(val, str):
                    register_secret(val)
                else:
                    remember(val)
        elif isinstance(node, list):
            for val in node:
                remember(val)
    remember(payload)
    if response.status_code != 200 or 'error' in payload:
        raise APIError(format_error_response(response.status_code, payload), response.status_code)
    return response.status_code, payload


def bearer(token: str) -> dict[str, str]:
    return {'Authorization': 'Bearer ' + register_secret(token)}


def numeric_id(value: str) -> str:
    if not re.fullmatch(r'[0-9]+', value):
        raise APIError('ID phải chỉ gồm chữ số; không dùng URL hoặc tên tài khoản.')
    return value


def normalize_ad_account(value: str) -> str:
    return 'act_' + numeric_id(value.removeprefix('act_'))


def meta_get(path: str, token: str, params: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    version = require_env('META_API_VERSION')
    if not re.fullmatch(r'v[0-9]+\.[0-9]+', version):
        raise APIError('META_API_VERSION cần dạng vNN.N theo phiên bản được hỗ trợ của Meta app.')
    return request_json('GET', f'https://graph.facebook.com/{version}/{path}', headers=bearer(token), params=params)


def meta_discover(path: str, fields: str) -> tuple[list[dict[str, Any]], bool]:
    params: dict[str, Any] = {'fields': fields, 'limit': 100}
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for _ in range(10):
        _, body = meta_get(path, require_env('META_ACCESS_TOKEN'), params)
        rows.extend(body.get('data', []))
        paging = body.get('paging', {})
        if not paging.get('next'):
            return rows, False
        cursor = paging.get('cursors', {}).get('after')
        if not cursor or cursor in seen:
            return rows, True
        seen.add(cursor)
        params['after'] = cursor
    return rows, True


def parser(title: str, *, dates: bool = False, limit: int = 10, page: bool = False) -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=title)
    def positive(value: str) -> int:
        try:
            number = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError('limit phải là số nguyên') from None
        if not 1 <= number <= 100:
            raise argparse.ArgumentTypeError('limit phải trong khoảng 1–100')
        return number
    result.add_argument('--limit', type=positive, default=limit)
    if dates:
        def iso(value: str) -> str:
            try:
                if date.fromisoformat(value).isoformat() != value:
                    raise ValueError
            except ValueError:
                raise argparse.ArgumentTypeError('Ngày phải theo YYYY-MM-DD') from None
            return value
        result.add_argument('--start', type=iso, default='2026-09-01')
        result.add_argument('--end', type=iso, default='2026-09-30')
    if page:
        result.add_argument('--page-id')
    return result


def pass_result(service: str, details: dict[str, Any], message: str = 'API truy cập thành công.') -> Result:
    return Result(service=service, success=True, status='PASS', status_code=200, message=message, details=details)


def execute(service: str, required: tuple[str, ...], check: Callable[[argparse.Namespace], Result], args: argparse.Namespace) -> Result:
    missing = [name for name in required if not optional_env(name)]
    if missing:
        message = 'Thiếu cấu hình: ' + ', '.join(missing)
        if 'META_AD_ACCOUNT_ID' in missing:
            message += '. Chạy test_meta_ad_accounts trước.'
        return Result(service=service, success=False, status='SKIP', status_code=None, message=message, details={})
    try:
        return check(args)
    except APIError as exc:
        return Result(service=service, success=False, status='FAIL', status_code=exc.status_code, message=redact(str(exc)), details={})
    except Exception:
        # Never expose a raw exception: libraries can include URLs and credentials.
        return Result(service=service, success=False, status='FAIL', status_code=None, message='Lỗi cấu hình hoặc cấu trúc response không hợp lệ; chi tiết thô được ẩn để bảo vệ credential.', details={})


def print_result(result: Result) -> None:
    print(f"STATUS: {result['status_code'] if result['status_code'] is not None else 'N/A'}\nRESULT: {result['status']}")
    print(redact(result['message']))
    def render(value: Any, indent: str = '') -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                label = 'Page Access Token (masked)' if key == 'Masked credential' else key
                if isinstance(item, (dict, list)):
                    print(f'{indent}{label}:')
                    if key in ('Daily report', 'Top channel groups') and item:
                        columns = list(item[0])
                        print(indent + '  ' + ' | '.join(columns))
                        for row in item:
                            print(indent + '  ' + ' | '.join(str(row.get(col, 'N/A')) for col in columns))
                    else:
                        render(item, indent + '  ')
                else:
                    print(f'{indent}{label}: {item if item is not None else "N/A"}')
        elif isinstance(value, list):
            if not value:
                print(indent + '(empty)')
            for index, item in enumerate(value, 1):
                print(f'{indent}{index}.')
                render(item, indent + '  ')
        else:
            print(indent + str(value))
    render(sanitize(result['details']))


def cli(service: str, title: str, required: tuple[str, ...], check: Callable[[argparse.Namespace], Result], *, dates: bool = False, page: bool = False, limit: int = 10) -> None:
    arg_parser = parser(title, dates=dates, page=page, limit=limit)
    args = arg_parser.parse_args()
    if dates and args.start > args.end:
        arg_parser.error('--start phải nhỏ hơn hoặc bằng --end')
    load_environment()
    if page and args.page_id:
        required = tuple(name for name in required if name != 'META_PAGE_ID')
    section(title)
    result = execute(service, required, check, args)
    print_result(result)
    raise SystemExit(1 if result['status'] == 'FAIL' else 2 if result['status'] == 'SKIP' else 0)
