"""汇总统计 + 脸库审计接口"""
from fastapi import APIRouter, Depends

from core.db import get_db
from service.stats_service import StatsService, ClusterService
from common.response import ApiResponse

router = APIRouter(tags=["汇总/审计"])


@router.get("/api/stats/summary", response_model=ApiResponse[dict])
def summary(db=Depends(get_db)):
    return ApiResponse(data=StatsService(db).summary())


@router.get("/api/stats/face-coverage", response_model=ApiResponse[dict])
def face_coverage(db=Depends(get_db)):
    return ApiResponse(data=StatsService(db).face_coverage())


@router.get("/api/stats/face-count", response_model=ApiResponse[dict])
def face_count(db=Depends(get_db)):
    return ApiResponse(data=StatsService(db).face_count_dist())


@router.get("/api/audit/duplicates", response_model=ApiResponse[dict])
def duplicates(db=Depends(get_db)):
    return ApiResponse(data=ClusterService(db).find_duplicates())
