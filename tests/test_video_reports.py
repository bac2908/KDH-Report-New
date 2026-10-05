import csv
from io import StringIO

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
BASE = '/api/v1/video-reports/'


@pytest.mark.parametrize('start,end', [('2026-09-01','2026-09-30'), ('2026-09-24','2026-09-30'), ('2026-09-30','2026-09-30'), ('2026-04-01','2026-09-30')])
def test_tiktok_totals_and_daily_series_reconcile(start, end):
    data = client.get(BASE + 'tiktok', params={'start':start, 'end':end}).json()
    for key in ['spend','reach','views','clicks','leads']:
        assert data['totals'][key] == sum(row[key] for row in data['rows'])
    assert sum(data['chart']['series'][0]) == data['totals']['spend']
    assert sum(data['chart']['series'][1]) == data['totals']['leads']
    assert data['chart']['dates'][0] == start and data['chart']['dates'][-1] == end
    assert data['totals']['cpa'] == round(data['totals']['spend'] / data['totals']['leads'])
    assert data['data_source'] == 'mock'


def test_reference_totals_and_youtube_chart_modes():
    tt = client.get(BASE + 'tiktok').json()
    yt = client.get(BASE + 'youtube').json()
    assert tt['totals']['spend'] == 18500000 and tt['totals']['leads'] == 315
    assert yt['totals']['views'] == 124500 and yt['totals']['watch_hours'] == 4850
    assert sum(yt['chart']['series'][0]) == 124500
    assert sum(yt['chart']['watch_series'][0]) == 4850
    assert len(yt['rows']) == 4
    for data in (tt,yt):
        assert all(data['fragments'][key].strip() for key in ('kpis','table','funnel'))


def test_filters_dates_empty_and_csv_match():
    params = {'query':'DINH DUONG', 'status':'optimize'}
    data = client.get(BASE + 'tiktok', params=params).json()
    assert [r['id'] for r in data['rows']] == ['TK-V3']
    assert data['totals']['spend'] == 18500000
    response = client.get(BASE + 'tiktok/export', params=params)
    assert response.content.startswith(b'\xef\xbb\xbf')
    assert 'TK-V3' in response.text and 'TK-V1' not in response.text
    response = client.get(BASE + 'youtube', params={'start':'2026-09-24','end':'2026-09-30'})
    assert response.json()['rows'] == []
    assert 'Không có video mẫu' in response.json()['fragments']['table']
    assert [r['id'] for r in client.get(BASE + 'youtube', params={'query':'tiem chung'}).json()['rows']] == ['YT-02']


@pytest.mark.parametrize('channel,params', [
    ('tiktok',{'start':'2026-10-01'}), ('youtube',{'start':'2026-09-30','end':'2026-09-01'}),
    ('tiktok',{'status':'invalid'}), ('youtube',{'status':'high'}),
    ('youtube',{'sort':'spend'}), ('tiktok',{'sort':'subscribers'}), ('youtube',{'query':'x'*201}),
])
def test_invalid_filters_rejected_in_api_and_export(channel, params):
    for suffix in ('','/export'):
        assert client.get(BASE + channel + suffix, params=params).status_code == 422


def test_csv_formula_safety_and_comparison():
    response = client.get(BASE + 'youtube/export', params={'query':'=1+1', 'compare':'false'})
    rows = list(csv.reader(StringIO(response.content.decode('utf-8-sig'))))
    assert rows[2][1] == "'=1+1"
    assert 'Kỳ trước' not in response.text
    assert 'Thời gian xem (giờ)' in response.text
    daily_header = next(i for i, row in enumerate(rows) if row == ['Ngày', 'Thời gian xem (giờ)'])
    assert sum(int(row[1]) for row in rows[daily_header + 1:daily_header + 31]) == 4850


@pytest.mark.parametrize('path,marker', [('/report/tiktok','tt-campaigns'),('/report/tiktok-ads','tt-videos'),('/report/youtube','yt-audience')])
def test_pages_have_dedicated_content_and_shared_navigation(path, marker):
    response = client.get(path)
    assert response.status_code == 200
    assert f'id="{marker}"' in response.text
    assert 'id="tiktok-submenu"' in response.text and 'id="youtube-submenu"' in response.text
    assert '/static/js/pages/video.js' in response.text
