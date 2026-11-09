"""考勤接口 - 控制层（对应 @RestController）"""
from fastapi import APIRouter, Depends, Query, UploadFile, File

from api.deps import get_attendance_service
from service.attendance_service import AttendanceService
from common.response import ApiResponse

router = APIRouter(prefix="/api/attendance", tags=["考勤签到"])


@router.post("/checkin", response_model=ApiResponse[dict])
async def checkin(
    file: UploadFile = File(..., description="人脸照片"),
    check_type: str = Query("checkin", description="checkin签到 / checkout签退"),
    svc: AttendanceService = Depends(get_attendance_service),
):
    """上传照片签到/签退：识别身份 + 判定状态 + 落库"""
    content = await file.read()
    result = svc.checkin(content, check_type)
    return ApiResponse(data=result.model_dump())


@router.get("", response_model=ApiResponse[dict])
def list_attendance(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: int | None = Query(None, description="学生ID(精确)"),
    check_type: str | None = Query(None, description="checkin/checkout"),
    status: str | None = Query(None, description="normal/late/early/absent"),
    day: str | None = Query(None, description="日期(YYYY-MM-DD)"),
    svc: AttendanceService = Depends(get_attendance_service),
):
    """考勤记录分页查询"""
    filters = {"student_id": student_id, "check_type": check_type, "status": status, "day": day}
    total, items = svc.list_records(page, page_size, **filters)
    return ApiResponse(data={"total": total, "page": page, "page_size": page_size, "items": items})


@router.get("/stats", response_model=ApiResponse[dict])
def attendance_stats(svc: AttendanceService = Depends(get_attendance_service)):
    """今日考勤统计"""
    return ApiResponse(data=svc.today_stats())
