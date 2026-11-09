import request from './request'

// 公告管理
export const getNotices = (params) => request.get('/api/notices', { params })
export const getNotice = (id) => request.get(`/api/notices/${id}`)
export const createNotice = (data) => request.post('/api/notices', data)
export const updateNotice = (id, data) => request.put(`/api/notices/${id}`, data)
export const deleteNotice = (id) => request.delete(`/api/notices/${id}`)
