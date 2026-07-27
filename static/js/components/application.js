/**
 * 投递管理页面
 */
const ApplicationPage = {
  setup() {
    const activeTab = ref('list');
    const loading = ref(false);
    const applications = ref([]);
    const total = ref(0);
    const page = ref(1);
    const perPage = ref(20);
    const filter = ref({ status: '', company: '' });

    // Excel 导出表单
    const exportForm = ref({
      template_id: null, job_ids: [], min_score: 60, only_unapplied: false,
    });
    const templates = ref([]);
    const resumes = ref([]);
    const exportLoading = ref(false);

    // 话术生成
    const scriptDialog = ref(false);
    const scriptForm = ref({ resume_id: null });
    const scriptContent = ref(null);
    const scriptLoading = ref(false);
    const currentApp = ref(null);

    // 批量话术
    const batchDialog = ref(false);
    const batchForm = ref({ resume_id: null, job_ids: [] });
    const batchLoading = ref(false);
    const batchResult = ref(null);

    async function load() {
      loading.value = true;
      try {
        const params = { page: page.value, per_page: perPage.value };
        if (filter.value.status) params.status = filter.value.status;
        if (filter.value.company) params.company = filter.value.company;
        const data = await API.application.list(params);
        applications.value = data.items;
        total.value = data.total;
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        loading.value = false;
      }
    }

    async function loadOptions() {
      try {
        const [t, r] = await Promise.all([API.template.list(), API.resume.list()]);
        templates.value = t;
        resumes.value = r;
        if (r.length && !scriptForm.value.resume_id) {
          scriptForm.value.resume_id = r[0].id;
          batchForm.value.resume_id = r[0].id;
        }
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function updateStatus(app, status) {
      try {
        await API.application.update(app.id, { status });
        ElMessage.success('状态已更新');
        await load();
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function markApplied(app) {
      try {
        await API.application.markApplied(app.id);
        ElMessage.success('已标记为已投递');
        await load();
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function remove(app) {
      try {
        await ElMessageBox.confirm(`确定删除投递记录？`, '提示', { type: 'warning' });
        await API.application.delete(app.id);
        ElMessage.success('已删除');
        await load();
      } catch (e) {
        if (e !== 'cancel' && e.message) ElMessage.error(e.message);
      }
    }

    function openScript(app) {
      currentApp.value = app;
      scriptContent.value = null;
      scriptDialog.value = true;
    }

    async function generateScript() {
      if (!scriptForm.value.resume_id) {
        ElMessage.warning('请选择简历');
        return;
      }
      scriptLoading.value = true;
      try {
        const data = await API.application.generateScript(currentApp.value.job_id, {
          resume_id: scriptForm.value.resume_id, save: true,
        });
        scriptContent.value = data;
        ElMessage.success('话术已生成');
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        scriptLoading.value = false;
      }
    }

    function copyText(text) {
      navigator.clipboard.writeText(text).then(() => {
        ElMessage.success('已复制到剪贴板');
      }).catch(() => ElMessage.error('复制失败'));
    }

    function openJobUrl(url) {
      if (url) window.open(url, '_blank');
    }

    async function exportExcel() {
      exportLoading.value = true;
      try {
        const data = await API.application.exportExcel(exportForm.value);
        ElMessage.success(`已导出 ${data.record_count} 条记录`);
        window.open(data.download_url, '_blank');
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        exportLoading.value = false;
      }
    }

    function openBatch() {
      batchDialog.value = true;
      batchResult.value = null;
      // 预填入当前列表的 job_id
      batchForm.value.job_ids = applications.value.filter(a => a.job).slice(0, 10).map(a => a.job_id);
    }

    async function batchGenerate() {
      let jobIds = batchForm.value.job_ids;
      if (typeof jobIds === 'string') {
        jobIds = jobIds.split(/[,，\n]/).map(s => s.trim()).filter(s => s);
      }
      if (!Array.isArray(jobIds)) jobIds = [];
      if (!batchForm.value.resume_id || !jobIds.length) {
        ElMessage.warning('请选择简历和岗位');
        return;
      }
      batchLoading.value = true;
      try {
        const payload = { resume_id: batchForm.value.resume_id, job_ids: jobIds };
        const data = await API.application.batchGenerate(payload);
        batchResult.value = data;
        ElMessage.success(`批量生成完成，成功 ${data.success}/${data.total}`);
        await load();
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        batchLoading.value = false;
      }
    }

    function statusTagType(s) {
      return { not_applied: 'info', applied: '', interview: 'warning', offer: 'success', rejected: 'danger' }[s] || 'info';
    }
    function statusText(s) {
      return { not_applied: '未投递', applied: '已投递', interview: '面试中', offer: 'Offer', rejected: '已拒绝' }[s] || s;
    }

    onMounted(async () => {
      await loadOptions();
      await load();
    });

    return {
      activeTab, loading, applications, total, page, perPage, filter,
      exportForm, templates, resumes, exportLoading,
      scriptDialog, scriptForm, scriptContent, scriptLoading, currentApp,
      batchDialog, batchForm, batchLoading, batchResult,
      load, loadOptions, updateStatus, markApplied, remove,
      openScript, generateScript, copyText, openJobUrl, exportExcel,
      openBatch, batchGenerate, statusTagType, statusText,
    };
  },
  template: `
    <div>
      <div class="page-title">投递管理
        <div>
          <el-button @click="openBatch"><el-icon><MagicStick /></el-icon> 批量生成话术</el-button>
          <el-button type="primary" @click="activeTab = 'export'"><el-icon><Download /></el-icon> 导出Excel</el-button>
        </div>
      </div>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="投递记录" name="list">
          <div style="margin-bottom:12px;display:flex;gap:12px;">
            <el-select v-model="filter.status" placeholder="状态" clearable @change="load" style="width:120px;">
              <el-option label="未投递" value="not_applied"></el-option>
              <el-option label="已投递" value="applied"></el-option>
              <el-option label="面试中" value="interview"></el-option>
              <el-option label="Offer" value="offer"></el-option>
              <el-option label="已拒绝" value="rejected"></el-option>
            </el-select>
            <el-input v-model="filter.company" placeholder="公司名" clearable @change="load" style="width:200px;"></el-input>
            <el-button @click="load"><el-icon><Refresh /></el-icon> 刷新</el-button>
          </div>

          <el-table :data="applications" v-loading="loading" border size="small">
            <el-table-column label="公司" prop="job.company" min-width="120"></el-table-column>
            <el-table-column label="岗位" prop="job.title" min-width="140"></el-table-column>
            <el-table-column label="城市" prop="job.city" width="80"></el-table-column>
            <el-table-column label="薪资" prop="job.salary_text" width="100"></el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="投递时间" width="140">
              <template #default="{ row }">
                <span style="font-size:12px;">{{ row.applied_at ? row.applied_at.slice(0,16) : '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="280" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="openScript(row)"><el-icon><ChatDotRound /></el-icon> 话术</el-button>
                <el-button v-if="row.status === 'not_applied'" size="small" type="success" @click="markApplied(row)">标记已投</el-button>
                <el-select v-else :model-value="row.status" size="small" style="width:100px;" @change="(v) => updateStatus(row, v)">
                  <el-option label="已投递" value="applied"></el-option>
                  <el-option label="面试中" value="interview"></el-option>
                  <el-option label="Offer" value="offer"></el-option>
                  <el-option label="已拒绝" value="rejected"></el-option>
                  <el-option label="未投递" value="not_applied"></el-option>
                </el-select>
                <el-button size="small" type="primary" @click="openJobUrl(row.job?.job_url)" :disabled="!row.job?.job_url">跳转</el-button>
                <el-button size="small" type="danger" @click="remove(row)"><el-icon><Delete /></el-icon></el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="page"
            :page-size="perPage"
            :total="total"
            layout="total, prev, pager, next"
            @current-change="load"
            style="margin-top:16px;justify-content:flex-end;display:flex;"></el-pagination>
        </el-tab-pane>

        <el-tab-pane label="Excel 导出" name="export">
          <el-card>
            <el-form :model="exportForm" label-width="120px">
              <el-form-item label="按模板筛选">
                <el-select v-model="exportForm.template_id" placeholder="可选" clearable style="width:240px;">
                  <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id"></el-option>
                </el-select>
              </el-form-item>
              <el-form-item label="最低匹配分数">
                <el-input-number v-model="exportForm.min_score" :min="0" :max="100"></el-input-number>
              </el-form-item>
              <el-form-item label="仅未投递">
                <el-switch v-model="exportForm.only_unapplied"></el-switch>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="exportLoading" @click="exportExcel">
                  <el-icon><Download /></el-icon> 导出 Excel 清单
                </el-button>
              </el-form-item>
            </el-form>
            <el-alert type="info" :closable="false">
              导出的 Excel 包含：公司名称、岗位名称、工作地点、薪资、匹配分数、岗位要求摘要、发布时间、投递状态、岗位原链接等
            </el-alert>
          </el-card>
        </el-tab-pane>
      </el-tabs>

      <!-- 话术生成对话框 -->
      <el-dialog v-model="scriptDialog" title="AI 投递话术" width="700px">
        <div v-if="currentApp">
          <el-alert type="info" :closable="false" style="margin-bottom:12px;">
            为「{{ currentApp.job?.company }} - {{ currentApp.job?.title }}」生成专属话术
          </el-alert>
          <el-form label-width="80px">
            <el-form-item label="选择简历">
              <el-select v-model="scriptForm.resume_id" style="width:300px;">
                <el-option v-for="r in resumes" :key="r.id" :label="r.name" :value="r.id"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="scriptLoading" @click="generateScript">
                <el-icon><MagicStick /></el-icon> 生成专属话术
              </el-button>
            </el-form-item>
          </el-form>

          <div v-if="scriptContent">
            <el-divider content-position="left">打招呼话术
              <el-button size="small" text @click="copyText(scriptContent.application.greeting_message)"><el-icon><CopyDocument /></el-icon> 复制</el-button>
            </el-divider>
            <div class="script-block">{{ scriptContent.application.greeting_message }}</div>

            <el-divider content-position="left">定制自我介绍
              <el-button size="small" text @click="copyText(scriptContent.application.self_introduction)"><el-icon><CopyDocument /></el-icon> 复制</el-button>
            </el-divider>
            <div class="script-block">{{ scriptContent.application.self_introduction }}</div>

            <div style="margin-top:16px;text-align:center;">
              <el-button type="primary" @click="openJobUrl(currentApp.job?.job_url)" :disabled="!currentApp.job?.job_url">
                <el-icon><Link /></el-icon> 前往岗位页面投递
              </el-button>
            </div>
          </div>
        </div>
      </el-dialog>

      <!-- 批量话术对话框 -->
      <el-dialog v-model="batchDialog" title="批量生成话术" width="700px">
        <el-form :model="batchForm" label-width="100px">
          <el-form-item label="选择简历">
            <el-select v-model="batchForm.resume_id" style="width:300px;">
              <el-option v-for="r in resumes" :key="r.id" :label="r.name" :value="r.id"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="岗位 ID">
            <el-input v-model="batchForm.job_ids" type="textarea" :rows="3"
              :placeholder="'逗号分隔的岗位 ID，如：1,2,3'"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="batchLoading" @click="batchGenerate">开始批量生成</el-button>
          </el-form-item>
        </el-form>
        <div v-if="batchResult">
          <el-alert :type="batchResult.failed === 0 ? 'success' : 'warning'" :closable="false">
            总计 {{ batchResult.total }}，成功 {{ batchResult.success }}，失败 {{ batchResult.failed }}，已保存 {{ batchResult.saved }}
          </el-alert>
        </div>
      </el-dialog>
    </div>
  `
};
