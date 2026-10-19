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
              <el-form-item label="战队"><el-input v-model="regForm.team" placeholder="选填" /></el-form-item>
              <el-button type="success" style="width:100%" @click="onRegister">注 册</el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>
        <p style="color:#999;font-size:12px;text-align:center">演示账号 admin / admin123</p>
      </el-card>
    </div>

    <div v-else>
      <!-- 顶部 -->
      <el-header class="header">
        <span>🚩 {{ contest.name || 'CTF' }}</span>
        <span>
          <el-button v-if="role==='admin'" link @click="adminDialog=true">🛠 管理后台</el-button>
          <el-button link @click="showMe">👤 我的数据</el-button>
          积分：<b style="color:#67c23a">{{ score }}</b> {{ username }}
          <el-button link @click="logout">退出</el-button>
        </span>
      </el-header>

      <!-- 倒计时 -->
      <div v-if="contest.end_time" class="countdown">
        ⏳ 距离比赛结束：<b>{{ countdown }}</b>
      </div>

      <!-- 公告 -->
      <el-alert v-for="a in announcements" :key="a.id" :title="`[${a.title}] ${a.content}`"
                type="warning" :closable="false" style="margin:8px 16px" />

      <el-container class="main">
        <el-row :gutter="16">
          <el-col :span="16">
            <el-card shadow="never">
              <template #header>
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
                  <b>题目（共 {{ challenges.length }} 题）</b>
                  <el-input v-model="kw" size="small" placeholder="搜索题目..." style="width:200px" />
                  <el-radio-group v-model="filterCat" size="small">
                    <el-radio-button label="">全部</el-radio-button>
                    <el-radio-button label="web">Web</el-radio-button>
                    <el-radio-button label="misc">Misc</el-radio-button>
                    <el-radio-button label="crypto">Crypto</el-radio-button>
                    <el-radio-button label="reverse">Reverse</el-radio-button>
                  </el-radio-group>
                </div>
              </template>
              <el-table :data="filtered" border size="small" @row-click="openDetail" style="cursor:pointer">
                <el-table-column prop="id" label="#" width="50" />
                <el-table-column prop="title" label="题目">
                  <template #default="s">
                    {{ s.row.title }}
                    <el-tag v-if="s.row.bloods && s.row.bloods.length" size="mini" type="danger" style="margin-left:6px">
                      🩸 {{ s.row.bloods[0] }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="category" label="分类" width="80">
                  <template #default="s"><el-tag size="small">{{ s.row.category }}</el-tag></template>
                </el-table-column>
                <el-table-column prop="difficulty" label="难度" width="80">
                  <template #default="s"><el-tag size="small" :type="diffType(s.row.difficulty)">{{ s.row.difficulty }}</el-tag></template>
                </el-table-column>
                <el-table-column prop="score" label="当前分" width="80" />
                <el-table-column label="" width="60">
                  <template #default="s">
                    <el-tag v-if="s.row.solved" type="success" size="small">✓</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>

          <el-col :span="8">
            <el-card shadow="never">
              <template #header><b>🏆 排行榜</b>
                <el-button size="small" link @click="exportBoard">导出CSV</el-button>
              </template>
              <el-table :data="board" size="small" max-height="500">
                <el-table-column prop="rank" label="#" width="50" />
                <el-table-column prop="username" label="选手" />
                <el-table-column prop="score" label="分" width="70" />
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-container>

      <!-- 题目详情 -->
      <el-drawer v-model="drawer" :title="current.title" size="600px">
        <el-alert v-if="current.external_url" type="primary" :closable="false" style="margin-bottom:10px">
          靶机：<a :href="current.external_url" target="_blank">{{ current.external_url }}</a>
        </el-alert>
        <el-alert v-if="envUrl" type="success" :closable="false" style="margin-bottom:10px">
          环境：{{ envUrl }}
          <el-button size="small" @click="openEnv(envUrl)">打开</el-button>
          <el-button size="small" @click="renewEnv">续期</el-button>
          <el-button size="small" @click="stopEnv">关闭</el-button>
        </el-alert>

        <h4>题目描述</h4>
        <pre style="white-space:pre-wrap;background:#f6f8fa;padding:10px">{{ current.description }}</pre>

        <div v-if="current.attachments?.length">
          <el-button v-for="a in current.attachments" :key="a.id" size="small" @click="downloadAttach(a.id)">
            📎 {{ a.filename }}
          </el-button>
        </div>

        <el-divider />
        <h4>提示（购买扣分）</h4>
        <div v-for="h in current.hints" :key="h.id" style="margin-bottom:8px">
          <span v-if="h.bought">{{ h.content }}</span>
          <el-button v-else size="small" @click="buyHint(h.id)">花 {{ h.cost }} 分买提示</el-button>
        </div>

        <el-divider />
        <el-input v-model="flagInput" placeholder="flag{...}" />
        <el-button type="primary" style="margin-top:8px" @click="doSubmit">提交</el-button>
        <el-button v-if="current.has_docker" style="margin-top:8px" @click="startEnv">🚀 启动环境</el-button>

        <el-divider />
        <h4>讨论区</h4>
        <el-input v-model="commentText" placeholder="友好讨论，禁止发 flag" />
        <el-button size="small" style="margin-top:6px" @click="postComment">发送</el-button>
        <div v-for="c in comments" :key="c.id" style="margin-top:8px;font-size:13px">
          <b :style="{color: c.is_admin ? '#e6a23c' : '#409eff'}">{{ c.username }}</b>
          <span style="color:#999;margin:0 6px">{{ c.created_at }}</span>
          <div>{{ c.content }}</div>
        </div>
      </el-drawer>

      <!-- 我的数据 -->
      <el-dialog v-model="meDialog" title="👤 我的解题数据" width="500px">
        <div ref="radarRef" style="width:100%;height:300px"></div>
      </el-dialog>

      <!-- 管理员 -->
      <el-dialog v-model="adminDialog" title="🛠 管理员" width="600px">
        <el-tabs v-model="adminTab">
          <el-tab-pane label="比赛设置" name="contest">
            <el-form :model="contestForm" label-width="100px">
              <el-form-item label="赛事名"><el-input v-model="contestForm.name" /></el-form-item>
              <el-form-item label="开始时间"><el-input v-model="contestForm.start_time" placeholder="2026-01-01 09:00:00" /></el-form-item>
              <el-form-item label="结束时间"><el-input v-model="contestForm.end_time" placeholder="2026-01-02 18:00:00" /></el-form-item>
              <el-button type="primary" @click="saveContest">保存</el-button>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="发布公告" name="anno">
            <el-form :model="annoForm" label-width="80px">
              <el-form-item label="标题"><el-input v-model="annoForm.title" /></el-form-item>
              <el-form-item label="内容"><el-input v-model="annoForm.content" type="textarea" /></el-form-item>
              <el-button type="primary" @click="postAnno">发布</el-button>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="新建题目" name="new">
            <el-form :model="newCh" label-width="100px">
              <el-form-item label="标题"><el-input v-model="newCh.title" /></el-form-item>
              <el-form-item label="分类">
                <el-select v-model="newCh.category">
                  <el-option v-for="c in ['web','misc','crypto','reverse']" :key="c" :label="c" :value="c" />
                </el-select>
              </el-form-item>
              <el-form-item label="难度">
                <el-select v-model="newCh.difficulty">
                  <el-option v-for="d in ['easy','medium','hard']" :key="d" :label="d" :value="d" />
                </el-select>
              </el-form-item>
              <el-form-item label="起始分"><el-input v-model.number="newCh.base_score" type="number" /></el-form-item>
              <el-form-item label="最低分"><el-input v-model.number="newCh.min_score" type="number" /></el-form-item>
              <el-form-item label="Flag"><el-input v-model="newCh.flag" /></el-form-item>
              <el-form-item label="描述"><el-input v-model="newCh.description" type="textarea" :rows="3" /></el-form-item>
              <el-form-item label="外部URL"><el-input v-model="newCh.external_url" /></el-form-item>
              <el-button type="primary" @click="createChallenge">创建</el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const token = ref(localStorage.getItem('token') || '')
const username = ref(localStorage.getItem('username') || '')
const score = ref(localStorage.getItem('score') || 0)
const role = ref(localStorage.getItem('role') || 'user')
const tab = ref('login')
const loginForm = ref({ username: '', password: '' })
const regForm = ref({ username: '', password: '', team: '' })

const challenges = ref([]), board = ref([]), announcements = ref([])
const filterCat = ref(''), kw = ref('')
const contest = ref({}), countdown = ref('')
let timer = null

const drawer = ref(false), current = ref({}), flagInput = ref('')
const envUrl = ref(''), commentText = ref(''), comments = ref([])
const meDialog = ref(false), radarRef = ref(null)
const adminDialog = ref(false), adminTab = ref('contest')
const contestForm = ref({ name: '', start_time: '', end_time: '' })
const annoForm = ref({ title: '', content: '' })
const newCh = ref({ title:'', category:'web', difficulty:'easy', base_score:500,
                    min_score:100, flag:'', description:'', external_url:'' })

const filtered = computed(() => challenges.value.filter(c =>
  (!filterCat.value || c.category === filterCat.value) &&
  (!kw.value || c.title.toLowerCase().includes(kw.value.toLowerCase()))))

const onLogin = async () => {
  try {
    const { data } = await axios.post('/auth/login', loginForm.value)
    Object.assign(localStorage, { token:data.token, username:data.username, score:data.score, role:data.role })
    token.value=data.token; username.value=data.username; score.value=data.score; role.value=data.role
    ElMessage.success('登录成功'); await refresh()
  } catch (e) { ElMessage.error(e.response?.data?.msg || '登录失败') }
}
const onRegister = async () => {
  try { await axios.post('/auth/register', regForm.value); ElMessage.success('注册成功'); tab.value='login' }
  catch (e) { ElMessage.error(e.response?.data?.msg || '注册失败') }
}
const logout = () => { localStorage.clear(); token.value=''; role.value='user' }

const refresh = async () => {
  const [c, b, a, ct] = await Promise.all([
    axios.get('/challenges'), axios.get('/scoreboard'),
    axios.get('/announcements'), axios.get('/contest')
  ])
  challenges.value=c.data; board.value=b.data; announcements.value=a.data; contest.value=ct.data
}

const openDetail = async (row) => {
  current.value = (await axios.get(`/challenges/${row.id}`)).data
  comments.value = (await axios.get(`/comment/${row.id}`)).data
  flagInput = ''; envUrl.value = ''; commentText.value = ''
  drawer.value = true
}

const doSubmit = async () => {
  try {
    const { data } = await axios.post('/submit', { challenge_id: current.value.id, flag: flagInput })
    if (data.correct) { ElMessage.success(data.msg); score.value=data.score; localStorage.setItem('score', data.score); drawer.value=false; await refresh() }
    else ElMessage.error(data.msg)
  } catch (e) { ElMessage.error(e.response?.data?.msg || '提交失败') }
}

const buyHint = async (hid) => {
  const { data } = await axios.post(`/hint/buy/${hid}`)
  ElMessage.success(data.msg); await openDetail(current.value)
}

const postComment = async () => {
  await axios.post(`/comment/${current.value.id}`, { content: commentText.value })
  commentText.value = ''
  comments.value = (await axios.get(`/comment/${current.value.id}`)).data
}

const startEnv = async () => {
  const { data } = await axios.post(`/env/start/${current.value.id}`)
  if (data.url) envUrl.value = data.url
  if (data.message) ElMessage.warning(data.message)
}
const stopEnv = async () => { await axios.post(`/env/stop/${current.value.id}`); envUrl.value='' }
const renewEnv = async () => { await axios.post('/env/renew'); ElMessage.success('已续期') }
const openEnv = (u) => window.open(u, '_blank')
const downloadAttach = async (fid) => {
  const res = await axios.get(`/attachment/${fid}`, { responseType:'blob' })
  const a = document.createElement('a'); a.href=URL.createObjectURL(new Blob([res.data])); a.click()
}

const exportBoard = async () => {
  const res = await axios.get('/admin/scoreboard/export', { responseType:'blob' })
  const a = document.createElement('a'); a.href=URL.createObjectURL(new Blob([res.data])); a.download='scoreboard.csv'; a.click()
}

const saveContest = async () => { await axios.post('/admin/contest', contestForm.value); ElMessage.success('已保存') }
const postAnno = async () => { await axios.post('/admin/announcement', annoForm.value); ElMessage.success('已发布'); annoForm.value={title:'',content:''}; await refresh() }
const createChallenge = async () => { await axios.post('/admin/challenge', newCh.value); ElMessage.success('已创建'); adminDialog.value=false; await refresh() }

const showMe = async () => {
  meDialog.value = true
  const { data } = await axios.get('/me')
  await nextTick()
  const chart = echarts.init(radarRef.value)
  chart.setOption({
    title: { text: '我的解题分布', left: 'center' },
    radar: { indicator: ['web','misc','crypto','reverse'].map(c => ({ name:c, max:10 })) },
    series: [{ type:'radar', data:[{ value:['web','misc','crypto','reverse'].map(c => data.by_category[c]||0), name:'做题数' }] }]
  })
}
// 把 meDialog 打开按钮接上
window.__showMe = showMe

const diffType = (d) => ({ easy:'success', medium:'warning', hard:'danger' }[d]||'')

// 倒计时
const tick = () => {
  if (!contest.value.end_time) return
  const end = new Date(contest.value.end_time.replace(' ', 'T'))
  const diff = end - new Date()
  if (diff <= 0) { countdown.value = '比赛已结束'; return }
  const h = Math.floor(diff/3600000), m = Math.floor(diff%3600000/60000), s = Math.floor(diff%60000/1000)
  countdown.value = `${h}时 ${m}分 ${s}秒`
}

onMounted(() => {
  if (token.value) { refresh(); timer = setInterval(tick, 1000) }
})
onBeforeUnmount(() => timer && clearInterval(timer)
</script>

<style>
body { margin:0; background:#0f1419; color:#ddd; }
.header { background:#1a2229; color:#fff; display:flex; justify-content:space-between; align-items:center; padding:0 24px; }
.header .el-button { color:#fff; }
.countdown { background:#3a2a1a; color:#ffb866; text-align:center; padding:6px; font-size:15px; }
.main { padding:16px; }
.auth-wrap { display:flex; justify-content:center; padding-top:10vh; }
.auth-card { width:420px; background:#fff; }
.el-card { border:none; }
</style>
