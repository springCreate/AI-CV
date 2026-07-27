"""
招聘平台数据层

设计原则：
1. 国内招聘平台（BOSS直聘、智联、前程无忧等）均未开放个人开发者岗位查询 API
2. 本模块保留 Mock 数据适配器用于演示，同时支持手动录入真实岗位
3. 严格遵守合规要求：无爬虫、无模拟登录、无自动投递
4. 所有来源返回统一的 JobRawItem 结构
"""
import logging
import random
import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class JobRawItem:
    """统一的岗位原始数据结构"""

    def __init__(self, data: Dict[str, Any]):
        self.platform = data.get("platform", "manual")
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


class MockAdapter:
    """
    Mock 数据适配器：生成演示数据，保证完整流程可演示
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
    """岗位数据源管理器"""

    def __init__(self):
        self.mock_adapter = MockAdapter()

    def fetch_all_jobs(self, keyword: str, city: str = "", page: int = 1,
                       page_size: int = 20) -> List[JobRawItem]:
        """拉取岗位（当前仅支持 Mock 演示数据）"""
        try:
            items = self.mock_adapter.fetch_jobs(keyword, city, page, page_size)
            logger.info("Mock 模式返回 %d 个岗位", len(items))
            return items
        except Exception as e:
            logger.exception("Mock 拉取失败: %s", e)
            return []
