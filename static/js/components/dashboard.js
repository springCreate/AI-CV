/**
 * 仪表盘页面
 */
const DashboardPage = {
  setup() {
    const stats = ref({ total: 0, applied: 0, interviewing: 0, offered: 0, rejected: 0, not_applied: 0, trend_7d: [] });
    const resumeCount = ref(0);
    const templateCount = ref(0);
    const jobCount = ref(0);
    const loading = ref(false);

    async function loadData() {
      loading.value = true;
      try {
        const [s, r, t, j] = await Promise.all([
          API.application.stats(),
          API.resume.list(),
          API.template.list(),
          API.job.list({ page: 1, per_page: 1 }),
        ]);
        stats.value = s;
        resumeCount.value = r.length;
        templateCount.value = t.length;
        jobCount.value = j.total;
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        loading.value = false;
      }
    }

    onMounted(loadData);

    return { stats, resumeCount, templateCount, jobCount, loading, loadData };
  },
  template: `
    <div v-loading="loading">
      <div class="page-title">仪表盘
        <el-button type="primary" size="small" @click="loadData"><el-icon><Refresh /></el-icon> 刷新</el-button>
      </div>

      <el-row :gutter="16" class="section-card">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-value">{{ resumeCount }}</div>
            <div class="stat-label">简历数量</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-value">{{ templateCount }}</div>
            <div class="stat-label">求职诉求模板</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-value">{{ jobCount }}</div>
            <div class="stat-label">缓存岗位数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-value">{{ stats.applied }}</div>
            <div class="stat-label">已投递岗位</div>
          </div>
        </el-col>
      </el-row>

      <el-card class="section-card">
        <template #header><strong>投递状态分布</strong></template>
        <el-row :gutter="16">
          <el-col :span="4"><div class="stat-card"><div class="stat-value" style="color:#718096;">{{ stats.not_applied }}</div><div class="stat-label">未投递</div></div></el-col>
          <el-col :span="4"><div class="stat-card"><div class="stat-value" style="color:#3182ce;">{{ stats.applied }}</div><div class="stat-label">已投递</div></div></el-col>
          <el-col :span="4"><div class="stat-card"><div class="stat-value" style="color:#d69e2e;">{{ stats.interviewing }}</div><div class="stat-label">面试中</div></div></el-col>
          <el-col :span="4"><div class="stat-card"><div class="stat-value" style="color:#38a169;">{{ stats.offered }}</div><div class="stat-label">Offer</div></div></el-col>
          <el-col :span="4"><div class="stat-card"><div class="stat-value" style="color:#e53e3e;">{{ stats.rejected }}</div><div class="stat-label">已拒绝</div></div></el-col>
          <el-col :span="4"><div class="stat-card"><div class="stat-value" style="color:#805ad5;">{{ stats.total }}</div><div class="stat-label">总记录</div></div></el-col>
        </el-row>
      </el-card>

      <el-card>
        <template #header><strong>近 7 日投递趋势</strong></template>
        <div v-if="stats.trend_7d && stats.trend_7d.length" style="display:flex;align-items:flex-end;height:200px;gap:12px;padding:0 20px;">
          <div v-for="item in stats.trend_7d" :key="item.date" style="flex:1;text-align:center;">
            <div :style="{height: (item.count * 30 + 10) + 'px', background:'linear-gradient(180deg,#4299e1,#3182ce)',borderRadius:'6px 6px 0 0',transition:'all 0.3s'}"></div>
            <div style="font-size:12px;color:#718096;margin-top:8px;">{{ item.count }}</div>
            <div style="font-size:11px;color:#a0aec0;margin-top:2px;">{{ item.date.slice(5) }}</div>
          </div>
        </div>
        <div v-else class="empty-state">暂无数据</div>
      </el-card>
    </div>
  `
};
