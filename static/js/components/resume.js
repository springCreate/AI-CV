/**
 * 简历管理页面
 */
const ResumePage = {
  setup() {
    const resumes = ref([]);
    const loading = ref(false);
    const uploadDialog = ref(false);
    const createDialog = ref(false);
    const editDialog = ref(false);
    const optimizeDialog = ref(false);
    const detailDialog = ref(false);
    const uploadFile = ref(null);
    const uploadName = ref('');
    const uploadLoading = ref(false);
    const createLoading = ref(false);
    const currentResume = ref(null);
    const editForm = ref({});
    const createForm = ref({ name: '', real_name: '', target_position: '', target_city: '', expected_salary: '', self_evaluation: '' });
    const optimizeForm = ref({ jd: '', template_id: null });
    const templates = ref([]);
    const optimizeResult = ref(null);
    const optimizing = ref(false);
    const applyFields = ref({});

    async function load() {
      loading.value = true;
      try {
        resumes.value = await API.resume.list();
        templates.value = await API.template.list();
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        loading.value = false;
      }
    }

    function handleFileChange(file) {
      uploadFile.value = file.raw;
      uploadName.value = file.name;
    }

    async function handleUpload() {
      if (!uploadFile.value) {
        ElMessage.warning('请先选择文件');
        return;
      }
      uploadLoading.value = true;
      try {
        const fd = new FormData();
        fd.append('file', uploadFile.value);
        fd.append('name', uploadName.value);
        const data = await API.resume.upload(fd);
        ElMessage.success('简历上传并解析成功');
        uploadDialog.value = false;
        uploadFile.value = null;
        uploadName.value = '';
        await load();
        currentResume.value = data.resume;
        detailDialog.value = true;
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        uploadLoading.value = false;
      }
    }

    function openCreate() {
      createForm.value = { name: '', real_name: '', target_position: '', target_city: '', expected_salary: '', self_evaluation: '' };
      createDialog.value = true;
    }

    async function saveCreate() {
      if (!createForm.value.name.trim()) {
        ElMessage.warning('请输入简历名称');
        return;
      }
      createLoading.value = true;
      try {
        const data = await API.resume.create(createForm.value);
        ElMessage.success('简历创建成功');
        createDialog.value = false;
        await load();
        currentResume.value = data;
        detailDialog.value = true;
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        createLoading.value = false;
      }
    }

    function viewDetail(r) {
      currentResume.value = r;
      detailDialog.value = true;
      loadDetail(r.id);
    }

    async function loadDetail(id) {
      try {
        currentResume.value = await API.resume.get(id);
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    function editBasic(r) {
      editForm.value = { ...r };
      editDialog.value = true;
    }

    async function saveBasic() {
      try {
        await API.resume.update(editForm.value.id, editForm.value);
        ElMessage.success('更新成功');
        editDialog.value = false;
        await load();
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function remove(r) {
      try {
        await ElMessageBox.confirm(`确定删除简历「${r.name}」？`, '提示', { type: 'warning' });
        await API.resume.delete(r.id);
        ElMessage.success('删除成功');
        await load();
      } catch (e) {
        if (e !== 'cancel' && e.message) ElMessage.error(e.message);
      }
    }

    function openOptimize(r) {
      currentResume.value = r;
      optimizeForm.value = { jd: '', template_id: templates.value.find(t => t.is_default)?.id || null };
      optimizeResult.value = null;
      applyFields.value = {};
      optimizeDialog.value = true;
    }

    async function doOptimize() {
      if (!optimizeForm.value.jd.trim()) {
        ElMessage.warning('请输入目标岗位 JD');
        return;
      }
      optimizing.value = true;
      try {
        const data = await API.resume.optimize(currentResume.value.id, optimizeForm.value);
        optimizeResult.value = data;
        ElMessage.success('优化建议已生成');
        // 默认应用项初始化
        applyFields.value = {
          self_evaluation: data.suggestions.evaluation_suggestions?.suggested || '',
          add_skills: (data.suggestions.skill_suggestions || []).map(s => ({...s, _selected: true})),
        };
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        optimizing.value = false;
      }
    }

    async function applyOptimization() {
      const fields = {
        self_evaluation: applyFields.value.self_evaluation,
        add_skills: (applyFields.value.add_skills || []).filter(s => s._selected).map(s => ({
          name: s.name, level: s.level, category: s.category,
        })),
        update_experiences: [],
        update_projects: [],
        delete_experiences: [],
        delete_projects: [],
      };
      try {
        await API.resume.applyOptimization(currentResume.value.id, optimizeResult.value.log_id, fields);
        ElMessage.success('优化建议已应用');
        optimizeDialog.value = false;
        await load();
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function exportPdf(r) {
      try {
        const data = await API.resume.exportPdf(r.id, { pages: 'single' });
        ElMessage.success('PDF 生成成功');
        window.open(`/api/resume/${r.id}/download-pdf`, '_blank');
        await load();
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function reparse(r) {
      try {
        await ElMessageBox.confirm('重新解析将覆盖当前简历内容，是否继续？', '提示', { type: 'warning' });
        ElMessage.info('AI 重新解析中...');
        await API.resume.reparse(r.id);
        ElMessage.success('重新解析成功');
        await load();
      } catch (e) {
        if (e !== 'cancel' && e.message) ElMessage.error(e.message);
      }
    }

    // 子模块添加
    const subDialog = ref(false);
    const subType = ref('');
    const subForm = ref({});
    function openAddSub(type) {
      subType.value = type;
      subForm.value = {};
      subDialog.value = true;
    }
    async function saveSub() {
      try {
        const apiMap = {
          education: API.resume.addEducation,
          experience: API.resume.addExperience,
          project: API.resume.addProject,
          skill: API.resume.addSkill,
        };
        await apiMap[subType.value](currentResume.value.id, subForm.value);
        ElMessage.success('添加成功');
        subDialog.value = false;
        await loadDetail(currentResume.value.id);
      } catch (e) {
        ElMessage.error(e.message);
      }
    }
    async function removeSub(type, item) {
      try {
        const apiMap = {
          education: API.resume.deleteEducation,
          experience: API.resume.deleteExperience,
          project: API.resume.deleteProject,
          skill: API.resume.deleteSkill,
        };
        await apiMap[type](currentResume.value.id, item.id);
        ElMessage.success('已删除');
        await loadDetail(currentResume.value.id);
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    onMounted(load);

    return {
      resumes, loading, uploadDialog, createDialog, editDialog, optimizeDialog, detailDialog,
      uploadFile, uploadName, uploadLoading, createLoading, currentResume, editForm, createForm,
      optimizeForm, templates, optimizeResult, optimizing, applyFields,
      subDialog, subType, subForm,
      load, handleFileChange, handleUpload, openCreate, saveCreate, viewDetail, loadDetail,
      editBasic, saveBasic, remove, openOptimize, doOptimize, applyOptimization,
      exportPdf, reparse, openAddSub, saveSub, removeSub,
    };
  },
  template: `
    <div v-loading="loading">
      <div class="page-title">我的简历
        <div>
          <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 手动创建</el-button>
          <el-button type="primary" @click="uploadDialog = true"><el-icon><Upload /></el-icon> 上传简历</el-button>
        </div>
      </div>

      <div v-if="resumes.length === 0 && !loading" class="empty-state">
        <el-icon><Document /></el-icon>
        <div style="margin-top:12px;">还没有简历，点击右上角手动创建或上传 PDF/Word 简历</div>
      </div>

      <el-row :gutter="16">
        <el-col v-for="r in resumes" :key="r.id" :span="8" style="margin-bottom:16px;">
          <el-card class="resume-card" @click="viewDetail(r)">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
              <div style="flex:1;">
                <div style="font-size:16px;font-weight:600;color:#1a202c;">{{ r.name }}</div>
                <div style="font-size:13px;color:#718096;margin-top:4px;">
                  {{ r.real_name || '未填写姓名' }} · {{ r.target_position || '未指定岗位' }}
                </div>
                <div style="font-size:12px;color:#a0aec0;margin-top:8px;">
                  {{ r.source_file_type ? '来源：' + r.source_file_type.toUpperCase() : '手动创建' }}
                </div>
              </div>
              <el-tag v-if="r.is_active" type="success" size="small">激活</el-tag>
            </div>
            <div style="margin-top:12px;display:flex;gap:6px;flex-wrap:wrap;">
              <el-button size="small" @click.stop="openOptimize(r)"><el-icon><MagicStick /></el-icon> AI 优化</el-button>
              <el-button size="small" @click.stop="exportPdf(r)"><el-icon><Download /></el-icon> 导出PDF</el-button>
              <el-button size="small" @click.stop="editBasic(r)"><el-icon><Edit /></el-icon> 编辑</el-button>
              <el-button v-if="r.source_file_path" size="small" @click.stop="reparse(r)"><el-icon><Refresh /></el-icon> 重解析</el-button>
              <el-button size="small" type="danger" @click.stop="remove(r)"><el-icon><Delete /></el-icon></el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 手动创建对话框 -->
      <el-dialog v-model="createDialog" title="手动创建简历" width="600px">
        <el-form :model="createForm" label-width="100px">
          <el-form-item label="简历名称" required><el-input v-model="createForm.name" placeholder="如：测试简历"></el-input></el-form-item>
          <el-form-item label="姓名"><el-input v-model="createForm.real_name" placeholder="真实姓名"></el-input></el-form-item>
          <el-form-item label="目标岗位"><el-input v-model="createForm.target_position" placeholder="如：软件测试"></el-input></el-form-item>
          <el-form-item label="期望城市"><el-input v-model="createForm.target_city" placeholder="如：北京"></el-input></el-form-item>
          <el-form-item label="期望薪资"><el-input v-model="createForm.expected_salary" placeholder="如：8000-12000"></el-input></el-form-item>
          <el-form-item label="自我评价">
            <el-input type="textarea" v-model="createForm.self_evaluation" :rows="4" placeholder="简要描述个人优势"></el-input>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="createDialog = false">取消</el-button>
          <el-button type="primary" :loading="createLoading" @click="saveCreate">创建</el-button>
        </template>
      </el-dialog>

      <!-- 上传对话框 -->
      <el-dialog v-model="uploadDialog" title="上传简历" width="500px">
        <el-upload
          drag
          :auto-upload="false"
          accept=".pdf,.docx,.doc"
          :on-change="handleFileChange"
          :show-file-list="false">
          <el-icon style="font-size:48px;color:#a0aec0;"><UploadFilled /></el-icon>
          <div style="margin-top:8px;">将简历文件拖到此处，或<em style="color:#4299e1;">点击上传</em></div>
          <template #tip>
            <div style="font-size:12px;color:#a0aec0;text-align:center;margin-top:8px;">
              支持 PDF / Word，系统将自动调用 AI 解析为结构化信息
            </div>
          </template>
        </el-upload>
        <div v-if="uploadName" style="margin-top:12px;color:#4299e1;">已选择：{{ uploadName }}</div>
        <template #footer>
          <el-button @click="uploadDialog = false">取消</el-button>
          <el-button type="primary" :loading="uploadLoading" @click="handleUpload">上传并解析</el-button>
        </template>
      </el-dialog>

      <!-- 详情对话框 -->
      <el-dialog v-model="detailDialog" :title="currentResume ? currentResume.name : '简历详情'" width="80%" top="5vh">
        <div v-if="currentResume" v-loading="!currentResume.educations">
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item label="姓名">{{ currentResume.real_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="性别">{{ currentResume.gender || '-' }}</el-descriptions-item>
            <el-descriptions-item label="年龄">{{ currentResume.age || '-' }}</el-descriptions-item>
            <el-descriptions-item label="电话">{{ currentResume.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ currentResume.email || '-' }}</el-descriptions-item>
            <el-descriptions-item label="现居地">{{ currentResume.location || '-' }}</el-descriptions-item>
            <el-descriptions-item label="目标岗位">{{ currentResume.target_position || '-' }}</el-descriptions-item>
            <el-descriptions-item label="期望城市">{{ currentResume.target_city || '-' }}</el-descriptions-item>
            <el-descriptions-item label="期望薪资">{{ currentResume.expected_salary || '-' }}</el-descriptions-item>
          </el-descriptions>

          <el-divider content-position="left">自我评价
            <el-button size="small" @click="openAddSub('evaluation')" style="margin-left:8px;">编辑</el-button>
          </el-divider>
          <div v-if="currentResume.self_evaluation" class="jd-text">{{ currentResume.self_evaluation }}</div>
          <div v-else class="empty-state" style="padding:20px;">未填写</div>

          <el-divider content-position="left">教育经历
            <el-button size="small" type="primary" @click="openAddSub('education')" style="margin-left:8px;">添加</el-button>
          </el-divider>
          <el-timeline v-if="currentResume.educations && currentResume.educations.length">
            <el-timeline-item v-for="edu in currentResume.educations" :key="edu.id" :timestamp="edu.start_date + ' - ' + (edu.end_date || '至今')" placement="top">
              <el-card shadow="never">
                <div style="display:flex;justify-content:space-between;">
                  <strong>{{ edu.school }} · {{ edu.major }} · {{ edu.degree }}</strong>
                  <el-button size="small" type="danger" text :icon="Delete" @click="removeSub('education', edu)"></el-button>
                </div>
                <div v-if="edu.description" style="margin-top:4px;font-size:13px;color:#4a5568;">{{ edu.description }}</div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          <div v-else class="empty-state" style="padding:20px;">未填写</div>

          <el-divider content-position="left">工作/实习经历
            <el-button size="small" type="primary" @click="openAddSub('experience')" style="margin-left:8px;">添加</el-button>
          </el-divider>
          <el-timeline v-if="currentResume.experiences && currentResume.experiences.length">
            <el-timeline-item v-for="exp in currentResume.experiences" :key="exp.id" :timestamp="exp.start_date + ' - ' + (exp.end_date || '至今')" placement="top">
              <el-card shadow="never">
                <div style="display:flex;justify-content:space-between;">
                  <strong>{{ exp.company }} · {{ exp.position }} <el-tag size="small" v-if="exp.job_type">{{ exp.job_type }}</el-tag></strong>
                  <el-button size="small" type="danger" text :icon="Delete" @click="removeSub('experience', exp)"></el-button>
                </div>
                <div v-if="exp.description" style="margin-top:4px;font-size:13px;color:#4a5568;white-space:pre-wrap;">{{ exp.description }}</div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          <div v-else class="empty-state" style="padding:20px;">未填写</div>

          <el-divider content-position="left">项目经历
            <el-button size="small" type="primary" @click="openAddSub('project')" style="margin-left:8px;">添加</el-button>
          </el-divider>
          <el-timeline v-if="currentResume.projects && currentResume.projects.length">
            <el-timeline-item v-for="proj in currentResume.projects" :key="proj.id" :timestamp="proj.start_date + ' - ' + (proj.end_date || '至今')" placement="top">
              <el-card shadow="never">
                <div style="display:flex;justify-content:space-between;">
                  <strong>{{ proj.name }} · {{ proj.role }}</strong>
                  <el-button size="small" type="danger" text :icon="Delete" @click="removeSub('project', proj)"></el-button>
                </div>
                <div v-if="proj.tech_stack" style="margin-top:4px;font-size:12px;color:#805ad5;">技术栈：{{ proj.tech_stack }}</div>
                <div v-if="proj.description" style="margin-top:4px;font-size:13px;color:#4a5568;white-space:pre-wrap;">{{ proj.description }}</div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          <div v-else class="empty-state" style="padding:20px;">未填写</div>

          <el-divider content-position="left">专业技能
            <el-button size="small" type="primary" @click="openAddSub('skill')" style="margin-left:8px;">添加</el-button>
          </el-divider>
          <div v-if="currentResume.skills && currentResume.skills.length" class="tag-cloud">
            <el-tag v-for="sk in currentResume.skills" :key="sk.id" closable @close="removeSub('skill', sk)" style="margin:4px;">
              {{ sk.name }} · {{ sk.level }}
            </el-tag>
          </div>
          <div v-else class="empty-state" style="padding:20px;">未填写</div>
        </div>
      </el-dialog>

      <!-- 基础信息编辑 -->
      <el-dialog v-model="editDialog" title="编辑简历基础信息" width="600px">
        <el-form :model="editForm" label-width="100px">
          <el-form-item label="简历名称"><el-input v-model="editForm.name"></el-input></el-form-item>
          <el-form-item label="姓名"><el-input v-model="editForm.real_name"></el-input></el-form-item>
          <el-form-item label="性别">
            <el-select v-model="editForm.gender" placeholder="选择性别" clearable>
              <el-option label="男" value="男"></el-option>
              <el-option label="女" value="女"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="年龄"><el-input-number v-model="editForm.age" :min="16" :max="80"></el-input-number></el-form-item>
          <el-form-item label="电话"><el-input v-model="editForm.phone"></el-input></el-form-item>
          <el-form-item label="邮箱"><el-input v-model="editForm.email"></el-input></el-form-item>
          <el-form-item label="现居地"><el-input v-model="editForm.location"></el-input></el-form-item>
          <el-form-item label="目标岗位"><el-input v-model="editForm.target_position"></el-input></el-form-item>
          <el-form-item label="期望城市"><el-input v-model="editForm.target_city"></el-input></el-form-item>
          <el-form-item label="期望薪资"><el-input v-model="editForm.expected_salary"></el-input></el-form-item>
          <el-form-item label="自我评价">
            <el-input type="textarea" v-model="editForm.self_evaluation" :rows="4"></el-input>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="editDialog = false">取消</el-button>
          <el-button type="primary" @click="saveBasic">保存</el-button>
        </template>
      </el-dialog>

      <!-- 子模块添加 -->
      <el-dialog v-model="subDialog" :title="'添加' + (subType==='education'?'教育经历':subType==='experience'?'工作经历':subType==='project'?'项目经历':subType==='skill'?'技能':'自我评价')" width="600px">
        <el-form :model="subForm" label-width="100px">
          <template v-if="subType==='education'">
            <el-form-item label="学校"><el-input v-model="subForm.school"></el-input></el-form-item>
            <el-form-item label="专业"><el-input v-model="subForm.major"></el-input></el-form-item>
            <el-form-item label="学历">
              <el-select v-model="subForm.degree"><el-option label="大专" value="大专"></el-option><el-option label="本科" value="本科"></el-option><el-option label="硕士" value="硕士"></el-option><el-option label="博士" value="博士"></el-option></el-select>
            </el-form-item>
            <el-form-item label="开始时间"><el-input v-model="subForm.start_date" placeholder="如 2021-09"></el-input></el-form-item>
            <el-form-item label="结束时间"><el-input v-model="subForm.end_date" placeholder="如 2025-06 或 至今"></el-input></el-form-item>
            <el-form-item label="描述"><el-input type="textarea" v-model="subForm.description" :rows="3"></el-input></el-form-item>
          </template>
          <template v-else-if="subType==='experience'">
            <el-form-item label="公司"><el-input v-model="subForm.company"></el-input></el-form-item>
            <el-form-item label="职位"><el-input v-model="subForm.position"></el-input></el-form-item>
            <el-form-item label="类型">
              <el-select v-model="subForm.job_type"><el-option label="全职" value="全职"></el-option><el-option label="实习" value="实习"></el-option></el-select>
            </el-form-item>
            <el-form-item label="开始时间"><el-input v-model="subForm.start_date" placeholder="如 2022-07"></el-input></el-form-item>
            <el-form-item label="结束时间"><el-input v-model="subForm.end_date" placeholder="如 2024-08 或 至今"></el-input></el-form-item>
            <el-form-item label="工作内容"><el-input type="textarea" v-model="subForm.description" :rows="4" placeholder="STAR 法则描述"></el-input></el-form-item>
          </template>
          <template v-else-if="subType==='project'">
            <el-form-item label="项目名称"><el-input v-model="subForm.name"></el-input></el-form-item>
            <el-form-item label="担任角色"><el-input v-model="subForm.role"></el-input></el-form-item>
            <el-form-item label="开始时间"><el-input v-model="subForm.start_date" placeholder="如 2023-01"></el-input></el-form-item>
            <el-form-item label="结束时间"><el-input v-model="subForm.end_date" placeholder="如 2023-06 或 至今"></el-input></el-form-item>
            <el-form-item label="技术栈"><el-input v-model="subForm.tech_stack" placeholder="逗号分隔"></el-input></el-form-item>
            <el-form-item label="项目描述"><el-input type="textarea" v-model="subForm.description" :rows="4" placeholder="STAR 法则描述"></el-input></el-form-item>
          </template>
          <template v-else-if="subType==='skill'">
            <el-form-item label="技能名称"><el-input v-model="subForm.name"></el-input></el-form-item>
            <el-form-item label="掌握程度">
              <el-select v-model="subForm.level"><el-option label="了解" value="了解"></el-option><el-option label="熟悉" value="熟悉"></el-option><el-option label="熟练" value="熟练"></el-option><el-option label="精通" value="精通"></el-option></el-select>
            </el-form-item>
            <el-form-item label="分类">
              <el-select v-model="subForm.category"><el-option label="编程语言" value="编程语言"></el-option><el-option label="框架" value="框架"></el-option><el-option label="工具" value="工具"></el-option><el-option label="数据库" value="数据库"></el-option><el-option label="软技能" value="软技能"></el-option><el-option label="其他" value="其他"></el-option></el-select>
            </el-form-item>
          </template>
        </el-form>
        <template #footer>
          <el-button @click="subDialog = false">取消</el-button>
          <el-button type="primary" @click="saveSub">保存</el-button>
        </template>
      </el-dialog>

      <!-- AI 优化对话框 -->
      <el-dialog v-model="optimizeDialog" title="AI 简历优化（五维度）" width="80%" top="5vh">
        <el-alert type="info" :closable="false" style="margin-bottom:16px;">
          系统将基于目标岗位 JD 与求职诉求，生成五维度优化建议。建议需手动确认后才会应用到简历。
        </el-alert>
        <el-form label-width="100px">
          <el-form-item label="目标岗位 JD">
            <el-input type="textarea" v-model="optimizeForm.jd" :rows="6" placeholder="粘贴目标岗位 JD 全文"></el-input>
          </el-form-item>
          <el-form-item label="求职诉求模板">
            <el-select v-model="optimizeForm.template_id" placeholder="可选" clearable>
              <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="optimizing" @click="doOptimize">
              <el-icon><MagicStick /></el-icon> 生成优化建议
            </el-button>
          </el-form-item>
        </el-form>

        <div v-if="optimizeResult">
          <el-divider content-position="left">优化建议</el-divider>

          <el-tabs>
            <el-tab-pane label="关键词适配">
              <div v-for="(item, idx) in optimizeResult.suggestions.keyword_suggestions" :key="'k'+idx" class="suggestion-item">
                <div class="target">目标：{{ item.target }} / {{ item.field }}</div>
                <div class="original">{{ item.original }}</div>
                <div class="suggested">→ {{ item.suggested }}</div>
                <div class="reason">{{ item.reason }}</div>
              </div>
              <div v-if="!optimizeResult.suggestions.keyword_suggestions?.length" class="empty-state">暂无建议</div>
            </el-tab-pane>

            <el-tab-pane label="删减建议">
              <div v-for="(item, idx) in optimizeResult.suggestions.deletion_suggestions" :key="'d'+idx" class="suggestion-item" style="border-left-color:#e53e3e;">
                <div class="target">{{ item.target }}</div>
                <div class="reason">{{ item.reason }}</div>
                <div class="suggested">{{ item.detail }}</div>
              </div>
              <div v-if="!optimizeResult.suggestions.deletion_suggestions?.length" class="empty-state">暂无建议</div>
            </el-tab-pane>

            <el-tab-pane label="技能补充">
              <el-table :data="optimizeResult.suggestions.skill_suggestions" size="small">
                <el-table-column type="selection" width="50">
                  <template #default="{ row }">
                    <el-checkbox v-model="row._selected"></el-checkbox>
                  </template>
                </el-table-column>
                <el-table-column prop="name" label="技能"></el-table-column>
                <el-table-column prop="level" label="程度" width="100"></el-table-column>
                <el-table-column prop="category" label="分类" width="120"></el-table-column>
                <el-table-column prop="reason" label="理由"></el-table-column>
              </el-table>
              <div v-if="!optimizeResult.suggestions.skill_suggestions?.length" class="empty-state">暂无建议</div>
            </el-tab-pane>

            <el-tab-pane label="自我评价">
              <div v-if="optimizeResult.suggestions.evaluation_suggestions">
                <div v-for="h in optimizeResult.suggestions.evaluation_suggestions.highlights" :key="h" style="margin-bottom:4px;">
                  <el-tag type="info" size="small">{{ h }}</el-tag>
                </div>
                <el-input type="textarea" v-model="applyFields.self_evaluation" :rows="8" style="margin-top:12px;"></el-input>
              </div>
            </el-tab-pane>

            <el-tab-pane label="排版优化">
              <div v-for="(item, idx) in optimizeResult.suggestions.format_suggestions" :key="'f'+idx" class="suggestion-item" style="border-left-color:#805ad5;">
                <div class="target">{{ item.target }}</div>
                <div v-for="i in item.issues" :key="i" class="reason">• {{ i }}</div>
                <div class="suggested">{{ item.suggested }}</div>
              </div>
              <div v-if="!optimizeResult.suggestions.format_suggestions?.length" class="empty-state">暂无建议</div>
            </el-tab-pane>
          </el-tabs>

          <div style="margin-top:16px;text-align:right;">
            <el-button type="primary" @click="applyOptimization">
              <el-icon><Check /></el-icon> 确认应用建议
            </el-button>
          </div>
        </div>
      </el-dialog>
    </div>
  `
};
