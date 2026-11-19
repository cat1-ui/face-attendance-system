import request from '../api/request'

// 浏览器用 <img src> 加载图片时，不会带上 Authorization 头，
// 受保护的图片接口一律 401。所以这里先用 axios 取回二进制，
// 再转成 object URL 交给 <img> / el-image 用。
// 注意：object URL 会占内存，组件卸载时要 revokeObjectURL。
export async function fetchImageObjectUrl(path) {
  const blob = await request.get(path, { responseType: 'blob' })
  return URL.createObjectURL(blob)
}
