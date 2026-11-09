import request from './request'

// 考勤签到/签退
export const checkin = (formData, checkType = 'checkin') =>
  request.post(`/api/attendance/checkin?check_type=${checkType}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

// 考勤记录查询
export const getAttendance = (params) => request.get('/api/attendance', { params })

// 今日考勤统计
export const getAttendanceStats = () => request.get('/api/attendance/stats')
