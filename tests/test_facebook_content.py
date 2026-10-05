import csv
import io

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
API = '/api/v1/reports/facebook-content'


@pytest.mark.parametrize('params', [{}, {'start': '2026-09-24', 'end': '2026-09-30'}, {'start': '2026-04-01', 'end': '2026-09-30'}])
def test_content_summary_reconciles(params):
    response = client.get(API, params=params)
    assert response.status_code == 200
    data = response.json()
    m = data['metrics']
    assert sum(row['count'] for row in data['formats']) == m['total_posts']
    assert sum(row['count'] for row in data['topics']) == m['total_posts']
    assert sum(row['reach'] for row in data['topics']) == m['reach']
    assert sum(row['value'] for row in data['engagement_breakdown']) == m['engagement']
    assert data['engagement_breakdown'][-1]['value'] == m['link_clicks']
    assert data['reach_mix']['organic'] + data['reach_mix']['paid'] == m['reach']
    assert m['engagement_rate'] == round(m['engagement'] / m['reach'] * 100, 2)
    assert len(data['fragments']) == 7
    assert all(fragment.strip() != '<div></div>' for fragment in data['fragments'].values())


def test_filters_only_affect_known_posts_and_honor_dates():
    data = client.get(API, params={'query': 'DINH DUONG', 'format': 'carousel'}).json()
    assert [row['id'] for row in data['posts']] == ['post-004']
    assert data['metrics']['total_posts'] == 48
    week = client.get(API, params={'start': '2026-09-24', 'end': '2026-09-30'}).json()
    assert [row['id'] for row in week['posts']] == ['post-004', 'post-005']
    assert client.get(API, params={'format': 'photo'}).json()['posts'] == []
    assert client.get(API, params={'start': '2026-08-01', 'end': '2026-08-31'}).json()['posts'] == []


@pytest.mark.parametrize('sort,key', [('reach_desc','reach'), ('engagement_desc','engagement'), ('shares_desc','shares'), ('clicks_desc','clicks')])
def test_posts_sorted(sort, key):
    posts = client.get(API, params={'sort': sort}).json()['posts']
    assert [p[key] for p in posts] == sorted([p[key] for p in posts], reverse=True)


@pytest.mark.parametrize('params', [{'start':'2026-10-01'}, {'start':'2026-09-30','end':'2026-09-01'}, {'format':'bad'}, {'topic':'bad'}, {'sort':'bad'}, {'query':'x'*201}])
def test_content_rejects_invalid_filters(params):
    assert client.get(API, params=params).status_code == 422
    assert client.get(API + '/export', params=params).status_code == 422


def test_content_csv_matches_filters_and_prevents_formulas():
    response = client.get(API + '/export', params={'topic':'nutrition','compare':'false'})
    assert response.status_code == 200
    assert response.content.startswith(b'\xef\xbb\xbf')
    assert 'post-004' in response.text and 'post-001' not in response.text
    assert 'Kỳ trước' not in response.text
    response = client.get(API + '/export', params={'query':'=1+1'})
    rows = list(csv.reader(io.StringIO(response.content.decode('utf-8-sig'))))
    assert rows[3][1] == "'=1+1"


def test_content_page_aliases_and_active_navigation():
    for path in ['/report/social', '/report/facebook-content']:
        response = client.get(path)
        assert response.status_code == 200
        assert 'href="/report/social" aria-current="page"' in response.text
        assert 'fc-topic-grid' in response.text
        assert 'post-005' in response.text
