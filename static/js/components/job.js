/**
 * 岗位匹配页面
 */
const JobPage = {
  setup() {
    const activeTab = ref('jobs');
    const loading = ref(false);

    // 匹配表单
    const matchForm = ref({ resume_id: null, job_id: null, template_id: null });
    const resumes = ref([]);
    const templates = ref([]);
    const jobs = ref([]);
    const matchResult = ref(null);
    const matchLoading = ref(false);

    // 匹配记录
    const records = ref([]);
    const recordsTotal = ref(0);
    const recordsPage = ref(1);
    const recordsPerPage = ref(20);
    const recordsFilter = ref({ only_passed: true, min_score: null });

    // 岗位列表
    const jobsTotal = ref(0);
    const jobsPage = ref(1);
    const jobsFilter = ref({ city: '', keyword: '' });

    // 手动录入岗位
    const createDialog = ref(false);
    const createForm = ref({
      title: '', company: '', city: '', district: '',
      salary_min: null, salary_max: null, salary_text: '',
      work_years: '', education: '', job_type: '全职',
      is_weekend_off: null, has_accommodation: null,
      jd_text: '', company_size: '', company_industry: '',
      hr_name: '', job_url: ''
    });
    const createLoading = ref(false);

    // 详情
    const detailDialog = ref(false);
    const currentJob = ref(null);

    async function loadOptions() {
      try {
        const [r, t, j] = await Promise.all([API.resume.list(), API.template.list(), API.job.list({ per_page: 100 })]);
        resumes.value = r;
        templates.value = t;
        jobs.value = j.items || [];
        if (r.length && !matchForm.value.resume_id) matchForm.value.resume_id = r[0].id;
        const def = t.find(x => x.is_default);
        if (def && !matchForm.value.template_id) matchForm.value.template_id = def.id;
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function startMatch() {
      if (!matchForm.value.resume_id) {
        ElMessage.warning('请选择简历');
        return;
      }
      if (!matchForm.value.job_id) {
        ElMessage.warning('请选择岗位');
        return;
      }
      if (!matchForm.value.template_id) {
        ElMessage.warning('请选择求职诉求模板');
        return;
      }
      matchLoading.value = true;
      try {
        const data = await API.job.match({
          resume_id: matchForm.value.resume_id,
          job_id: matchForm.value.job_id,
          template_id: matchForm.value.template_id,
        });
        matchResult.value = data;
        ElMessage.success(`匹配完成，得分 ${data.match_score}`);
        await loadRecords();
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        matchLoading.value = false;
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

    function openCreateDialog() {
      createForm.value = {
        title: '', company: '', city: '', district: '',
        salary_min: null, salary_max: null, salary_text: '',
        work_years: '', education: '', job_type: '全职',
        is_weekend_off: null, has_accommodation: null,
        jd_text: '', company_size: '', company_industry: '',
        hr_name: '', job_url: ''
      };
      createDialog.value = true;
    }

    async function submitCreateJob() {
      if (!createForm.value.title || !createForm.value.company || !createForm.value.job_url) {
        ElMessage.warning('岗位名称、公司和原链接为必填项');
        return;
      }
      createLoading.value = true;
      try {
        await API.job.create(createForm.value);
        ElMessage.success('岗位录入成功');
        createDialog.value = false;
        await loadJobs();
        await loadOptions();
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        createLoading.value = false;
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
      await loadJobs();
    });

    return {
      activeTab, loading,
      matchForm, resumes, templates, jobs, matchResult, matchLoading,
      records, recordsTotal, recordsPage, recordsPerPage, recordsFilter,
      jobsTotal, jobsPage, jobsFilter,
      detailDialog, currentJob,
      createDialog, createForm, createLoading,
      loadOptions, startMatch, loadRecords, loadJobs,
      viewJob, deleteJob, scoreClass, openJobUrl, handleTabChange,
      openCreateDialog, submitCreateJob,
    };
  },
  template: `
    <div>
      <div class="page-title">岗位匹配</div>

      <el-card class="section-card">
        <template #header><strong>智能匹配</strong></template>
        <el-form :model="matchForm" label-width="100px" :inline="true">
          <el-form-item label="选择简历" required>
            <el-select v-model="matchForm.resume_id" placeholder="请选择" style="width:200px;">
              <el-option v-for="r in resumes" :key="r.id" :label="r.name" :value="r.id"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="选择岗位" required>
            <el-select v-model="matchForm.job_id" placeholder="请选择" style="width:280px;" filterable>
              <el-option v-for="j in jobs" :key="j.id" :label="j.company + ' - ' + j.title" :value="j.id"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="求职诉求" required>
            <el-select v-model="matchForm.template_id" placeholder="请选择" style="width:180px;">
              <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="startMatch" :loading="matchLoading">开始匹配</el-button>
          </el-form-item>
        </el-form>

        <div v-if="matchResult" style="margin-top:16px;">
          <el-divider content-position="left">匹配结果</el-divider>
          <div style="display:flex;gap:24px;">
            <div style="text-align:center;">
              <div :class="['score-display', scoreClass(matchResult.match_score)]">{{ matchResult.match_score }}</div>
              <div style="font-size:12px;color:#718096;margin-top:4px;">匹配度</div>
            </div>
            <div style="flex:1;">
              <div style="font-weight:bold;margin-bottom:8px;">{{ matchResult.job?.company }} - {{ matchResult.job?.title }}</div>
              <div style="font-size:14px;color:#2d3748;">{{ matchResult.match_summary }}</div>
              <div v-if="matchResult.skill_suggestions && matchResult.skill_suggestions.length" style="margin-top:12px;">
                <el-tag type="warning" size="small" style="margin-right:8px;">技能提升建议</el-tag>
                <ul style="margin-top:8px;padding-left:20px;">
                  <li v-for="(s, idx) in matchResult.skill_suggestions" :key="idx" style="font-size:13px;color:#e53e3e;margin-bottom:4px;">{{ s }}</li>
                </ul>
              </div>
              <div v-if="matchResult.missing_skills && matchResult.missing_skills.length" style="margin-top:12px;">
                <el-tag type="danger" size="small" style="margin-right:8px;">缺失技能</el-tag>
                <span v-for="(s, idx) in matchResult.missing_skills" :key="idx" style="margin-right:8px;">
                  <el-tag size="small">{{ s }}</el-tag>
                </span>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="匹配记录" name="match">
          <div style="margin-bottom:12px;display:flex;gap:12px;align-items:center;">
            <el-checkbox v-model="recordsFilter.only_passed" @change="loadRecords">仅显示通过硬性过滤</el-checkbox>
            <el-input-number v-model="recordsFilter.min_score" :min="0" :max="100" placeholder="最低分数" @change="loadRecords" style="width:120px;"></el-input-number>
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
            <el-input v-model="jobsFilter.city" placeholder="城市" clearable @change="loadJobs" style="width:120px;"></el-input>
            <el-input v-model="jobsFilter.keyword" placeholder="公司/岗位关键词" clearable @change="loadJobs" style="width:200px;"></el-input>
            <el-button @click="loadJobs"><el-icon><Refresh /></el-icon> 刷新</el-button>
            <el-button type="primary" @click="openCreateDialog"><el-icon><Plus /></el-icon> 手动录入岗位</el-button>
          </div>

          <el-table :data="jobs" v-loading="loading" border size="small">
            <el-table-column label="公司" prop="company" min-width="120"></el-table-column>
            <el-table-column label="岗位" prop="title" min-width="140"></el-table-column>
            <el-table-column label="城市" prop="city" width="80"></el-table-column>
            <el-table-column label="薪资" prop="salary_text" width="100"></el-table-column>
            <el-table-column label="年限" prop="work_years" width="80"></el-table-column>
            <el-table-column label="学历" prop="education" width="80"></el-table-column>
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
            <el-descriptions-item label="公司规模">{{ currentJob.company_size }}</el-descriptions-item>
            <el-descriptions-item label="公司行业">{{ currentJob.company_industry }}</el-descriptions-item>
            <el-descriptions-item label="HR">{{ currentJob.hr_name }}</el-descriptions-item>
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

      <el-dialog v-model="createDialog" title="手动录入岗位" width="680px">
        <el-form :model="createForm" label-width="100px">
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="岗位名称" required>
                <el-input v-model="createForm.title" placeholder="例如：Java开发工程师"></el-input>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="公司名称" required>
                <el-input v-model="createForm.company" placeholder="例如：某某科技有限公司"></el-input>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="城市">
                <el-input v-model="createForm.city" placeholder="例如：北京"></el-input>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="区县">
                <el-input v-model="createForm.district" placeholder="例如：海淀区"></el-input>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="最低薪资">
                <el-input-number v-model="createForm.salary_min" :min="0" placeholder="最低月薪" style="width:100%;"></el-input-number>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最高薪资">
                <el-input-number v-model="createForm.salary_max" :min="0" placeholder="最高月薪" style="width:100%;"></el-input-number>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="薪资文本">
                <el-input v-model="createForm.salary_text" placeholder="例如：15K-25K"></el-input>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="工作年限">
                <el-input v-model="createForm.work_years" placeholder="例如：1-3年"></el-input>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="学历">
                <el-select v-model="createForm.education" placeholder="请选择" style="width:100%;">
                  <el-option label="大专" value="大专"></el-option>
                  <el-option label="本科" value="本科"></el-option>
                  <el-option label="硕士" value="硕士"></el-option>
                  <el-option label="博士" value="博士"></el-option>
                  <el-option label="不限" value="不限"></el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="工作类型">
                <el-select v-model="createForm.job_type" placeholder="请选择" style="width:100%;">
                  <el-option label="全职" value="全职"></el-option>
                  <el-option label="兼职" value="兼职"></el-option>
                  <el-option label="实习" value="实习"></el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="公司规模">
                <el-input v-model="createForm.company_size" placeholder="例如：1000-5000人"></el-input>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="公司行业">
                <el-input v-model="createForm.company_industry" placeholder="例如：互联网"></el-input>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="HR姓名">
                <el-input v-model="createForm.hr_name" placeholder="例如：张经理"></el-input>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="岗位原链接" required>
                <el-input v-model="createForm.job_url" placeholder="https://..."></el-input>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="双休">
                <el-select v-model="createForm.is_weekend_off" placeholder="请选择" clearable style="width:100%;">
                  <el-option label="是" :value="true"></el-option>
                  <el-option label="否" :value="false"></el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="包住宿">
                <el-select v-model="createForm.has_accommodation" placeholder="请选择" clearable style="width:100%;">
                  <el-option label="是" :value="true"></el-option>
                  <el-option label="否" :value="false"></el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="岗位JD">
            <el-input v-model="createForm.jd_text" type="textarea" :rows="4" placeholder="岗位职责与要求..."></el-input>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="createDialog = false">取消</el-button>
          <el-button type="primary" @click="submitCreateJob" :loading="createLoading">确认录入</el-button>
        </template>
      </el-dialog>
    </div>
  `
};
