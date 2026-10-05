# Kiểm tra độc lập dữ liệu thật

Các CLI này xác minh credential đọc được dữ liệu từ Google, Meta và TikTok trước khi tích hợp. PASS giúp xác nhận quyền truy cập; không chứng minh mọi KPI đã được ánh xạ đúng với nghiệp vụ KinderHealth. Cần xác nhận đúng property, Page, ad account và định nghĩa Lead/Booking trước khi thay mock.

**Chưa thay mock data trong KDH Dashboard.** Không sửa UI, route, provider, database hoặc OAuth UI. Không cần chạy FastAPI. Import module không đọc `.env` và không gọi mạng. CRM chỉ có [checklist](CRM_BOOKING_CHECKLIST.md).

## Chuẩn bị

Tại thư mục `D:\KDH-Report-New`, dùng Python environment đã cài `requirements.txt`:

```powershell
.\.venv\Scripts\Activate.ps1
```

Nếu không muốn activate, thay `python` trong các lệnh dưới bằng `.\.venv\Scripts\python.exe`.
Chạy từ máy host; Docker image hiện tại không đóng gói thư mục `scripts`. Không cần đổi Docker để dùng bộ kiểm tra này.

Người quản lý credential tự thêm các biến vào `.env` tại root. Script **không sửa `.env`**, không ghi token vào DB hoặc file. `.env` được Git ignore; không commit secret, chụp màn hình token hoặc gửi log thô. Chỉ `.env.example` có placeholder mới để trống. Biến môi trường hệ điều hành có ưu tiên hơn `.env`.

| Nguồn | Biến cần có |
|---|---|
| Google chung | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` |
| GSC | Google chung + `GSC_PROPERTY_URL` |
| GA4 | Google chung + `GA4_PROPERTY_ID` |
| Meta Pages / Ad Account discovery | `META_API_VERSION`, `META_ACCESS_TOKEN` |
| Facebook Content | `META_API_VERSION`, `META_PAGE_ID`, `META_PAGE_ACCESS_TOKEN` |
| Facebook Ads | `META_API_VERSION`, `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID` |
| TikTok Ads | `TIKTOK_ACCESS_TOKEN`, `TIKTOK_ADVERTISER_ID` |

Repo chưa có tên biến tương đương cần alias. Các biến cấu hình app/database cũ được giữ nguyên.

- Google: dùng refresh token của OAuth app hiện có, không đổi Desktop OAuth sang Web OAuth. GSC cần scope `https://www.googleapis.com/auth/webmasters.readonly` và quyền trên property; GA4 cần `https://www.googleapis.com/auth/analytics.readonly`, quyền đọc property và bật Analytics Data API. Refresh không tự thêm scope chưa được cấp.
- `GSC_PROPERTY_URL`: nhập chính xác URL-prefix (gồm dấu `/` cuối nếu có) hoặc `sc-domain:domain-cua-ban`; script URL-encode property. `GA4_PROPERTY_ID`: ID số, chấp nhận tiền tố `properties/`; không dùng Measurement ID `G-...`.
- Meta: tự đặt `META_API_VERSION` dạng `vNN.N` theo phiên bản còn hỗ trợ của app; script không đoán phiên bản mới nhất. User token dùng discovery/Ads; Page token dùng đọc posts. Quyền thường cần kiểm tra: `pages_show_list`, `pages_read_engagement`, và `ads_read` cùng quyền trên tài sản. Một số nội dung/field có thể cần quyền bổ sung hoặc App Review theo loại token/app.
- `META_PAGE_ID`: ID số. `META_AD_ACCOUNT_ID`: chấp nhận ID số hoặc `act_` + ID số. Discovery không tự chọn tài khoản, không ghi Page token xuống đĩa. Token hiển thị chỉ có dạng mask; giá trị ngắn được ẩn toàn bộ. Cần tự lấy Page token đầy đủ qua luồng quản lý credential được phép, không thể tái sử dụng chuỗi mask làm token.
- TikTok: token Business API phải được cấp quyền report cho đúng advertiser; `TIKTOK_ADVERTISER_ID` là ID số. Base URL `v1.3` nằm một chỗ trong `test_tiktok_ads.py`.

## Lệnh chạy và kết quả mong đợi

Chạy lần lượt:

```powershell
python -m scripts.real_data_tests.test_gsc
python -m scripts.real_data_tests.test_ga4
python -m scripts.real_data_tests.test_meta_pages
python -m scripts.real_data_tests.test_facebook_content
python -m scripts.real_data_tests.test_meta_ad_accounts
python -m scripts.real_data_tests.test_meta_ads
python -m scripts.real_data_tests.test_tiktok_ads
```

