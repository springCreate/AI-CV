/**
 * 主应用入口
 */
const { createApp, ref, computed, onMounted, reactive, nextTick } = Vue;
const { ElMessage, ElMessageBox, ElNotification } = ElementPlus;

const App = {
  setup() {
    const isLoggedIn = ref(!!API.getToken());
    const currentUser = ref(API.getUser() || {});
    const authTab = ref('login');
    const authLoading = ref(false);
    const currentMenu = ref('dashboard');
    const loginForm = ref(null);
    const registerForm = ref(null);

    const loginData = reactive({ username: '', password: '' });
    const registerData = reactive({ username: '', nickname: '', password: '', confirmPassword: '' });

    const loginRules = {
      username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
      password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
    };
    const registerRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 32, message: '长度 3-32 位', trigger: 'blur' },
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, max: 64, message: '长度 6-64 位', trigger: 'blur' },
      ],
      confirmPassword: [
        { required: true, message: '请再次输入密码', trigger: 'blur' },
        {
          validator: (rule, value, callback) => {
            if (value !== registerData.password) callback(new Error('两次密码不一致'));
            else callback();
          }, trigger: 'blur',
        },
      ],
    };

    // 系统状态
    const mockMode = ref(false);
    const aiConfigured = ref(false);
    const newRemindersCount = ref(0);

    // 组件映射
    const componentMap = {
      'dashboard': 'DashboardPage',
      'resume': 'ResumePage',
      'template': 'TemplatePage',
      'job': 'JobPage',
      'interview': 'InterviewPage',
      'blacklist': 'BlacklistPage',
      'settings': 'SettingsPage',
    };
    const currentPageComponent = computed(() => componentMap[currentMenu.value] || 'DashboardPage');

    async function handleLogin() {
      try {
        await loginForm.value.validate();
        authLoading.value = true;
        const data = await API.auth.login({ username: loginData.username, password: loginData.password });
        API.setToken(data.token);
        API.setUser(data.user);
        currentUser.value = data.user;
        isLoggedIn.value = true;
        ElMessage.success('登录成功');
        loadSystemStatus();
      } catch (e) {
        if (e.message) ElMessage.error(e.message);
      } finally {
        authLoading.value = false;
      }
    }

    async function handleRegister() {
      try {
        await registerForm.value.validate();
        authLoading.value = true;
        const data = await API.auth.register({
          username: registerData.username,
          password: registerData.password,
          nickname: registerData.nickname,
        });
        API.setToken(data.token);
        API.setUser(data.user);
        currentUser.value = data.user;
        isLoggedIn.value = true;
        ElMessage.success('注册成功');
        loadSystemStatus();
      } catch (e) {
        if (e.message) ElMessage.error(e.message);
      } finally {
        authLoading.value = false;
      }
    }

    function handleLogout() {
      API.setToken(null);
      API.setUser(null);
      currentUser.value = {};
      isLoggedIn.value = false;
      currentMenu.value = 'dashboard';
      ElMessage.success('已退出登录');
    }

    function handleMenuSelect(index) {
      currentMenu.value = index;
    }

    function handleUserCommand(cmd) {
      if (cmd === 'logout') handleLogout();
      else if (cmd === 'settings') currentMenu.value = 'settings';
    }

    async function loadSystemStatus() {
      try {
        const cfg = await API.system.config();
        mockMode.value = cfg.mock_mode;
        aiConfigured.value = cfg.deepseek.configured;
      } catch (e) {
        // 静默失败
      }
    }

    async function loadNewReminders() {
      try {
        const data = await API.job.newReminders();
        newRemindersCount.value = 0;
        if (data.count === 0) {
          ElMessage.info('暂无新岗位提醒');
          return;
        }
        ElNotification({
          title: `发现 ${data.count} 个新高匹配岗位`,
          message: data.items.slice(0, 5).map(i => `• ${i.job.company} - ${i.job.title}（${i.match_score}分）`).join('\n'),
          type: 'success',
          duration: 10000,
        });
        if (currentMenu.value !== 'job') currentMenu.value = 'job';
      } catch (e) {
        ElMessage.error(e.message);
      }
    }

    onMounted(async () => {
      if (isLoggedIn.value) {
        try {
          const u = await API.auth.me();
          currentUser.value = u;
          API.setUser(u);
        } catch (e) {
          isLoggedIn.value = false;
        }
        loadSystemStatus();
      }
    });

    return {
      isLoggedIn, currentUser, authTab, authLoading,
      loginData, registerData, loginRules, registerRules,
      loginForm, registerForm,
      currentMenu, currentPageComponent,
      mockMode, aiConfigured, newRemindersCount,
      handleLogin, handleRegister, handleLogout,
      handleMenuSelect, handleUserCommand,
      loadNewReminders,
      Bell: ElementPlusIconsVue.Bell,
    };
  },
  template: document.getElementById('app').innerHTML,
};

const app = createApp(App);
app.use(ElementPlus);
for (const [key, comp] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, comp);
}
// 注册各页面组件
app.component('DashboardPage', DashboardPage);
app.component('ResumePage', ResumePage);
app.component('TemplatePage', TemplatePage);
app.component('JobPage', JobPage);
app.component('InterviewPage', InterviewPage);
app.component('BlacklistPage', BlacklistPage);
app.component('SettingsPage', SettingsPage);

app.mount('#app');
