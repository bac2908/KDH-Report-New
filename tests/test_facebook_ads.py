import csv
import io

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)
ENDPOINT = '/api/v1/reports/facebook-ads'


def report(**params):
    response = client.get(ENDPOINT, params=params)
    assert response.status_code == 200
    return response.json()


@pytest.mark.parametrize('params', [{}, {'start': '2026-09-24', 'end': '2026-09-30'}, {'status': 'attention'}, {'campaign': '893120491'}])
def test_totals_and_rates_use_the_same_counts(params):
    data = report(**params)
    totals = data['totals']
    for key in ['spend', 'reach', 'clicks', 'impressions', 'leads', 'appointments', 'landing_views']:
        assert totals[key] == sum(c[key] for c in data['campaigns'])
    assert sum(p['spend'] for p in data['placements']) == totals['spend']
    assert totals['ctr'] == pytest.approx(totals['clicks'] / totals['impressions'] * 100)
    assert totals['cpl'] == pytest.approx(totals['spend'] / totals['leads'])
    assert totals['cpc'] == pytest.approx(totals['spend'] / totals['clicks'])
    assert totals['cpa'] == pytest.approx(totals['spend'] / totals['appointments'])
    assert totals['cr'] == pytest.approx(totals['leads'] / totals['clicks'] * 100)
    assert data['analysis_method'] == 'rules'
    for metric in data['metrics']:
        assert metric['delta'] == pytest.approx((totals[metric['key']] / data['previous'][metric['key']] - 1) * 100)


def test_search_status_and_campaign_filter_every_section():
    data = report(query='TIEM CHUNG', status='active')
    assert [c['id'] for c in data['campaigns']] == ['893120491']
    assert data['totals']['spend'] == 12500000
    assert [c['id'] for c in data['creatives']] == ['video-01']
    assert '[V2]' not in data['fragments']['insights']
    empty = report(query='TIEM CHUNG', status='attention')
    assert empty['campaigns'] == empty['creatives'] == []
    assert empty['totals']['spend'] == empty['totals']['leads'] == 0
    assert empty['totals']['ctr'] is None
    assert empty['totals']['cpl'] is None
    assert 'Không có chiến dịch' in empty['fragments']['campaigns']
    assert all(p['percent'] == 0 for p in empty['placements'])


def test_cpl_sort_and_empty_query_are_stable():
    ascending = report(sort='cpl_asc')['campaigns']
    descending = report(sort='cpl_desc')['campaigns']
    assert [c['id'] for c in ascending] == ['893120491', '893120492', '893120493']
    assert [c['id'] for c in descending] == ['893120493', '893120492', '893120491']


@pytest.mark.parametrize('params', [
    {'start': '2026-09-30', 'end': '2026-09-01'}, {'start': '2026-03-31'},
    {'end': '2026-10-01'}, {'start': 'invalid'}, {'campaign': 'missing'},
    {'status': 'missing'}, {'sort': 'missing'}, {'query': 'a' * 201},
])
def test_rejects_invalid_filters(params):
    assert client.get(ENDPOINT, params=params).status_code == 422
    assert client.get(ENDPOINT + '/export', params=params).status_code == 422


def test_export_matches_filtered_counts_dates_and_comparison():
    response = client.get(ENDPOINT + '/export', params={
        'start': '2026-09-24', 'end': '2026-09-30', 'campaign': '893120493', 'compare': 'false',
    })
    assert response.status_code == 200
    assert response.content.startswith(b'\xef\xbb\xbf')
    rows = list(csv.reader(io.StringIO(response.content.decode('utf-8-sig'))))
    assert rows[1] == ['Từ ngày', '2026-09-24', 'Đến ngày', '2026-09-30']
    assert rows[4] == ['Chỉ số', 'Giá trị']
    assert rows[5] == ['Tổng Chi tiêu', '1330000']
    assert '893120491' not in response.text
    assert '893120492' not in response.text
    assert '893120493' in response.text


def test_export_search_is_text_not_a_formula():
    response = client.get(ENDPOINT + '/export', params={'query': '=1+1'})
    rows = list(csv.reader(io.StringIO(response.content.decode('utf-8-sig'))))
    assert rows[2][5] == "'=1+1"


def test_page_aliases_and_local_assets_after_reorganization():
    import re
    for path in ['/overview', '/report/seo', '/report/facebook-ads', '/report/ads', '/facebook-ads', '/report/youtube']:
        response = client.get(path)
        assert response.status_code == 200
        for asset in set(re.findall(r'(?:src|href)="(/static/[^"?]+)', response.text)):
            assert client.get(asset).status_code == 200, asset
    assert client.get('/api/v1/reports/ads').json()['totals']['leads'] == 485
