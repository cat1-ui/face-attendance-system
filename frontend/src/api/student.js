import request from './request'

// 学生管理
export const getStudents = (params) => request.get('/api/students', { params })
export const getStudent = (id) => request.get(`/api/students/${id}`)
export const createStudent = (data) => request.post('/api/students', data)
export const updateStudent = (id, data) => request.put(`/api/students/${id}`, data)
export const deleteStudent = (id) => request.delete(`/api/students/${id}`)
export const importStudents = (formData) => request.post('/api/students/import', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})

// 枚举
export const getEnums = () => request.get('/api/enums')
