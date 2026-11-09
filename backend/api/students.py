"""学生管理接口 - 控制层（对应 @RestController）

异常流转链：
  业务层 raise ValueError → 控制层 except → raise HTTPException → 全局异常处理器转 ApiResponse
"""
import io

import pandas as pd
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File

from api.deps import get_student_service
from schemas import StudentCreate, StudentUpdate
from service.service import StudentService
from common.response import ApiResponse

router = APIRouter(prefix="/api/students", tags=["学生管理"])


@router.get("", response_model=ApiResponse[dict])
def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: str | None = Query(None, description="姓名(模糊)"),
    student_no: str | None = Query(None, description="学号(模糊)"),
    phone: str | None = Query(None, description="联系方式(模糊)"),
    gender: str | None = Query(None, description="性别(精确，男/女)"),
    age: int | None = Query(None, ge=18, le=28, description="年龄(精确，18~28)"),
    class_name: str | None = Query(None, description="班级(模糊)"),
    major: str | None = Query(None, description="专业(模糊)"),
    enroll_year: int | None = Query(None, description="入学年份(精确)"),
    face_status: int | None = Query(None, description="录入状态(精确)"),
    svc: StudentService = Depends(get_student_service),
):
    filters = {
        "name": name, "student_no": student_no, "phone": phone,
        "gender": gender, "age": age, "class_name": class_name, "major": major,
        "enroll_year": enroll_year, "face_status": face_status,
    }
    # 组合查询语义：所有已填条件之间是 AND（多填一个就多收窄一层）；
    # 其中模糊字段再做最短长度校验，防止只输入 1 个字符就把全部学生暴露出来
    # 各字段最短长度：学号 3 位、姓名 2 位、电话 4 位、班级 2 位、专业 2 位
    # （age/gender/enroll_year/face_status 是精确匹配，不设最短长度）
    min_len_map = {
        "name": 2, "student_no": 3, "phone": 4, "class_name": 2, "major": 2,
    }
    field_label = {
        "name": "姓名", "student_no": "学号", "phone": "联系方式",
        "class_name": "班级", "major": "专业",
    }
    for field, min_len in min_len_map.items():
        val = filters.get(field)
        if val is not None and val != "" and len(str(val)) < min_len:
            label = field_label.get(field, field)
            raise HTTPException(
                status_code=400,
                detail=f"「{label}」至少输入 {min_len} 个字符，当前仅 {len(str(val))} 个",
            )
    total, items = svc.list(page, page_size, **filters)
    return ApiResponse(data={"total": total, "page": page, "page_size": page_size,
                             "items": [i.model_dump() for i in items]})


@router.get("/{sid}", response_model=ApiResponse[dict])
def get_student(sid: int, svc: StudentService = Depends(get_student_service)):
    s = svc.get(sid)
    if not s:
        raise HTTPException(status_code=404, detail="学生不存在")
    return ApiResponse(data=s.model_dump())


@router.post("", response_model=ApiResponse[dict], status_code=201)
def create_student(data: StudentCreate, svc: StudentService = Depends(get_student_service)):
    try:
        s = svc.create(data)
        return ApiResponse(data=s.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{sid}", response_model=ApiResponse[dict])
def update_student(sid: int, data: StudentUpdate, svc: StudentService = Depends(get_student_service)):
    s = svc.update(sid, data)
    if not s:
        raise HTTPException(status_code=404, detail="学生不存在")
    return ApiResponse(data=s.model_dump())


@router.delete("/{sid}", response_model=ApiResponse)
def delete_student(sid: int, svc: StudentService = Depends(get_student_service)):
    ok_flag = svc.delete(sid)
    if not ok_flag:
        raise HTTPException(status_code=404, detail="学生不存在")
    return ApiResponse(message="删除成功")


@router.post("/import", response_model=ApiResponse[dict])
async def import_students(
    file: UploadFile = File(..., description="CSV 文件（含 student_no,name,gender,age,class_name,major,enroll_year,phone 列）"),
    svc: StudentService = Depends(get_student_service),
):
    """批量导入学生 CSV"""
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception:
        raise HTTPException(status_code=400, detail="CSV 解析失败，请检查文件格式")

    # 列名映射（兼容中英文表头）
    col_map = {
        "student_no": "student_no", "学号": "student_no",
        "name": "name", "姓名": "name",
        "gender": "gender", "性别": "gender",
        "age": "age", "年龄": "age",
        "class_name": "class_name", "班级": "class_name",
        "major": "major", "专业": "major",
        "enroll_year": "enroll_year", "入学年份": "enroll_year",
        "phone": "phone", "联系方式": "phone", "电话": "phone",
    }
    df = df.rename(columns=col_map)

    # 只保留有效列，转成 list[dict]
    valid_cols = ["student_no", "name", "gender", "age", "class_name", "major", "enroll_year", "phone"]
    df = df[[c for c in valid_cols if c in df.columns]]
    # NaN 转 None，整型列转 int（pandas 读进来是 float，直接入库会变 20.0）
    rows = df.where(pd.notnull(df), None).to_dict(orient="records")
    for r in rows:
        for col in ("enroll_year", "age"):
            if r.get(col) is not None:
                r[col] = int(r[col])

    result = svc.import_students(rows)
    return ApiResponse(data=result)
