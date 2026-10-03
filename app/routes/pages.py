from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.services.reports import ReportService

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))


@router.get("/overview")
async def overview_page(request: Request):
    return templates.TemplateResponse(
        "overview.html",
        {"request": request, "title": "Tổng quan toàn bộ dự án", "overview": ReportService().get_overview()},
    )


@router.get("/report/seo")
async def seo_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="seo.html",
        context={"title": "SEO & Lưu lượng Website", "seo": ReportService().get_seo(), "active_report": "seo"},
    )


@router.get("/report/facebook-ads")
@router.get("/report/ads")
@router.get("/facebook-ads")
async def facebook_ads_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="facebook_ads.html",
        context={"title": "Facebook Ads & Chi phí - Hiệu quả chiến dịch & Tối ưu CPL", "active_report": "facebook-ads", "ads": ReportService().get_facebook_ads()},
    )



@router.get("/report/{report_name}")
async def report_page(request: Request, report_name: str):
    return templates.TemplateResponse(
        "report.html",
        {"request": request, "title": report_name.replace("-", " ").title(), "report_name": report_name},
    )
