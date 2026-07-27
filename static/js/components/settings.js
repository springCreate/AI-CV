/**
 * 系统设置页面
 */
const SettingsPage = {
  setup() {
    const config = ref(null);
    const userForm = ref({});
    const pwdForm = ref({ old_password: '', new_password: '', confirm: '' });
    const loading = ref(false);
    const testing = ref(false);

    async function loadConfig() {
      try {
        config.value = await API.system.config();
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function loadUser() {
      try {
        const u = await API.auth.me();
        userForm.value = { ...u };
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function saveUser() {
      try {
        await API.auth.updateMe({
          nickname: userForm.value.nickname,
          email: userForm.value.email,
          phone: userForm.value.phone,
          target_position: userForm.value.target_position,
          target_city: userForm.value.target_city,
          expected_salary_min: userForm.value.expected_salary_min,
        });
        ElMessage.success('用户信息已更新');
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function resetPassword() {
      if (pwdForm.value.new_password !== pwdForm.value.confirm) {
        ElMessage.error('两次密码不一致');
        return;
      }
      try {
        await API.auth.resetPassword({
          old_password: pwdForm.value.old_password,
          new_password: pwdForm.value.new_password,
        });
        ElMessage.success('密码已重置');
        pwdForm.value = { old_password: '', new_password: '', confirm: '' };
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    async function testAi() {
      testing.value = true;
      try {
        const data = await API.system.testAi();
        if (data.success) {
          ElMessage.success(`DeepSeek 连接成功：${data.response.response || ''}`);
        } else {
          ElMessage.error(data.message);
        }
      } catch (e) {
        ElMessage.error(e.message);
      } finally {
        testing.value = false;
      }
    }

    onMounted(() => {
      loadConfig();
      loadUser();
    });

    return {
        config, userForm, pwdForm, loading, testing,
        loadConfig, loadUser, saveUser, resetPassword, testAi,
      };
  },
  template: `
    <div>
      <div class="page-title">系统设置</div>

      <el-card class="section-card">
        <template #header><strong>DeepSeek AI 配置状态</strong></template>
        <div v-if="config">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="配置状态">
              <el-tag :type="config.deepseek.configured ? 'success' : 'danger'" size="small">
                {{ config.deepseek.configured ? '已配置' : '未配置' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="模型">{{ config.deepseek.model }}</el-descriptions-item>
            <el-descriptions-item label="API 地址">{{ config.deepseek.base_url }}</el-descriptions-item>
            <el-descriptions-item label="最大上下文">{{ config.deepseek.max_context_tokens }} tokens</el-descriptions-item>
          </el-descriptions>
          <div style="margin-top:12px;display:flex;gap:12px;">
            <el-button type="primary" :loading="testing" @click="testAi"><el-icon><Connection /></el-icon> 测试连接</el-button>
            <el-alert v-if="!config.deepseek.configured" type="warning" :closable="false" style="flex:1;">
              请在 config.yaml 中填入 DeepSeek API Key 后重启服务
            </el-alert>
          </div>
        </div>
      </el-card>

      <el-card class="section-card">
        <template #header><strong>个人信息</strong></template>
        <el-form :model="userForm" label-width="120px">
          <el-form-item label="用户名">
            <el-input v-model="userForm.username" disabled></el-input>
          </el-form-item>
          <el-form-item label="昵称"><el-input v-model="userForm.nickname"></el-input></el-form-item>
          <el-form-item label="邮箱"><el-input v-model="userForm.email"></el-input></el-form-item>
          <el-form-item label="手机号"><el-input v-model="userForm.phone"></el-input></el-form-item>
          <el-form-item label="目标岗位"><el-input v-model="userForm.target_position"></el-input></el-form-item>
          <el-form-item label="期望城市"><el-input v-model="userForm.target_city"></el-input></el-form-item>
          <el-form-item label="期望最低薪资"><el-input-number v-model="userForm.expected_salary_min" :min="0" :step="1000"></el-input-number> 元/月</el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveUser">保存</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card>
        <template #header><strong>重置密码</strong></template>
        <el-form :model="pwdForm" label-width="120px">
          <el-form-item label="原密码"><el-input v-model="pwdForm.old_password" type="password" show-password></el-input></el-form-item>
          <el-form-item label="新密码"><el-input v-model="pwdForm.new_password" type="password" show-password></el-input></el-form-item>
          <el-form-item label="确认新密码"><el-input v-model="pwdForm.confirm" type="password" show-password></el-input></el-form-item>
          <el-form-item>
            <el-button type="primary" @click="resetPassword">重置密码</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  `
};
