import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import axios from 'axios'
import App from './App.vue'

const app = createApp(App)
axios.defaults.baseURL = '/api'
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
axios.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      location.reload()
    }
    return Promise.reject(err)
  }
)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