| Module | Khi PASS |
|---|---|
| `test_gsc` | Top query, clicks, impressions, CTR dạng tỷ lệ 0–1 và vị trí trung bình |
| `test_ga4` | Bảng theo ngày: activeUsers, sessions, screenPageViews, eventCount; thêm top channel groups nếu request phụ thành công |
| `test_meta_pages` | Danh sách Page token nhìn thấy, ID, tasks, Page token đã mask; không yêu cầu đủ 3 Page |
| `test_facebook_content` | Post ID, ngày, caption tối đa 160 ký tự, reactions/comments/shares và permalink; không suy diễn Reach |
| `test_meta_ad_accounts` | Account ID, tên, trạng thái, currency, timezone; người dùng tự chọn đúng account chạy quảng cáo KinderHealth |
| `test_meta_ads` | Campaign metrics và actions nguyên gốc; các conversion action chỉ là ứng viên, không tính Lead hoặc CPL |
| `test_tiktok_ads` | HTTP 200 **và** API code `0`; bảng spend/impressions/clicks/ctr/cpc theo ngày |

Hoặc chạy tất cả, mỗi nguồn được xử lý độc lập:

```powershell
python -m scripts.real_data_tests.run_all
```

Kết thúc có bảng PASS/FAIL/SKIP theo thứ tự trên và `CRM / Booking: NOT CONFIGURED`. Thiếu cấu hình nguồn nào thì chỉ SKIP nguồn đó. Thiếu Meta ad account thì chạy discovery trước.

Report mặc định **2026-09-01 đến 2026-09-30**. GSC, GA4, Meta Ads, TikTok và run_all hỗ trợ:

```powershell
python -m scripts.real_data_tests.test_gsc --start 2026-09-01 --end 2026-09-30 --limit 10
python -m scripts.real_data_tests.test_facebook_content --page-id 123456789 --limit 5
python -m scripts.real_data_tests.run_all --start 2026-09-01 --end 2026-09-30 --limit 10
```

`123456789` chỉ minh họa cú pháp ID, hãy thay bằng Page ID thật. `--page-id` có ưu tiên hơn `META_PAGE_ID`. `--help` không đọc credential và không gọi mạng.

Giới hạn CLI chung 1–100 dòng, mặc định 10; riêng Facebook Content mặc định 5 bài gần nhất, không lọc ngày. `run_all --limit` áp dụng cho các report và Content. Discovery Page/Ad Account lấy tối đa 10 trang × 100 mục; báo `Pagination truncated` nếu còn dữ liệu. Discovery bỏ qua `--limit`. Các report chỉ lấy một trang mẫu, không export toàn bộ dữ liệu: Meta báo `More available`, TikTok có page info; GA4/GSC có thể còn dòng ngoài limit. Đây không phải tổng hợp kỳ đầy đủ. Múi giờ và cách ghi nhận chỉ số theo từng nền tảng.

## Trạng thái và mã thoát

- `PASS`: API trả thành công, có dữ liệu hoặc truy cập hợp lệ nhưng kỳ/danh sách rỗng. Không biến dữ liệu rỗng thành mock.
- `FAIL`: lỗi API, xác thực, quyền, cấu hình sai hoặc response không hợp lệ. TikTok HTTP 200 với code khác `0` vẫn FAIL.
- `SKIP`: thiếu biến cấu hình, không gửi request nguồn đó.

Exit code: `0` nếu tất cả check đã chạy PASS; `1` nếu có FAIL; `2` nếu không có FAIL nhưng còn SKIP. GA4 report chính thành công nhưng report channel lỗi vẫn PASS kèm `Channel warning`. Không có Lead/Booking được tự chọn từ event GA4.

Mỗi request timeout 30 giây; không tự retry, không theo redirect. Không in raw exception, header credential hoặc URL chứa token. URL hiển thị được bỏ thông tin đăng nhập, fragment và query không cần thiết. Field không trả về hiển thị `N/A`; không suy ra 0 hoặc metric khác. Token được giữ trong bộ nhớ trong thời gian chạy, không lưu trên đĩa.

## Troubleshooting

### Google

- **401**: token không hợp lệ/hết hạn; kiểm tra OAuth credential và refresh token thuộc đúng client.
- **403**: kiểm tra scope, API đã bật và quyền tài khoản Google trên đúng GSC/GA4 property. Refresh token cũ không tự có scope mới.
- **404**: kiểm tra `GSC_PROPERTY_URL` chính xác (domain property khác URL-prefix) hoặc GA4 property ID; không dùng stream/measurement ID.
- **200 nhưng không có rows**: truy cập thành công; kiểm tra kỳ có dữ liệu, độ trễ và timezone. Không giả dữ liệu để lấp khoảng trống.
- **invalid_grant / invalid_client** ở OAuth: xác minh token bị thu hồi/hết hạn, client và cấu hình OAuth hiện có. Không tự đổi loại OAuth app.

