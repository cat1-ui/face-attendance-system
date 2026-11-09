import request from './request'

// 人脸录入
export const uploadFace = (studentId, formData) => request.post(`/api/students/${studentId}/faces`, formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})
export const getFaces = (studentId) => request.get(`/api/students/${studentId}/faces`)
export const deleteFace = (faceId) => request.delete(`/api/faces/${faceId}`)
