/**
 * 求职诉求模板页面
 */
const TemplatePage = {
  setup() {
    const templates = ref([]);
    const loading = ref(false);
    const dialog = ref(false);
    const editing = ref(false);
    const form = ref({});

    function emptyForm() {
      return {
        name: '', cities: [], position: '', job_type: '全职',
        salary_min: null, salary_max: null,
        work_years_min: null, work_years_max: null,
        require_weekend_off: false, require_no_overtime: false, require_accommodation: false,
        intern_certificate: false, intern_min_months: null,
        other_requirements: '', keywords: [], is_default: false,
      };
    }

    async function load() {
      loading.value = true;
      try {
        templates.value = await API.template.list();
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        loading.value = false;
      }
    }

    function openCreate() {
      form.value = emptyForm();
      editing.value = false;
      dialog.value = true;
    }

    function openEdit(t) {
      form.value = { ...t, cities: [...(t.cities || [])], keywords: [...(t.keywords || [])] };
      editing.value = true;
      dialog.value = true;
    }

    async function save() {
      if (!form.value.name) {
        ElMessage.warning('请填写模板名称');
        return;
      }
      try {
        if (editing.value) {
          await API.template.update(form.value.id, form.value);
        } else {
          await API.template.create(form.value);
        }
        ElMessage.success('保存成功');
        dialog.value = false;
        await load();
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function remove(t) {
      try {
        await ElMessageBox.confirm(`确定删除模板「${t.name}」？`, '提示', { type: 'warning' });
        await API.template.delete(t.id);
        ElMessage.success('已删除');
        await load();
      } catch (e) {
        if (e !== 'cancel' && e.message) ElMessage.error(e.message);
      }
    }

    async function setDefault(t) {
      try {
        await API.template.setDefault(t.id);
        ElMessage.success('已设为默认');
        await load();
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    onMounted(load);

    return { templates, loading, dialog, editing, form, load, openCreate, openEdit, save, remove, setDefault };
  },
  template: `
    <div v-loading="loading">
      <div class="page-title">求职诉求模板
        <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建模板</el-button>
      </div>

      <div v-if="templates.length === 0 && !loading" class="empty-state">
        <el-icon><Files /></el-icon>
        <div style="margin-top:12px;">还没有求职诉求模板</div>
      </div>

      <el-row :gutter="16">
        <el-col v-for="t in templates" :key="t.id" :span="12" style="margin-bottom:16px;">
          <el-card>
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
              <div>
                <div style="font-size:16px;font-weight:600;">
                  {{ t.name }}
                  <el-tag v-if="t.is_default" type="success" size="small">默认</el-tag>
                </div>
                <div style="font-size:13px;color:#4a5568;margin-top:6px;">
                  <span v-if="t.position">岗位：{{ t.position }} · </span>
                  <span v-if="t.cities && t.cities.length">城市：{{ t.cities.join('/') }} · </span>
                  <span v-if="t.salary_min">{{ t.salary_min }}-{{ t.salary_max || '不限' }}元</span>
                </div>
                <div style="margin-top:8px;" class="tag-cloud">
                  <el-tag v-if="t.job_type" size="small">{{ t.job_type }}</el-tag>
                  <el-tag v-if="t.require_weekend_off" size="small" type="warning">双休</el-tag>
                  <el-tag v-if="t.require_no_overtime" size="small" type="warning">不加班</el-tag>
                  <el-tag v-if="t.require_accommodation" size="small" type="warning">包住宿</el-tag>
                  <el-tag v-if="t.intern_certificate" size="small" type="info">实习证明</el-tag>
                  <el-tag v-for="k in (t.keywords || [])" :key="k" size="small">{{ k }}</el-tag>
                </div>
              </div>
              <div>
                <el-button size="small" @click="openEdit(t)"><el-icon><Edit /></el-icon></el-button>
                <el-button v-if="!t.is_default" size="small" @click="setDefault(t)">设为默认</el-button>
                <el-button size="small" type="danger" @click="remove(t)"><el-icon><Delete /></el-icon></el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-dialog v-model="dialog" :title="editing ? '编辑模板' : '新建模板'" width="700px">
        <el-form :model="form" label-width="120px">
          <el-form-item label="模板名称"><el-input v-model="form.name" placeholder="如：北京测试岗-8k双休"></el-input></el-form-item>
          <el-form-item label="设为默认"><el-switch v-model="form.is_default"></el-switch></el-form-item>
          <el-divider content-position="left">硬性筛选条件</el-divider>
          <el-form-item label="目标岗位"><el-input v-model="form.position" placeholder="如：软件测试"></el-input></el-form-item>
          <el-form-item label="期望城市">
            <el-select v-model="form.cities" multiple filterable allow-create placeholder="可多选">
              <el-option v-for="c in ['北京','上海','深圳','杭州','广州','成都','南京','武汉','天津','西安','苏州','长沙','重庆']" :key="c" :label="c" :value="c"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="工作类型">
            <el-radio-group v-model="form.job_type">
              <el-radio label="全职">全职</el-radio>
              <el-radio label="实习">实习</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="薪资范围（元/月）">
            <el-input-number v-model="form.salary_min" :min="0" :step="1000" placeholder="最低"></el-input-number>
            <span style="margin:0 8px;">-</span>
            <el-input-number v-model="form.salary_max" :min="0" :step="1000" placeholder="最高"></el-input-number>
          </el-form-item>
          <el-form-item label="工作年限">
            <el-input-number v-model="form.work_years_min" :min="0" placeholder="最少"></el-input-number>
            <span style="margin:0 8px;">-</span>
            <el-input-number v-model="form.work_years_max" :min="0" placeholder="最多"></el-input-number>
          </el-form-item>
          <el-divider content-position="left">作息与福利</el-divider>
          <el-form-item label="必须双休"><el-switch v-model="form.require_weekend_off"></el-switch></el-form-item>
          <el-form-item label="不加班"><el-switch v-model="form.require_no_overtime"></el-switch></el-form-item>
          <el-form-item label="包住宿"><el-switch v-model="form.require_accommodation"></el-switch></el-form-item>
          <el-divider content-position="left">实习专属</el-divider>
          <el-form-item label="可开实习证明"><el-switch v-model="form.intern_certificate"></el-switch></el-form-item>
          <el-form-item label="实习最短月数"><el-input-number v-model="form.intern_min_months" :min="1"></el-input-number></el-form-item>
          <el-divider content-position="left">其他</el-divider>
          <el-form-item label="关键词">
            <el-select v-model="form.keywords" multiple filterable allow-create placeholder="逗号分隔的关键词，用于 AI 软性匹配加权"></el-select>
          </el-form-item>
          <el-form-item label="其他要求">
            <el-input type="textarea" v-model="form.other_requirements" :rows="3"></el-input>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialog = false">取消</el-button>
          <el-button type="primary" @click="save">保存</el-button>
        </template>
      </el-dialog>
    </div>
  `
};
