/**
 * 岗位匹配页面
 */
const JobPage = {
  setup() {
    const activeTab = ref('match');
    const loading = ref(false);
    const fetchLoading = ref(false);

    // 拉取匹配表单
    const fetchForm = ref({ resume_id: null, template_id: null, keyword: '', city: '' });
    const resumes = ref([]);
    const templates = ref([]);
    const lastResult = ref(null);

    // 匹配记录
    const records = ref([]);
    const recordsTotal = ref(0);
    const recordsPage = ref(1);
    const recordsPerPage = ref(20);
    const recordsFilter = ref({ only_passed: true, min_score: null, template_id: null });

    // 岗位列表
    const jobs = ref([]);
    const jobsTotal = ref(0);
    const jobsPage = ref(1);
    const jobsFilter = ref({ platform: '', city: '', keyword: '' });

    // 详情
    const detailDialog = ref(false);
    const currentJob = ref(null);

    async function loadOptions() {
      try {
        const [r, t] = await Promise.all([API.resume.list(), API.template.list()]);
        resumes.value = r;
        templates.value = t;
        // 默认选中第一个简历和默认模板
        if (r.length && !fetchForm.value.resume_id) fetchForm.value.resume_id = r[0].id;
        const def = t.find(x => x.is_default);
        if (def && !fetchForm.value.template_id) fetchForm.value.template_id = def.id;
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function fetchAndMatch() {
      if (!fetchForm.value.resume_id && resumes.value.length) fetchForm.value.resume_id = resumes.value[0].id;
      if (!fetchForm.value.template_id && templates.value.length) fetchForm.value.template_id = templates.value[0].id;
      if (!fetchForm.value.resume_id || !fetchForm.value.template_id) {
        ElMessage.warning('请选择简历和求职诉求模板');
        return;
      }
      fetchLoading.value = true;
      try {
        const data = await API.job.fetchMatch({
          resume_id: fetchForm.value.resume_id,
          template_id: fetchForm.value.template_id,
          keyword: fetchForm.value.keyword,
          city: fetchForm.value.city,
        });
        lastResult.value = data;
        ElMessage.success(`拉取 ${data.total_fetched} 个岗位，新增 ${data.new_saved}，高匹配 ${data.high_match_count}`);
        if (data.is_mock_mode) {
          ElMessage.warning('当前为演示模式，使用 Mock 数据');
        }
        await loadRecords();
        activeTab.value = 'match';
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        fetchLoading.value = false;
      }
    }

    async function loadRecords() {
      loading.value = true;
      try {
        const params = {
          page: recordsPage.value,
          per_page: recordsPerPage.value,
          only_passed: recordsFilter.value.only_passed ? 'true' : 'false',
        };
        if (recordsFilter.value.min_score) params.min_score = recordsFilter.value.min_score;
        if (recordsFilter.value.template_id) params.template_id = recordsFilter.value.template_id;
        const data = await API.job.matchRecords(params);
        records.value = data.items;
        recordsTotal.value = data.total;
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        loading.value = false;
      }
    }

    async function loadJobs() {
      loading.value = true;
      try {
        const params = { page: jobsPage.value, per_page: recordsPerPage.value };
        if (jobsFilter.value.platform) params.platform = jobsFilter.value.platform;
        if (jobsFilter.value.city) params.city = jobsFilter.value.city;
        if (jobsFilter.value.keyword) params.keyword = jobsFilter.value.keyword;
        const data = await API.job.list(params);
        jobs.value = data.items;
        jobsTotal.value = data.total;
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        loading.value = false;
      }
    }

    function viewJob(job) {
      currentJob.value = job;
      detailDialog.value = true;
    }

    async function deleteJob(job) {
      try {
        await ElMessageBox.confirm(`确定删除岗位「${job.title}」？`, '提示', { type: 'warning' });
        await API.job.delete(job.id);
        ElMessage.success('已删除');
        await loadJobs();
      } catch (e) {
        if (e !== 'cancel' && e.message) ElMessage.error(e.message);
      }
    }

    function scoreClass(score) {
      if (score >= 80) return 'score-high';
      if (score >= 60) return 'score-mid';
      return 'score-low';
    }

    function openJobUrl(url) {
      if (url) window.open(url, '_blank');
    }

    function handleTabChange(tab) {
      if (tab === 'match') loadRecords();
      else if (tab === 'jobs') loadJobs();
    }

    onMounted(async () => {
      await loadOptions();
      await loadRecords();
    });

    return {
      activeTab, loading, fetchLoading,
      fetchForm, resumes, templates, lastResult,
      records, recordsTotal, recordsPage, recordsPerPage, recordsFilter,
      jobs, jobsTotal, jobsPage, jobsFilter,
      detailDialog, currentJob,
      loadOptions, fetchAndMatch, loadRecords, loadJobs,
      viewJob, deleteJob, scoreClass, openJobUrl, handleTabChange,
    };
  },
  template: `
    <div>
      <div class="page-title">岗位匹配
        <el-button type="primary" @click="fetchAndMatch" :loading="fetchLoading">
          <el-icon><Refresh /></el-icon> 一键拉取并匹配
        </el-button>
      </div>

      <el-card class="section-card">
        <el-form :model="fetchForm" label-width="120px" :inline="true">
          <el-form-item label="选择简历">
            <el-select v-model="fetchForm.resume_id" placeholder="请选择" style="width:200px;">
              <el-option v-for="r in resumes" :key="r.id" :label="r.name" :value="r.id"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="求职诉求">
            <el-select v-model="fetchForm.template_id" placeholder="请选择" style="width:200px;">
              <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input v-model="fetchForm.keyword" placeholder="默认用模板岗位" style="width:160px;"></el-input>
          </el-form-item>
          <el-form-item label="城市">
            <el-input v-model="fetchForm.city" placeholder="默认用模板城市" style="width:120px;"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchAndMatch" :loading="fetchLoading">开始拉取</el-button>
          </el-form-item>
        </el-form>
        <el-alert v-if="lastResult" type="success" :closable="false" style="margin-top:8px;">
          本次拉取 {{ lastResult.total_fetched }} 个岗位，新增 {{ lastResult.new_saved }}，匹配 {{ lastResult.total_matched }}，高匹配度（≥80分）{{ lastResult.high_match_count }} 个
        </el-alert>
      </el-card>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="匹配记录" name="match">
          <div style="margin-bottom:12px;display:flex;gap:12px;align-items:center;">
            <el-checkbox v-model="recordsFilter.only_passed" @change="loadRecords">仅显示通过硬性过滤</el-checkbox>
            <el-input-number v-model="recordsFilter.min_score" :min="0" :max="100" placeholder="最低分数" @change="loadRecords" style="width:120px;"></el-input-number>
            <el-select v-model="recordsFilter.template_id" placeholder="按模板筛选" clearable @change="loadRecords" style="width:200px;">
              <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id"></el-option>
            </el-select>
            <el-button @click="loadRecords"><el-icon><Refresh /></el-icon> 刷新</el-button>
          </div>

          <el-table :data="records" v-loading="loading" border size="small">
            <el-table-column label="匹配分" width="80">
              <template #default="{ row }">
                <span :class="['score-badge', scoreClass(row.match_score)]">{{ row.match_score }}</span>
              </template>
            </el-table-column>
            <el-table-column label="公司" prop="job.company" min-width="120"></el-table-column>
            <el-table-column label="岗位" prop="job.title" min-width="140"></el-table-column>
            <el-table-column label="城市" prop="job.city" width="80"></el-table-column>
            <el-table-column label="薪资" prop="job.salary_text" width="100"></el-table-column>
            <el-table-column label="平台" prop="job.platform" width="80">
              <template #default="{ row }">
                <el-tag size="small">{{ row.job.platform }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="硬性过滤" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.hard_filter_passed" type="success" size="small">通过</el-tag>
                <el-tooltip v-else :content="row.hard_filter_reason" placement="top">
                  <el-tag type="danger" size="small">未通过</el-tag>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="匹配摘要" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <span style="font-size:12px;color:#4a5568;">{{ row.match_summary }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewJob(row.job)">详情</el-button>
                <el-button size="small" type="primary" @click="openJobUrl(row.job.job_url)">跳转</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="recordsPage"
            :page-size="recordsPerPage"
            :total="recordsTotal"
            layout="total, prev, pager, next"
            @current-change="loadRecords"
            style="margin-top:16px;justify-content:flex-end;display:flex;"></el-pagination>
        </el-tab-pane>

        <el-tab-pane label="全部岗位" name="jobs">
          <div style="margin-bottom:12px;display:flex;gap:12px;">
            <el-select v-model="jobsFilter.platform" placeholder="平台" clearable @change="loadJobs" style="width:120px;">
              <el-option label="BOSS直聘" value="boss"></el-option>
              <el-option label="智联招聘" value="zhilian"></el-option>
              <el-option label="前程无忧" value="51job"></el-option>
              <el-option label="实习僧" value="shixiseng"></el-option>
              <el-option label="演示数据" value="mock"></el-option>
            </el-select>
            <el-input v-model="jobsFilter.city" placeholder="城市" clearable @change="loadJobs" style="width:120px;"></el-input>
            <el-input v-model="jobsFilter.keyword" placeholder="公司/岗位关键词" clearable @change="loadJobs" style="width:200px;"></el-input>
            <el-button @click="loadJobs"><el-icon><Refresh /></el-icon> 刷新</el-button>
          </div>

          <el-table :data="jobs" v-loading="loading" border size="small">
            <el-table-column label="公司" prop="company" min-width="120"></el-table-column>
            <el-table-column label="岗位" prop="title" min-width="140"></el-table-column>
            <el-table-column label="城市" prop="city" width="80"></el-table-column>
            <el-table-column label="薪资" prop="salary_text" width="100"></el-table-column>
            <el-table-column label="年限" prop="work_years" width="80"></el-table-column>
            <el-table-column label="学历" prop="education" width="80"></el-table-column>
            <el-table-column label="平台" prop="platform" width="80"></el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewJob(row)">详情</el-button>
                <el-button size="small" type="primary" @click="openJobUrl(row.job_url)">跳转</el-button>
                <el-button size="small" type="danger" @click="deleteJob(row)"><el-icon><Delete /></el-icon></el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="jobsPage"
            :page-size="recordsPerPage"
            :total="jobsTotal"
            layout="total, prev, pager, next"
            @current-change="loadJobs"
            style="margin-top:16px;justify-content:flex-end;display:flex;"></el-pagination>
        </el-tab-pane>
      </el-tabs>

      <el-dialog v-model="detailDialog" title="岗位详情" width="700px">
        <div v-if="currentJob">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="公司">{{ currentJob.company }}</el-descriptions-item>
            <el-descriptions-item label="岗位">{{ currentJob.title }}</el-descriptions-item>
            <el-descriptions-item label="城市">{{ currentJob.city }} {{ currentJob.district }}</el-descriptions-item>
            <el-descriptions-item label="薪资">{{ currentJob.salary_text }}</el-descriptions-item>
            <el-descriptions-item label="工作年限">{{ currentJob.work_years }}</el-descriptions-item>
            <el-descriptions-item label="学历">{{ currentJob.education }}</el-descriptions-item>
            <el-descriptions-item label="工作类型">{{ currentJob.job_type }}</el-descriptions-item>
            <el-descriptions-item label="平台">{{ currentJob.platform }}</el-descriptions-item>
            <el-descriptions-item label="公司规模">{{ currentJob.company_size }}</el-descriptions-item>
            <el-descriptions-item label="公司行业">{{ currentJob.company_industry }}</el-descriptions-item>
            <el-descriptions-item label="HR">{{ currentJob.hr_name }}</el-descriptions-item>
            <el-descriptions-item label="发布时间">{{ currentJob.publish_time }}</el-descriptions-item>
            <el-descriptions-item label="双休" :span="1">{{ currentJob.is_weekend_off ? '是' : '否' }}</el-descriptions-item>
            <el-descriptions-item label="包住宿">{{ currentJob.has_accommodation ? '是' : '否' }}</el-descriptions-item>
          </el-descriptions>
          <el-divider content-position="left">岗位 JD</el-divider>
          <div class="jd-text">{{ currentJob.jd_text }}</div>
          <div v-if="currentJob.job_url" style="margin-top:16px;text-align:center;">
            <el-button type="primary" @click="openJobUrl(currentJob.job_url)">
              <el-icon><Link /></el-icon> 打开岗位原链接
            </el-button>
          </div>
        </div>
      </el-dialog>
    </div>
  `
};
