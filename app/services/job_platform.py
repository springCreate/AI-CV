"""
招聘平台 API 适配层

设计原则：
1. 统一抽象 BasePlatformAdapter，各平台实现各自的 fetch_jobs 方法
2. 平台未配置 API 时走 Mock 模式，返回演示数据，保证完整流程可演示
3. 严格遵守 PRD：仅查询公开岗位，无投递能力，无爬虫，无模拟登录
4. 所有平台返回统一的 JobRawItem 结构
"""
import logging
import random
import datetime
from typing import List, Dict, Any
from abc import ABC, abstractmethod

import requests

logger = logging.getLogger(__name__)


class JobRawItem:
    """统一的岗位原始数据结构"""

    def __init__(self, data: Dict[str, Any]):
        self.platform = data.get("platform", "unknown")
        self.platform_job_id = data.get("platform_job_id", "")
        self.title = data.get("title", "")
        self.company = data.get("company", "")
        self.city = data.get("city", "")
        self.district = data.get("district", "")
        self.salary_min = data.get("salary_min")
        self.salary_max = data.get("salary_max")
        self.salary_text = data.get("salary_text", "")
        self.work_years = data.get("work_years", "")
        self.education = data.get("education", "")
        self.job_type = data.get("job_type", "全职")
        self.is_weekend_off = data.get("is_weekend_off")
        self.has_accommodation = data.get("has_accommodation")
        self.jd_text = data.get("jd_text", "")
        self.company_size = data.get("company_size", "")
        self.company_industry = data.get("company_industry", "")
        self.hr_name = data.get("hr_name", "")
        self.publish_time = data.get("publish_time")
        self.job_url = data.get("job_url", "")

    def to_dict(self):
        return {
            "platform": self.platform,
            "platform_job_id": self.platform_job_id,
            "title": self.title,
            "company": self.company,
            "city": self.city,
            "district": self.district,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_text": self.salary_text,
            "work_years": self.work_years,
            "education": self.education,
            "job_type": self.job_type,
            "is_weekend_off": self.is_weekend_off,
            "has_accommodation": self.has_accommodation,
            "jd_text": self.jd_text,
            "company_size": self.company_size,
            "company_industry": self.company_industry,
            "hr_name": self.hr_name,
            "publish_time": self.publish_time,
            "job_url": self.job_url,
        }


class BasePlatformAdapter(ABC):
    """招聘平台适配器基类"""

    platform_name = "base"

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", False)

    @abstractmethod
    def fetch_jobs(self, keyword: str, city: str = "", page: int = 1,
                   page_size: int = 20) -> List[JobRawItem]:
        """拉取岗位列表"""
        pass

    def is_available(self) -> bool:
        return self.enabled


class BossAdapter(BasePlatformAdapter):
    """BOSS直聘适配器（需平台开放 API，目前多为 Mock 演示）"""
    platform_name = "boss"

    def fetch_jobs(self, keyword: str, city: str = "", page: int = 1,
                   page_size: int = 20) -> List[JobRawItem]:
        if not self.is_available():
            return []
        # 真实接入示例（占位）：
        # url = f"{self.config['base_url']}/jobs/search"
        # params = {"query": keyword, "city": city, "page": page, "size": page_size}
        # headers = {"Authorization": f"Bearer {self.config['app_key']}"}
        # resp = requests.get(url, params=params, headers=headers, timeout=15)
        # return self._parse_response(resp.json())
        logger.warning("BOSS直聘未配置真实 API，跳过")
        return []


class ZhilianAdapter(BasePlatformAdapter):
    """智联招聘适配器"""
    platform_name = "zhilian"

    def fetch_jobs(self, keyword: str, city: str = "", page: int = 1,
                   page_size: int = 20) -> List[JobRawItem]:
        if not self.is_available():
            return []
        logger.warning("智联招聘未配置真实 API，跳过")
        return []


class Job51Adapter(BasePlatformAdapter):
    """前程无忧适配器"""
    platform_name = "51job"

    def fetch_jobs(self, keyword: str, city: str = "", page: int = 1,
                   page_size: int = 20) -> List[JobRawItem]:
        if not self.is_available():
            return []
        logger.warning("前程无忧未配置真实 API，跳过")
        return []


class ShixisengAdapter(BasePlatformAdapter):
    """实习僧适配器"""
    platform_name = "shixiseng"

    def fetch_jobs(self, keyword: str, city: str = "", page: int = 1,
                   page_size: int = 20) -> List[JobRawItem]:
        if not self.is_available():
            return []
        logger.warning("实习僧未配置真实 API，跳过")
        return []


