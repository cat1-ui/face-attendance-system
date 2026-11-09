import request from './request'

// 汇总统计
export const getSummary = () => request.get('/api/stats/summary')
export const getFaceCoverage = () => request.get('/api/stats/face-coverage')
export const getFaceCount = () => request.get('/api/stats/face-count')
