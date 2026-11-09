"""枚举接口 + 公告接口"""
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks

from api.deps import get_notice_service
from core import enums
from core.ws_manager import manager
from schemas import NoticeCreate, NoticeOut, NoticeUpdate
from service.service import NoticeService
from common.response import ApiResponse

router = APIRouter(tags=["枚举/公告"])


# ============ 枚举 ============
@router.get("/api/enums", response_model=ApiResponse[dict])
def get_enums():
    """返回班级/专业下拉选项"""
    return ApiResponse(data={"classes": enums.CLASSES, "majors": enums.MAJORS})


# ============ 公告 ============
@router.get("/api/notices", response_model=ApiResponse[dict])
def list_notices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: NoticeService = Depends(get_notice_service),
):
    total, items = svc.list(page, page_size)
    return ApiResponse(data={"total": total, "page": page, "page_size": page_size,
                             "items": [NoticeOut.model_validate(i).model_dump() for i in items]})


@router.post("/api/notices", response_model=ApiResponse[dict], status_code=201)
async def create_notice(data: NoticeCreate, background_tasks: BackgroundTasks,
                        svc: NoticeService = Depends(get_notice_service)):
    n = svc.create(data.model_dump())
    notice_dict = NoticeOut.model_validate(n).model_dump()
    # 后台任务：广播公告给所有在线客户端（不阻塞响应）
    background_tasks.add_task(
        manager.broadcast,
        {"type": "notice", "data": notice_dict},
    )
    return ApiResponse(data=notice_dict)


@router.get("/api/notices/{nid}", response_model=ApiResponse[dict])
def get_notice(nid: int, svc: NoticeService = Depends(get_notice_service)):
    n = svc.get(nid)
    if not n:
        raise HTTPException(status_code=404, detail="公告不存在")
    return ApiResponse(data=NoticeOut.model_validate(n).model_dump())


@router.put("/api/notices/{nid}", response_model=ApiResponse[dict])
def update_notice(nid: int, data: NoticeUpdate, svc: NoticeService = Depends(get_notice_service)):
    n = svc.update(nid, data.model_dump())
    if not n:
        raise HTTPException(status_code=404, detail="公告不存在")
    return ApiResponse(data=NoticeOut.model_validate(n).model_dump())


@router.delete("/api/notices/{nid}", response_model=ApiResponse)
def delete_notice(nid: int, svc: NoticeService = Depends(get_notice_service)):
    if not svc.delete(nid):
        raise HTTPException(status_code=404, detail="公告不存在")
    return ApiResponse(message="删除成功")
