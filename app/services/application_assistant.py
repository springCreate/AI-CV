"""
投递辅助服务

按 PRD 6.1 节生成 AI 定制投递话术：
1. 打招呼文案（适配 BOSS直聘等平台的开场白）
2. 投递自我介绍（详细版，适配邮件/简历附带）
"""
import logging
from typing import Dict

from app.models.resume import Resume
from app.models.job import Job
from app.services.ai_service import DeepSeekService

logger = logging.getLogger(__name__)


class ApplicationAssistant:
    """投递辅助服务"""

    @staticmethod
    def generate_greeting_and_intro(resume: Resume, job: Job) -> Dict[str, str]:
        """
        为单个岗位生成专属打招呼话术 + 定制化自我介绍

        Returns:
            {"greeting": str, "self_introduction": str}
        """
        resume_data = resume.to_dict()

        system_prompt = """你是一名求职辅导专家，擅长根据候选人简历与目标岗位，生成高通过率的投递话术。

输出要求：
1. 严格输出 JSON 格式
2. greeting 控制在 80-150 字，符合 BOSS直聘等 IM 招聘平台的开场白习惯
3. self_introduction 控制在 300-500 字，结构化呈现，可作为邮件正文或附言
4. 话术要具体、真诚，避免空泛套话
5. 紧扣岗位 JD 中的核心要求，主动呼应招聘方需求
6. 不要虚构经历，只基于简历已有内容做话术优化

JSON 输出结构：
{
  "greeting": "HR 您好，我是...",
  "self_introduction": "尊敬的招聘负责人：\\n\\n您好！我是..."
}"""

        skills = [s.get("name", "") for s in resume_data.get("skills", [])]
        projects = resume_data.get("projects", [])
        experiences = resume_data.get("experiences", [])

        user_content = f"""# 候选人简历摘要
姓名：{resume_data.get('real_name', '未知')}
目标岗位：{resume_data.get('target_position', '未知')}
电话：{resume_data.get('phone', '未提供')}
邮箱：{resume_data.get('email', '未提供')}

## 专业技能
{', '.join(skills) if skills else '未填写'}

## 项目经历（共 {len(projects)} 个）
""" + "\n".join([
            f"- {p.get('name', '')}（{p.get('role', '')}）：{p.get('description', '')[:150]}"
            for p in projects[:3]
        ]) + f"""

## 工作/实习经历（共 {len(experiences)} 段）
""" + "\n".join([
            f"- {e.get('company', '')} {e.get('position', '')}（{e.get('start_date', '')}-{e.get('end_date', '')}）"
            for e in experiences[:3]
        ]) + f"""

## 自我评价
{resume_data.get('self_evaluation', '未填写')}

# 目标岗位信息
岗位名称：{job.title}
公司：{job.company}
工作地点：{job.city or '未指定'}
薪资：{job.salary_text or '面议'}
工作年限要求：{job.work_years or '不限'}

## 岗位 JD
{job.jd_text or '无'}

请基于以上信息生成专属投递话术 JSON。"""

        try:
            result = DeepSeekService.chat_json(system_prompt, user_content, temperature=0.6)
            return {
                "greeting": result.get("greeting", ""),
                "self_introduction": result.get("self_introduction", ""),
            }
        except Exception as e:
            logger.exception("AI 话术生成失败，使用兜底话术")
            real_name = resume_data.get('real_name', '候选人')
            target = resume_data.get('target_position', '目标岗位')
            return {
                "greeting": f"HR 您好，我叫{real_name}，应聘贵公司的{job.title}岗位。我有{target}相关经验，技能匹配度较高，期待能进一步沟通，谢谢！",
                "self_introduction": f"尊敬的招聘负责人：\n\n您好！我叫{real_name}，应聘{job.title}一职。\n\n我具备{target}相关背景，熟悉岗位核心技能要求，有扎实的项目与工作经验。我对贵公司{job.company}的发展方向和该岗位非常感兴趣，相信自己的能力能够胜任。\n\n期待有机会参加面试，进一步展示我的能力。\n\n谢谢！",
            }

    @staticmethod
    def batch_generate(resume: Resume, jobs: list, callback=None) -> list:
        """
        批量生成话术（含进度回调）

        Args:
            resume: 简历对象
            jobs: 岗位列表
            callback: 进度回调函数 (current, total, job) -> None

        Returns:
            [{"job_id": int, "greeting": str, "self_introduction": str, "success": bool, "error": str}]
        """
        results = []
        total = len(jobs)
        for i, job in enumerate(jobs, 1):
            try:
                content = ApplicationAssistant.generate_greeting_and_intro(resume, job)
                results.append({
                    "job_id": job.id,
                    "greeting": content["greeting"],
                    "self_introduction": content["self_introduction"],
                    "success": True,
                })
            except Exception as e:
                logger.exception("岗位 %s 话术生成失败", job.id)
                results.append({
                    "job_id": job.id,
                    "greeting": "",
                    "self_introduction": "",
                    "success": False,
                    "error": str(e),
                })
            if callback:
                callback(i, total, job)
        return results
