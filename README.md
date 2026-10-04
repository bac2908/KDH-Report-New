# KDH Marketing Reporting Dashboard

A FastAPI + Jinja2 marketing reporting dashboard built around a mock-data-first architecture.

## Stack

- FastAPI
- SQLAlchemy / PostgreSQL-ready data layer
- Jinja2 templates
- Vanilla JS + ECharts
- Pytest for smoke tests

## Chạy bằng Docker — một lệnh

Cài và mở Docker Desktop (Linux containers). Tại thư mục dự án, chạy:

```sh
docker compose up --build -d
```

Mở **http://localhost:8080** (tự chuyển đến `/overview`). FE và BE của **KDH-Report-New**
chạy trong container `kdh-report-new-app-1`, nhóm Compose **`kdh-report-new`**.
Nhóm này độc lập với dự án **KDH-Report** (`kdh-report`); không dùng chung container
hoặc network của hai dự án. Chạy lệnh trong đúng thư mục `D:\KDH-Report-New`.
Docker tự cài thư viện Python, build Tailwind CSS và khởi động FastAPI; máy host
không cần cài Python hoặc Node.js. Lần build đầu cần Internet để tải image và thư viện.
Cổng mặc định là 8080 để không trùng bản uvicorn đang chạy ở cổng 8000.

```sh
docker compose ps              # Kiểm tra trạng thái / healthcheck
docker compose logs -f app     # Xem log (Ctrl+C chỉ thoát xem log)
docker compose down            # Dừng và gỡ container của dự án
```

Sau khi sửa code, chạy lại `docker compose up --build -d` để cập nhật.
Container tự khởi động lại khi Docker Engine chạy, trừ khi đã chủ động dừng.
Muốn đổi cổng trên PowerShell, đặt `$env:KDH_PORT = '8090'` trước khi chạy Compose.
Ứng dụng mặc định chỉ được mở trên máy đang chạy Docker.

Bản Docker dùng cùng dữ liệu mẫu như bản local. Chưa thêm database vì luồng báo cáo
hiện chưa sử dụng database; Docker không tự kết nối Meta, Google hoặc CRM.
Các file `.env`, môi trường ảo, `node_modules` và dữ liệu thử trong `.work` không được
đưa vào image. Node.js chỉ dùng ở bước build CSS; container chạy bằng user không phải root.

## Run locally without Docker

1. Create and activate a virtual environment.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Start the app:
   `uvicorn main:app --reload`
4. Open http://localhost:8000/overview

## Features

- Vietnamese KinderHealth overview matching the supplied reference design
- Five KPI cards, six marketing channels, trend comparison and channel contributions
- Highlights, optimization alerts and next-period action plan
- Responsive navigation, date filters, chart metric switcher and comparison toggle
- Excel-compatible CSV export and browser print / Save as PDF (including plan-only print)
- JSON API endpoints for report data
- Repository/service layer separated from UI rendering
- SEO & website traffic dashboard at `/report/seo`, matching the supplied SEO HTML
- SEO ranking tabs, keyword search, landing-page details, weekly report and filtered CSV export
- Facebook Ads campaign filters, CPL sorting, campaign/creative details and an ad library
- Consistent Ads KPI, funnel and placement totals; filtered CSV and browser PDF export
- Rule-based Ads optimization report with text/PDF downloads (no AI service required)

The overview uses explicitly labeled mock data. September 2026 matches the reference;
other selectable periods (April–September 2026) are proportional demonstrations.
It is not connected to live customer or advertising accounts. Existing channel pages
remain available through the sidebar.

The SEO page preserves the reference's 148-keyword / 24-page summary counts. Its detailed
sample contains the six keywords and four landing pages provided in that reference.
Date filters scale sample counts; rankings, rates, and the illustrative trend shapes
are demonstration values. All reports share one sidebar. SEO and Facebook Ads use
the same inline accordion: the label opens the report, the arrow expands its sections.
Section links on the current report preserve filters and scroll to the selected section.

Facebook Ads at `/report/facebook-ads` uses three sample campaigns and three featured
creatives. Filters apply to the entire report, including exports and recommendations.
CTR, CPC, CPL, conversion and appointment rates are calculated from the same counts.
Demographic profiles and placement shares are illustrative. The optimization report
uses deterministic rules; Meta Marketing API, CRM and AI services are not connected.

## Dashboard styling

The compiled stylesheet, fonts, icons and logo are served locally; no Tailwind CDN or
external chart library is needed by `/overview`, `/report/seo` or `/report/facebook-ads`. To rebuild styles after changing
templates or `static/css/shared/dashboard.source.css`:

```sh
npm ci
npm run build:css
```

Run backend checks with `python -m pytest -q`.

## Project structure

The frontend is server-rendered Jinja2 HTML with local CSS and vanilla JavaScript.
`templates/` and `static/` together form the frontend; Python routes, services and
integrations remain in `app/`.

```text
templates/
  layouts/
    dashboard.html          # Shared dashboard document and shell
    basic.html              # Layout for generic channel reports
  components/dashboard/
    sidebar.html
    navigation.html         # Shared channel links and inline submenus
    header.html
    controls.html           # Shared date/source dialogs, export menu, toast
  pages/
    overview/
      index.html            # Page entry point: compose sections and load assets
      controls.html         # Page-specific dialogs
      partials/             # Summary, KPIs, channels, analytics, insights, plan
    seo/
      index.html
      controls.html
      partials/             # Summary, KPIs, trend, funnel, keywords, details
    facebook_ads/
      index.html
      controls.html
      partials/             # KPIs, campaigns, funnel, audience, creatives, insights
    report/
      index.html            # Generic channel report
static/
  css/
    shared/                 # Fonts, basic styles, dashboard.source.css
    pages/                  # seo.css and facebook-ads.css
    dist/dashboard.css      # Generated Tailwind output
  js/
    shared/                 # Shared sidebar, generic report bootstrap, chart helpers
    pages/                  # overview.js, seo.js, facebook-ads.js
  fonts/                    # Local fonts and icons with licenses
  img/                      # Logo and sample creative images
app/
  routes/                   # Page and JSON/CSV endpoints
  services/                 # Report orchestration
  repositories/             # Data access
  integrations/mock/        # Explicitly labeled sample data
  presentation.py           # Render the same Ads partials for AJAX updates
tests/                      # Endpoint, filtering and calculation checks
```

Edit page content in its `partials/`, and page behavior in `static/js/pages/`.
Change shared navigation once in `components/dashboard/`. `index.html` composes the
sections and declares that page's CSS/JS. Each page loads its own script explicitly.
Edit `static/css/shared/dashboard.source.css`, then run `npm run build:css`;
do not edit generated `static/css/dist/dashboard.css` directly. Public page URLs
are unchanged by this folder organization.
