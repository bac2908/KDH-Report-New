"""Offline, pure helper checks. No credentials or network are used."""
import argparse
import json

import pytest

from scripts.real_data_tests.common import (
    APIError, execute, format_error_response, mask_secret,
    normalize_ad_account, numeric_id, parser, register_secret, safe_json_print, sanitize,
)


@pytest.mark.parametrize('value', ['', 'a', '1234567890'])
def test_short_secret_is_fully_masked(value: str) -> None:
    assert mask_secret(value) == '[REDACTED]'


def test_long_secret_mask() -> None:
    assert mask_secret('EAAABCDEFGHIJK123456') == 'EAAABC...3456'


@pytest.mark.parametrize('value', ['123456', 'act_123456'])
def test_account_normalization(value: str) -> None:
    assert normalize_ad_account(value) == 'act_123456'


@pytest.mark.parametrize('value', ['act_', '../me', '123?access_token=private', '１２３'])
def test_reject_invalid_ids(value: str) -> None:
    with pytest.raises(APIError):
        numeric_id(value)


def test_recursive_redaction_and_safe_error(capsys: pytest.CaptureFixture[str]) -> None:
    sentinel = register_secret('offline-test-credential/with+punctuation')
    payload = {'nested': [{'access_token': sentinel}], 'message': f'Bearer {sentinel}',
               'URL': 'https://user:password@example.com/post?access_token=unregistered#private',
               'encoded': 'offline-test-credential%2Fwith%2Bpunctuation'}
    safe_json_print(payload)
    output = capsys.readouterr().out
    assert sentinel not in output
    assert 'unregistered' not in output
    assert 'punctuation' not in output
    assert json.loads(output)['URL'] == 'https://example.com/post'
    error = format_error_response(403, {'error': {'code': 190, 'message': 'See https://api.example.com/?token=unknown'}})
    assert 'unknown' not in error
    assert '403' in error and '190' in error


def test_safe_property_and_post_url() -> None:
    assert sanitize('https://example.com/') == 'https://example.com/'
    assert sanitize('https://facebook.com/story.php?story_fbid=123&id=456&access_token=secret') == 'https://facebook.com/story.php?story_fbid=123&id=456'


def test_missing_environment_skips_without_call(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('META_AD_ACCOUNT_ID', raising=False)
    def forbidden(args: argparse.Namespace) -> None:
        pytest.fail('Missing configuration must never invoke the check')
    result = execute('Facebook Ads', ('META_AD_ACCOUNT_ID',), forbidden, argparse.Namespace())
    assert result['status'] == 'SKIP'
    assert 'test_meta_ad_accounts' in result['message']


def test_unexpected_error_does_not_expose_raw_exception() -> None:
    def broken(args: argparse.Namespace) -> None:
        raise ValueError('private-unregistered-value')
    result = execute('Offline check', (), broken, argparse.Namespace())
    assert result['status'] == 'FAIL'
    assert 'private-unregistered-value' not in str(result)


@pytest.mark.parametrize('arguments', [['--limit', '0'], ['--limit', '101'], ['--start', '2026-02-30']])
def test_cli_rejects_invalid_arguments(arguments: list[str]) -> None:
    with pytest.raises(SystemExit):
        parser('Offline', dates=True).parse_args(arguments)