### Meta

- **Invalid token / code 190**: kiểm tra token hết hạn/thu hồi, loại token, app và người dùng cấp quyền.
- **Missing permissions / code 10, 200 hoặc HTTP 403**: kiểm tra scope và quyền trên Page/ad account, app mode/App Review. Graph API có thể trả lỗi quyền bằng HTTP 400.
- **`/me/accounts` rỗng**: token truy cập endpoint hợp lệ nhưng không có Page quản lý được trả về. Kiểm tra người dùng, business assignment và `pages_show_list`; không mặc định đủ 3 Page KinderHealth.
- **Wrong Page ID**: chạy discovery, xác minh Page token thuộc đúng Page và quyền đọc bài. Không dùng User ID thay Page ID.
- **Wrong Ad Account ID**: chạy discovery, chọn tài khoản thực chạy campaign của khách; script chấp nhận cả số và `act_...`.
- **Unsupported field/version**: kiểm tra phiên bản trong `.env` và field ở `test_facebook_content.py` (`/{page_id}/posts`), `test_meta_pages.py` (`/me/accounts`), `test_meta_ad_accounts.py` (`/me/adaccounts`) hoặc `test_meta_ads.py` (`/{act_id}/insights`). Script báo FAIL, không tự thay field thành Reach/Lead hay fake response.

### TikTok

- **HTTP error**: kiểm tra mạng, endpoint và quyền; lỗi kết nối không in URL/token.
- **HTTP 200 nhưng API code lỗi**: vẫn FAIL; đọc code/message đã được làm sạch.
- **Token expired**: cấp lại/refresh bằng quy trình credential của khách, script không tự lưu token.
- **Advertiser access denied**: xác minh advertiser đã authorize app và có quyền đọc report.
- **Dimension/metric không hỗ trợ**: xác minh `report/integrated/get/`, `AUCTION_ADVERTISER`, `advertiser_id` + `stat_time_day`, và danh sách metrics trong `test_tiktok_ads.py` với tài liệu app đang dùng. Không đổi nghĩa metric hoặc giả response.

## Kiểm tra code offline

```powershell
python -m pytest -q
```

`pytest.ini` chỉ discover `tests/`. Các test bổ sung chỉ kiểm tra helper offline, không gọi API. Không dùng pytest để chạy các CLI ngoài mạng. Chỉ chạy API sau khi bạn chủ động gọi module và đã cấu hình credential.

## Tài liệu đối chiếu

- [Google Desktop OAuth: refresh access token](https://developers.google.com/identity/protocols/oauth2/native-app#offline)
- [GSC Search Analytics query](https://developers.google.com/webmaster-tools/v1/searchanalytics/query)
- [GA4 Data API runReport](https://developers.google.com/analytics/devguides/reporting/data/v1/basics)
- [Meta Page access](https://developers.facebook.com/docs/graph-api/reference/user/accounts/), [Page posts](https://developers.facebook.com/docs/graph-api/reference/page/posts/), [Ad accounts](https://developers.facebook.com/docs/graph-api/reference/user/adaccounts/), [Ads Insights](https://developers.facebook.com/docs/marketing-api/insights/)
- Đối chiếu bổ sung khi cổng Meta docs không truy cập được: SDK chính thức của Meta, [User edges](https://github.com/facebook/facebook-python-business-sdk/blob/main/facebook_business/adobjects/user.py), [Page](https://github.com/facebook/facebook-python-business-sdk/blob/main/facebook_business/adobjects/page.py), [AdsInsights fields](https://github.com/facebook/facebook-python-business-sdk/blob/main/facebook_business/adobjects/adsinsights.py). Chỉ dùng để đối chiếu, không thêm SDK vào dependency.
- [TikTok official Business API SDK: Reporting API](https://github.com/tiktok/tiktok-business-api-sdk/blob/main/python_sdk/docs/ReportingApi.md)

Đã đối chiếu tài liệu Google và SDK/tài liệu reporting chính thức của TikTok. Meta documentation yêu cầu truy cập phù hợp và có thể thay đổi theo app/version; việc field hoạt động trên credential của KinderHealth phải được xác nhận bằng chính các lệnh này. Chưa có credential nên chưa thể chứng nhận kết nối thật hoặc field runtime của bất kỳ nguồn nào.
