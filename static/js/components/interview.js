/**
 * 面试题库页面
 */
const InterviewPage = {
  setup() {
    const activeTab = ref('list');
    const loading = ref(false);

    // 生成面试问题表单
    const generateForm = ref({ resume_id: null, job_id: null });
    const resumes = ref([]);
    const jobs = ref([]);
    const generateLoading = ref(false);

    // 题库列表
    const questions = ref([]);
    const questionsTotal = ref(0);
    const questionsPage = ref(1);
    const questionsPerPage = ref(20);
    const questionsFilter = ref({ job_id: null });

    // 当前选中的问题详情
    const detailDialog = ref(false);
    const currentQuestion = ref(null);

    async function loadOptions() {
      try {
        const [r, j] = await Promise.all([API.resume.list(), API.job.list({ per_page: 200 })]);
        resumes.value = r;
        jobs.value = j.items || [];
        if (r.length && !generateForm.value.resume_id) generateForm.value.resume_id = r[0].id;
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function generateQuestions() {
      if (!generateForm.value.resume_id) {
        ElMessage.warning('请选择简历');
        return;
      }
      if (!generateForm.value.job_id) {
        ElMessage.warning('请选择岗位');
        return;
      }
      generateLoading.value = true;
      try {
        const data = await API.interview.generate({
          resume_id: generateForm.value.resume_id,
          job_id: generateForm.value.job_id,
        });
        ElMessage.success(`成功生成 ${data.questions.length} 道面试题`);
        await loadQuestions();
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        generateLoading.value = false;
      }
    }

    async function loadQuestions() {
      loading.value = true;
      try {
        const params = { page: questionsPage.value, per_page: questionsPerPage.value };
        if (questionsFilter.value.job_id) params.job_id = questionsFilter.value.job_id;
        const data = await API.interview.list(params);
        questions.value = data.items;
        questionsTotal.value = data.total;
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        loading.value = false;
      }
    }

    function viewQuestion(q) {
      currentQuestion.value = q;
      detailDialog.value = true;
    }

    async function deleteQuestion(q) {
      try {
        await ElMessageBox.confirm(`确定删除该面试题？`, '提示', { type: 'warning' });
        await API.interview.delete(q.id);
        ElMessage.success('已删除');
        await loadQuestions();
      } catch (e) {
        if (e !== 'cancel' && e.message) ElMessage.error(e.message);
      }
    }

    function copyText(text) {
      navigator.clipboard.writeText(text).then(() => {
        ElMessage.success('已复制到剪贴板');
      }).catch(() => ElMessage.error('复制失败'));
    }

    function questionTypeTag(type) {
      const types = {
        'behavioral': { label: '行为面试', type: 'info' },
        'technical': { label: '技术考察', type: 'warning' },
        'project': { label: '项目经验', type: 'success' },
        'skill': { label: '技能深挖', type: '' },
        'culture': { label: '文化匹配', type: 'primary' },
      };
      return types[type] || { label: type, type: 'info' };
    }

    onMounted(async () => {
      await loadOptions();
      await loadQuestions();
    });

    return {
      activeTab, loading,
      generateForm, resumes, jobs, generateLoading,
      questions, questionsTotal, questionsPage, questionsPerPage, questionsFilter,
      detailDialog, currentQuestion,
      loadOptions, generateQuestions, loadQuestions,
      viewQuestion, deleteQuestion, copyText, questionTypeTag,
    };
  },
  template: `
    <div>
      <div class="page-title">面试题库</div>

      <el-card class="section-card">
        <template #header><strong>生成面试题</strong></template>
        <el-form :model="generateForm" label-width="100px" :inline="true">
          <el-form-item label="选择简历" required>
            <el-select v-model="generateForm.resume_id" placeholder="请选择" style="width:200px;">
              <el-option v-for="r in resumes" :key="r.id" :label="r.name" :value="r.id"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="选择岗位" required>
            <el-select v-model="generateForm.job_id" placeholder="请选择" style="width:280px;" filterable>
              <el-option v-for="j in jobs" :key="j.id" :label="j.company + ' - ' + j.title" :value="j.id"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="generateQuestions" :loading="generateLoading">
              <el-icon><Brain /></el-icon> 生成面试题
            </el-button>
          </el-form-item>
        </el-form>
        <el-alert type="info" :closable="false" style="margin-top:12px;">
          根据岗位JD和个人简历，AI将预测面试官可能提问的问题，并提供回答思路和示例答案
        </el-alert>
      </el-card>

      <el-card>
        <div style="margin-bottom:12px;display:flex;gap:12px;align-items:center;">
          <el-select v-model="questionsFilter.job_id" placeholder="按岗位筛选" clearable @change="loadQuestions" style="width:280px;">
            <el-option v-for="j in jobs" :key="j.id" :label="j.company + ' - ' + j.title" :value="j.id"></el-option>
          </el-select>
          <el-button @click="loadQuestions"><el-icon><Refresh /></el-icon> 刷新</el-button>
        </div>

        <el-table :data="questions" v-loading="loading" border size="small">
          <el-table-column label="题目类型" width="100">
            <template #default="{ row }">
              <el-tag :type="questionTypeTag(row.type).type" size="small">{{ questionTypeTag(row.type).label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="公司" prop="job.company" width="120"></el-table-column>
          <el-table-column label="岗位" prop="job.title" width="140"></el-table-column>
          <el-table-column label="问题" min-width="300" show-overflow-tooltip>
            <template #default="{ row }">
              <span style="font-size:13px;color:#2d3748;">{{ row.question }}</span>
            </template>
          </el-table-column>
          <el-table-column label="难度" width="80">
            <template #default="{ row }">
              <span v-if="row.difficulty === 'easy'" style="color:#48bb78;">简单</span>
              <span v-else-if="row.difficulty === 'medium'" style="color:#ed8936;">中等</span>
              <span v-else style="color:#fc8181;">困难</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="viewQuestion(row)">详情</el-button>
              <el-button size="small" type="danger" @click="deleteQuestion(row)"><el-icon><Delete /></el-icon></el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="questionsPage"
          :page-size="questionsPerPage"
          :total="questionsTotal"
          layout="total, prev, pager, next"
          @current-change="loadQuestions"
          style="margin-top:16px;justify-content:flex-end;display:flex;"></el-pagination>
      </el-card>

      <el-dialog v-model="detailDialog" title="面试题详情" width="700px">
        <div v-if="currentQuestion">
          <div style="margin-bottom:16px;">
            <div style="display:flex;gap:12px;margin-bottom:8px;">
              <el-tag :type="questionTypeTag(currentQuestion.type).type" size="small">{{ questionTypeTag(currentQuestion.type).label }}</el-tag>
              <span v-if="currentQuestion.difficulty === 'easy'" style="color:#48bb78;font-size:12px;">难度：简单</span>
              <span v-else-if="currentQuestion.difficulty === 'medium'" style="color:#ed8936;font-size:12px;">难度：中等</span>
              <span v-else style="color:#fc8181;font-size:12px;">难度：困难</span>
            </div>
            <div style="color:#4a5568;font-size:12px;">{{ currentQuestion.job?.company }} - {{ currentQuestion.job?.title }}</div>
          </div>

          <el-divider content-position="left">问题
            <el-button size="small" text @click="copyText(currentQuestion.question)"><el-icon><CopyDocument /></el-icon> 复制</el-button>
          </el-divider>
          <div style="font-size:15px;font-weight:500;color:#2d3748;margin-bottom:16px;">{{ currentQuestion.question }}</div>

          <el-divider content-position="left">考察要点</el-divider>
          <div style="margin-bottom:16px;">
            <span v-for="(point, idx) in currentQuestion.key_points" :key="idx" style="margin-right:8px;">
              <el-tag size="small">{{ point }}</el-tag>
            </span>
          </div>

          <el-divider content-position="left">回答思路
            <el-button size="small" text @click="copyText(currentQuestion.answer_approach)"><el-icon><CopyDocument /></el-icon> 复制</el-button>
          </el-divider>
          <div class="script-block">{{ currentQuestion.answer_approach }}</div>

          <el-divider content-position="left">示例答案
            <el-button size="small" text @click="copyText(currentQuestion.sample_answer)"><el-icon><CopyDocument /></el-icon> 复制</el-button>
          </div>
          <div class="script-block">{{ currentQuestion.sample_answer }}</div>

          <el-divider content-position="left">加分点</el-divider>
          <div style="margin-bottom:16px;">
            <ul style="padding-left:20px;">
              <li v-for="(tip, idx) in currentQuestion.bonus_points" :key="idx" style="font-size:13px;color:#48bb78;margin-bottom:4px;">{{ tip }}</li>
            </ul>
          </div>
        </div>
      </el-dialog>
    </div>
  `
};
