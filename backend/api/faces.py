"""人脸录入接口"""
import os

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from api.deps import get_face_service
from schemas import FaceOut
from service.service import FaceService
from common.response import ApiResponse
from core.security import require_admin

router = APIRouter(tags=["人脸录入"])


@router.post("/api/students/{sid}/faces", response_model=ApiResponse[dict])
async def enroll_face(
    sid: int,
    file: UploadFile = File(..., description="人脸照片"),
    svc: FaceService = Depends(get_face_service),
    _admin=Depends(require_admin),
):
    """上传脸照，检测人脸并三处落库"""
    content = await file.read()
    result = svc.enroll(sid, content, file.filename or "face.jpg")
    if not result["detected"]:
        raise HTTPException(status_code=400, detail=result["reason"])
    return ApiResponse(data={
        "detected": True,
        "face_id": result["face_id"],
        "image_path": result["image_path"],
    })


@router.get("/api/students/{sid}/faces", response_model=ApiResponse[list])
def list_faces(sid: int, svc: FaceService = Depends(get_face_service)):
    faces = svc.list_faces(sid)
    return ApiResponse(data=[FaceOut.model_validate(f).model_dump() for f in faces])


@router.get("/api/faces/{face_id}/image")
def get_face_image(face_id: int, svc: FaceService = Depends(get_face_service)):
    """返回脸照图片文件（供前端缩略图/预览）"""
    face = svc.repo.get_by_face_id(face_id)
    if not face or not face.image_path:
        raise HTTPException(status_code=404, detail="脸照不存在")
    if not os.path.exists(face.image_path):
        raise HTTPException(status_code=404, detail="脸照图片文件已丢失")
    return FileResponse(face.image_path)


@router.delete("/api/faces/{face_id}", response_model=ApiResponse)
def delete_face(face_id: int, svc: FaceService = Depends(get_face_service),
                _admin=Depends(require_admin)):
    ok_flag = svc.delete_face(face_id)
    if not ok_flag:
        raise HTTPException(status_code=404, detail="脸照不存在")
    return ApiResponse(message="删除成功")
