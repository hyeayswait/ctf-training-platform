<template>
  <div>
    <!-- 未登录 -->
    <div v-if="!token" class="auth-wrap">
      <el-card class="auth-card">
        <h2 style="text-align:center">🚩 CTF Training Platform</h2>
        <el-tabs v-model="tab">
          <el-tab-pane label="登录" name="login">
            <el-form :model="loginForm" label-width="60px">
              <el-form-item label="账号"><el-input v-model="loginForm.username" /></el-form-item>
              <el-form-item label="密码"><el-input v-model="loginForm.password" type="password" @keyup.enter="onLogin" /></el-form-item>
              <el-button type="primary" style="width:100%" @click="onLogin">登 录</el-button>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="注册" name="reg">
            <el-form :model="regForm" label-width="60px">
              <el-form-item label="账号"><el-input v-model="regForm.username" /></el-form-item>
              <el-form-item label="密码"><el-input v-model="regForm.password" type="password" /></el-form-item>
              <el-form-item label="战队"><el-input v-model="regForm.team" placeholder="选填，自动建队" /></el-form-item>
              <el-button type="success" style="width:100%" @click="onRegister">注 册</el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>
        <p style="color:#999;font-size:12px;text-align:center">演示账号 admin / admin123</p>
      </el-card>
    </div>

    <!-- 已登录 -->
    <div v-else>
      <el-header class="header">
        <span>🚩 CTF Training Platform</span>
        <span>
          当前积分：<b style="color:#67c23a">{{ score }}</b>
          &nbsp;&nbsp;{{ username }}
          <el-button link @click="logout">退出</el-button>
        </span>
      </el-header>

      <el-container class="main">
        <el-row :gutter="16">
          <!-- 题目列表 -->
          <el-col :span="16">
            <el-card shadow="never">
              <template #header>
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <b>题目列表</b>
                  <el-radio-group v-model="filterCat" size="small">
                    <el-radio-button label="">全部</el-radio-button>
                    <el-radio-button label="web">Web</el-radio-button>
                    <el-radio-button label="misc">Misc</el-radio-button>
                    <el-radio-button label="crypto">Crypto</el-radio-button>
                    <el-radio-button label="reverse">Reverse</el-radio-button>
                  </el-radio-group>
                </div>
              </template>
              <el-table :data="filteredChallenges" border size="small" @row-click="openDetail" style="cursor:pointer">
                <el-table-column prop="id" label="#" width="50" />
                <el-table-column prop="title" label="题目" />
                <el-table-column prop="category" label="分类" width="90">
                  <template #default="s"><el-tag size="small">{{ s.row.category }}</el-tag></template>
                </el-table-column>
                <el-table-column prop="difficulty" label="难度" width="90">
                  <template #default="s">
                    <el-tag size="small" :type="diffType(s.row.difficulty)">{{ s.row.difficulty }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="score" label="分值" width="80" />
                <el-table-column label="状态" width="90">
                  <template #default="s">
                    <el-tag v-if="s.row.solved" type="success" size="small">已解出</el-tag>
                    <el-tag v-else type="info" size="small">未完成</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>

          <!-- 排行榜 -->
          <el-col :span="8">
            <el-card shadow="ner">
              <template #header><b>🏆 排行榜</b></template>
              <el-table :data="board" size="small" :show-header="true">
                <el-table-column prop="rank" label="#" width="50" />
                <el-table-column prop="username" label="选手" />
                <el-table-column prop="team" label="战队" width="100" />
                <el-table-column prop="score" label="分" width="70" />
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-container>

      <!-- 题目详情抽屉 -->
      <el-drawer v-model="drawer" :title="current.title" size="540px">
        <el-alert v-if="envUrl" type="success" :closable="false" style="margin-bottom:12px"
                  :title="`靶机环境：${envUrl}`">
          <el-button size="small" @click="openEnv(envUrl)">打开靶机</el-button>
          <el-button size="small" @click="stopEnv">关闭环境</el-button>
        </el-alert>
        <el-alert v-if="envMsg" type="warning" :closable="false" style="margin-bottom:12px" :title="envMsg" />

        <h4>题目描述</h4>
        <pre style="white-space:pre-wrap;background:#f6f8fa;padding:12px;border-radius:6px">{{ current.description }}</pre>
        <p v-if="current.static_url" style="color:#409eff">附件/链接：<a :href="current.static_url" target="_blank">{{ current.static_url }}</a></p>

        <el-divider />
        <h4>提交 Flag</h4>
        <el-input v-model="flagInput" placeholder="flag{...}" />
        <el-button type="primary" style="margin-top:10px" @click="doSubmit">提交</el-button>
        <el-button v-if="current.has_docker" style="margin-top:10px" @click="startEnv">🚀 启动环境</el-button>
      </el-drawer>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const token = ref(localStorage.getItem('token') || '')
const username = ref(localStorage.getItem('username') || '')
const score = ref(localStorage.getItem('score') || 0)
const tab = ref('login')
const loginForm = ref({ username: '', password: '' })
const regForm = ref({ username: '', password: '', team: '' })

const challenges = ref([])
const board = ref([])
const filterCat = ref('')

const drawer = ref(false)
const current = ref({})
const flagInput = ref('')
const envUrl = ref('')
const envMsg = ref('')

const filteredChallenges = computed(() =>
  challenges.value.filter(c => !filterCat.value || c.category === filterCat.value))

const onLogin = async () => {
  try {
    const { data } = await axios.post('/auth/login', loginForm.value)
    token.value = data.token
    username.value = data.username
    score.value = data.score
    localStorage.setItem('token', data.token)
    localStorage.setItem('username', data.username)
    localStorage.setItem('score', data.score)
    ElMessage.success('登录成功')
    await refresh()
  } catch (e) {
    ElMessage.error(e.response?.data?.msg || '登录失败')
  }
}

const onRegister = async () => {
  try {
    await axios.post('/auth/register', regForm.value)
    ElMessage.success('注册成功，请登录')
    tab.value = 'login'
  } catch (e) {
    ElMessage.error(e.response?.data?.msg || '注册失败')
  }
}

const logout = () => {
    localStorage.clear(); token.value=''; username.value=''; score.value=0
}

const loadChallenges = async () => {
  const { data } = await axios.get('/challenges')
  challenges.value = data
}
const loadBoard = async () => {
  const { data } = await axios.get('/scoreboard')
  board.value = data
}
const refresh = async () => { await Promise.all([loadChallenges(), loadBoard()]) }

const openDetail = async (row) => {
  const { data } = await axios.get(`/challenges/${row.id}`)
  current.value = data
  flagInput.value = ''
  envUrl.value = ''
  envMsg.value = ''
  drawer.value = true
}

const doSubmit = async () => {
  try {
    const { data } = await axios.post('/submit', {
      challenge_id: current.value.id, flag: flagInput.value
    })
    if (data.correct) {
      ElMessage.success(data.msg)
      score.value = data.score
      localStorage.setItem('score', data.score)
      drawer.value = false
      await refresh()
    } else {
      ElMessage.error(data.msg)
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.msg || '提交失败')
  }
}

const startEnv = async () => {
  const { data } = await axios.post(`/env/start/${current.value.id}`)
  if (data.url) envUrl.value = data.url
  if (data.message) envMsg.value = data.message
}
const stopEnv = async () => {
  await axios.post(`/env/stop/${current.value.id}`)
  envUrl.value = ''
  ElMessage.success('环境已关闭')
}
const openEnv = (url) => window.open(url, '_blank')

const diffType = (d) => ({ easy: 'success', medium: 'warning', hard: 'danger' }[d] || '')

onMounted(() => { if (token.value) refresh() })
</script>

<style>
body { margin: 0; background: #0f1419; color: #ddd; }
.header { background:#1a2229; color:#fff; display:flex; justify-content:space-between; align-items:center; padding:0 24px; }
.header .el-button { color:#fff; }
.main { padding:16px; }
.auth-wrap { display:flex; justify-content:center; padding-top:10vh; }
.auth-card { width:420px; background:#fff; }
.el-card { border:none; }
</style>
