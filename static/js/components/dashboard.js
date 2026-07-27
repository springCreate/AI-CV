/**
 * 仪表盘页面
 */
const DashboardPage = {
  setup() {
    const resumeCount = ref(0);
    const templateCount = ref(0);
    const jobCount = ref(0);
    const interviewCount = ref(0);
    const loading = ref(false);

    async function loadData() {
      loading.value = true;
      try {
        const [r, t, j, iq] = await Promise.all([
          API.resume.list(),
          API.template.list(),
          API.job.list({ page: 1, per_page: 1 }),
          API.interview.list({ page: 1, per_page: 1 }),
        ]);
        resumeCount.value = r.length;
        templateCount.value = t.length;
        jobCount.value = j.total;
        interviewCount.value = iq.total;
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        loading.value = false;
      }
    }

    onMounted(loadData);

    return { resumeCount, templateCount, jobCount, interviewCount, loading, loadData };
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
            <div class="stat-label">岗位数量</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-value">{{ interviewCount }}</div>
            <div class="stat-label">面试题数量</div>
          </div>
        </el-col>
      </el-row>

      <el-card class="section-card">
        <template #header><strong>快速入口</strong></template>
        <el-row :gutter="16">
          <el-col :span="6" style="text-align:center;">
            <el-button type="primary" size="large" @click="$root.handleMenuSelect('resume')">上传简历</el-button>
          </el-col>
          <el-col :span="6" style="text-align:center;">
            <el-button type="success" size="large" @click="$root.handleMenuSelect('job')">岗位匹配</el-button>
          </el-col>
          <el-col :span="6" style="text-align:center;">
            <el-button type="warning" size="large" @click="$root.handleMenuSelect('interview')">生成面试题</el-button>
          </el-col>
          <el-col :span="6" style="text-align:center;">
            <el-button size="large" @click="$root.handleMenuSelect('settings')">系统设置</el-button>
          </el-col>
        </el-row>
      </el-card>

      <el-card>
        <template #header><strong>使用指南</strong></template>
        <el-steps direction="vertical" :active="4">
          <el-step title="上传简历" description="在「我的简历」页面上传 PDF/Word 格式的简历，系统将自动解析简历内容"></el-step>
          <el-step title="设置求职诉求" description="在「求职诉求」页面创建求职诉求模板，包括期望薪资、城市、工作年限等"></el-step>
          <el-step title="录入岗位并匹配" description="在「岗位匹配」页面手动录入岗位信息，选择简历和岗位进行智能匹配"></el-step>
          <el-step title="生成面试题" description="在「面试题库」页面选择简历和岗位，AI 将根据岗位JD和简历生成面试官可能提问的问题清单"></el-step>
        </el-steps>
      </el-card>
    </div>
  `
};
