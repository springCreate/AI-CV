/**
 * 黑名单管理页面
 */
const BlacklistPage = {
  setup() {
    const list = ref([]);
    const loading = ref(false);
    const dialog = ref(false);
    const form = ref({ company: '', reason: '' });

    async function load() {
      loading.value = true;
      try {
        list.value = await API.job.blacklist();
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        loading.value = false;
      }
    }

    function openAdd() {
      form.value = { company: '', reason: '' };
      dialog.value = true;
    }

    async function save() {
      if (!form.value.company) {
        ElMessage.warning('请输入公司名称');
        return;
      }
      try {
        await API.job.addBlacklist(form.value);
        ElMessage.success('已加入黑名单');
        dialog.value = false;
        await load();
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function remove(item) {
      try {
        await ElMessageBox.confirm(`确定将「${item.company}」移出黑名单？`, '提示', { type: 'warning' });
        await API.job.removeBlacklist(item.id);
        ElMessage.success('已移出黑名单');
        await load();
      } catch (e) {
        if (e !== 'cancel' && e.message) ElMessage.error(e.message);
      }
    }

    onMounted(load);

    return { list, loading, dialog, form, load, openAdd, save, remove };
  },
  template: `
    <div v-loading="loading">
      <div class="page-title">公司黑名单
        <el-button type="primary" @click="openAdd"><el-icon><Plus /></el-icon> 添加黑名单</el-button>
      </div>

      <el-alert type="info" :closable="false" style="margin-bottom:16px;">
        加入黑名单的公司，其所有岗位将自动从匹配结果中过滤，不展示、不参与匹配。
      </el-alert>

      <div v-if="list.length === 0 && !loading" class="empty-state">
        <el-icon><CircleClose /></el-icon>
        <div style="margin-top:12px;">黑名单为空</div>
      </div>

      <el-table v-else :data="list" border size="small">
        <el-table-column label="公司名称" prop="company" min-width="200"></el-table-column>
        <el-table-column label="拉黑原因" prop="reason" min-width="300"></el-table-column>
        <el-table-column label="加入时间" width="180">
          <template #default="{ row }">
            <span style="font-size:12px;">{{ row.created_at?.slice(0,16) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="remove(row)"><el-icon><Delete /></el-icon> 移除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-dialog v-model="dialog" title="添加黑名单" width="500px">
        <el-form :model="form" label-width="100px">
          <el-form-item label="公司名称">
            <el-input v-model="form.company" placeholder="请输入公司全称"></el-input>
          </el-form-item>
          <el-form-item label="拉黑原因">
            <el-input type="textarea" v-model="form.reason" :rows="3" placeholder="可选"></el-input>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialog = false">取消</el-button>
          <el-button type="primary" @click="save">加入黑名单</el-button>
        </template>
      </el-dialog>
    </div>
  `
};
