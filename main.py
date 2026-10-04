from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.routes.health import router as health_router
from app.routes.pages import router as pages_router
from app.routes.reports import router as reports_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="KDH Marketing Dashboard",
    description="Marketing reporting dashboard for KPI and channel performance analysis.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(health_router)
app.include_router(pages_router)
app.include_router(reports_router)

@app.get("/")
def root_redirect():
    return RedirectResponse(url="/overview")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
