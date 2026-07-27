/**
 * API 请求封装
 */
const API = (function() {
  const BASE = '/api';

  function getToken() {
    return localStorage.getItem('token') || '';
  }

  function setToken(token) {
    if (token) localStorage.setItem('token', token);
    else localStorage.removeItem('token');
  }

  function getUser() {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
  }

  function setUser(user) {
    if (user) localStorage.setItem('user', JSON.stringify(user));
    else localStorage.removeItem('user');
  }

  async function request(method, url, data = null, isFormData = false) {
    const headers = { 'Authorization': `Bearer ${getToken()}` };
    if (!isFormData && data) headers['Content-Type'] = 'application/json';

    const opts = { method, headers };
    if (data) {
      opts.body = isFormData ? data : JSON.stringify(data);
    }

    try {
      const resp = await fetch(BASE + url, opts);
      const result = await resp.json();
      if (resp.status === 401) {
        setToken(null); setUser(null);
        if (window.location.pathname !== '/') {
          window.location.href = '/';
        }
        throw new Error(result.message || '未登录或登录已过期');
      }
      if (!result.success) {
        throw new Error(result.message || '请求失败');
      }
      return result.data;
    } catch (e) {
      if (e.message === 'Failed to fetch') {
        throw new Error('网络连接失败，请检查后端服务是否启动');
      }
      throw e;
    }
  }

  return {
    // 认证
    auth: {
      register: (data) => request('POST', '/auth/register', data),
      login: (data) => request('POST', '/auth/login', data),
      me: () => request('GET', '/auth/me'),
      updateMe: (data) => request('PUT', '/auth/me', data),
      resetPassword: (data) => request('PUT', '/auth/password', data),
    },
    // 简历
    resume: {
      list: () => request('GET', '/resume'),
      get: (id) => request('GET', `/resume/${id}`),
      create: (data) => request('POST', '/resume', data),
      update: (id, data) => request('PUT', `/resume/${id}`, data),
      delete: (id) => request('DELETE', `/resume/${id}`),
      upload: (formData) => request('POST', '/resume/upload', formData, true),
      reparse: (id) => request('POST', `/resume/${id}/reparse`),
      // 子模块
      addEducation: (rid, data) => request('POST', `/resume/${rid}/education`, data),
      addExperience: (rid, data) => request('POST', `/resume/${rid}/experience`, data),
      addProject: (rid, data) => request('POST', `/resume/${rid}/project`, data),
      addSkill: (rid, data) => request('POST', `/resume/${rid}/skill`, data),
      updateEducation: (rid, iid, data) => request('PUT', `/resume/${rid}/education/${iid}`, data),
      updateExperience: (rid, iid, data) => request('PUT', `/resume/${rid}/experience/${iid}`, data),
      updateProject: (rid, iid, data) => request('PUT', `/resume/${rid}/project/${iid}`, data),
      updateSkill: (rid, iid, data) => request('PUT', `/resume/${rid}/skill/${iid}`, data),
      deleteEducation: (rid, iid) => request('DELETE', `/resume/${rid}/education/${iid}`),
      deleteExperience: (rid, iid) => request('DELETE', `/resume/${rid}/experience/${iid}`),
      deleteProject: (rid, iid) => request('DELETE', `/resume/${rid}/project/${iid}`),
      deleteSkill: (rid, iid) => request('DELETE', `/resume/${rid}/skill/${iid}`),
      // 优化
      optimize: (id, data) => request('POST', `/resume/${id}/optimize`, data),
      applyOptimization: (id, logId, data) => request('POST', `/resume/${id}/optimize/${logId}/apply`, data),
      // PDF
      exportPdf: (id, data) => request('POST', `/resume/${id}/export-pdf`, data),
    },
    // 求职诉求模板
    template: {
      list: () => request('GET', '/template'),
      get: (id) => request('GET', `/template/${id}`),
      create: (data) => request('POST', '/template', data),
      update: (id, data) => request('PUT', `/template/${id}`, data),
      delete: (id) => request('DELETE', `/template/${id}`),
      setDefault: (id) => request('POST', `/template/${id}/set-default`),
    },
    // 岗位
    job: {
      list: (params) => request('GET', '/job' + (params ? '?' + new URLSearchParams(params) : '')),
      get: (id) => request('GET', `/job/${id}`),
      delete: (id) => request('DELETE', `/job/${id}`),
      fetchMatch: (data) => request('POST', '/job/fetch-match', data),
      matchRecords: (params) => request('GET', '/job/match-records' + (params ? '?' + new URLSearchParams(params) : '')),
      newReminders: () => request('GET', '/job/new-reminders'),
      markRead: (id) => request('POST', `/job/${id}/mark-read`),
      platformsStatus: () => request('GET', '/job/platforms/status'),
      // 黑名单
      blacklist: () => request('GET', '/job/blacklist'),
      addBlacklist: (data) => request('POST', '/job/blacklist', data),
      removeBlacklist: (id) => request('DELETE', `/job/blacklist/${id}`),
    },
    // 投递
    application: {
      list: (params) => request('GET', '/application' + (params ? '?' + new URLSearchParams(params) : '')),
      get: (id) => request('GET', `/application/${id}`),
      create: (data) => request('POST', '/application', data),
      update: (id, data) => request('PUT', `/application/${id}`, data),
      delete: (id) => request('DELETE', `/application/${id}`),
      markApplied: (id) => request('POST', `/application/${id}/mark-applied`),
      generateScript: (jobId, data) => request('POST', `/application/${jobId}/generate-script`, data),
      batchGenerate: (data) => request('POST', '/application/batch-generate-scripts', data),
      exportExcel: (data) => request('POST', '/application/export-excel', data),
      stats: () => request('GET', '/application/stats'),
    },
    // 系统
    system: {
      health: () => request('GET', '/system/health'),
      config: () => request('GET', '/system/config'),
      testAi: () => request('POST', '/system/ai/test'),
    },
    // 工具
    getToken, setToken, getUser, setUser,
    downloadUrl: (path) => BASE + path.replace(BASE, ''),
  };
})();