class MockAdapter(BasePlatformAdapter):
    """
    Mock 数据适配器：当所有平台 API 未启用时，生成演示数据
    保证完整流程（匹配、打分、投递辅助）可演示
    """
    platform_name = "mock"

    # 演示公司池
    DEMO_COMPANIES = [
        ("字节跳动", "10000人以上", "互联网"),
        ("腾讯", "10000人以上", "互联网"),
        ("阿里巴巴", "10000人以上", "互联网"),
        ("美团", "10000人以上", "互联网"),
        ("百度", "10000人以上", "互联网"),
        ("网易", "5000-10000人", "互联网"),
        ("京东", "10000人以上", "电商"),
        ("小米", "10000人以上", "智能硬件"),
        ("华为", "10000人以上", "通信"),
        ("中软国际", "5000-10000人", "IT服务"),
        ("浪潮信息", "1000-5000人", "服务器"),
        ("商汤科技", "1000-5000人", "人工智能"),
        ("旷视科技", "500-1000人", "人工智能"),
        ("海康威视", "10000人以上", "安防"),
        ("大疆创新", "5000-10000人", "无人机"),
    ]

    DEMO_CITIES = ["北京", "上海", "深圳", "杭州", "广州", "成都", "南京", "武汉", "天津", "西安"]

    def is_available(self) -> bool:
        return True  # Mock 始终可用

    def fetch_jobs(self, keyword: str, city: str = "", page: int = 1,
                   page_size: int = 20) -> List[JobRawItem]:
        logger.info("Mock 模式生成演示岗位: keyword=%s, city=%s", keyword, city)
        random.seed(hash(keyword + city) + page)

        items = []
        count = min(page_size, 15)
        for i in range(count):
            company_info = random.choice(self.DEMO_COMPANIES)
            city_name = city if city else random.choice(self.DEMO_CITIES)
            salary_min = random.choice([6000, 7000, 8000, 10000, 12000, 15000, 18000, 20000, 25000])
            salary_max = salary_min + random.choice([3000, 5000, 8000, 10000])

            title_variants = [
                f"{keyword}工程师", f"高级{keyword}工程师", f"{keyword}专员",
                f"初级{keyword}", f"{keyword}实习生", f"{keyword}主管",
            ]
            title = random.choice(title_variants) if keyword else "软件工程师"

            is_weekend_off = random.random() > 0.3
            has_accom = random.random() > 0.7
            job_type = random.choice(["全职", "全职", "全职", "实习"])

            jd_templates = [
                f"岗位职责：\n1. 负责{keyword}相关工作；\n2. 参与产品需求分析与方案设计；\n3. 编写相关技术文档；\n4. 与团队协作完成项目目标。\n\n任职要求：\n1. 本科及以上学历，计算机相关专业；\n2. 熟悉{keyword}相关技术栈；\n3. 具备良好的沟通能力与团队合作精神；\n4. 有较强的问题分析与解决能力。",
                f"工作内容：\n- 负责{keyword}模块的设计与实现\n- 持续优化系统性能与稳定性\n- 参与代码评审与技术分享\n\n要求：\n- 1-3年相关工作经验\n- 熟练掌握{keyword}核心技术\n- 熟悉 Linux 操作系统\n- 有大厂经验优先",
                f"【岗位描述】\n1. 主导{keyword}方向的项目落地\n2. 跨部门协作推动业务发展\n3. 输出技术方案与最佳实践\n\n【任职资格】\n- 计算机/软件工程相关专业本科及以上\n- 精通{keyword}领域知识\n- 具备{'3-5' if random.random()>0.5 else '1-3'}年工作经验\n- 加分项：开源贡献、技术博客",
            ]

            publish_hours_ago = random.randint(1, 72)
            publish_time = datetime.datetime.utcnow() - datetime.timedelta(hours=publish_hours_ago)

            item = JobRawItem({
                "platform": "mock",
                "platform_job_id": f"mock_{page}_{i}_{random.randint(1000, 9999)}",
                "title": title,
                "company": company_info[0],
                "city": city_name,
                "district": random.choice(["朝阳区", "海淀区", "西城区", "浦东新区", "南山区", "余杭区", ""]),
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_text": f"{salary_min//1000}-{salary_max//1000}K",
                "work_years": random.choice(["不限", "1-3年", "1-3年", "3-5年", "3-5年", "5-10年"]),
                "education": random.choice(["本科", "本科", "本科", "硕士", "大专"]),
                "job_type": job_type,
                "is_weekend_off": is_weekend_off,
                "has_accommodation": has_accom,
                "jd_text": random.choice(jd_templates),
                "company_size": company_info[1],
                "company_industry": company_info[2],
                "hr_name": f"HR-{random.choice(['小李', '小王', '张经理', '刘主管', '陈老师'])}",
                "publish_time": publish_time,
                "job_url": f"https://www.example.com/jobs/mock_{page}_{i}",
            })
            items.append(item)
        return items


class PlatformManager:
    """平台适配器管理器"""

    def __init__(self, platforms_config: Dict[str, Any]):
        self.config = platforms_config
        self.adapters: Dict[str, BasePlatformAdapter] = {
            "boss": BossAdapter(platforms_config.get("boss", {})),
            "zhilian": ZhilianAdapter(platforms_config.get("zhilian", {})),
            "51job": Job51Adapter(platforms_config.get("51job", {})),
            "shixiseng": ShixisengAdapter(platforms_config.get("shixiseng", {})),
        }
        self.mock_adapter = MockAdapter({})
        self.mock_mode = platforms_config.get("mock_mode", True)

    def get_active_adapters(self) -> List[BasePlatformAdapter]:
        """获取所有启用的平台适配器"""
        active = [a for a in self.adapters.values() if a.is_available()]
        if not active and self.mock_mode:
            return [self.mock_adapter]
        return active

    def fetch_all_jobs(self, keyword: str, city: str = "", page: int = 1,
                       page_size: int = 20) -> List[JobRawItem]:
        """从所有启用平台拉取岗位"""
        all_items = []
        for adapter in self.get_active_adapters():
            try:
                items = adapter.fetch_jobs(keyword, city, page, page_size)
                all_items.extend(items)
                logger.info("平台 %s 返回 %d 个岗位", adapter.platform_name, len(items))
            except Exception as e:
                logger.exception("平台 %s 拉取失败: %s", adapter.platform_name, e)
        return all_items

    def is_mock_mode(self) -> bool:
        """是否运行在 Mock 模式"""
        if not self.mock_mode:
            return False
        return not any(a.is_available() for a in self.adapters.values())
