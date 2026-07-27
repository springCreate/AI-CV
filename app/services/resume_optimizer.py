"""
简历 AI 优化器

实现 PRD 3.2 节五大维度优化：
1. 岗位关键词适配改写
2. 无关内容筛选删减
3. 岗位技能补充
4. 专属自我评价生成
5. 标准化排版优化（STAR 法则）

重要：仅生成修改建议，必须经用户手动确认后才能应用
"""
import json
import logging
from typing import Dict, Any

from app.extensions import db
from app.models.resume import (
    Resume, ResumeEducation, ResumeExperience,
    ResumeProject, ResumeSkill, ResumeOptimizationLog
)
from app.services.ai_service import DeepSeekService

logger = logging.getLogger(__name__)


class ResumeOptimizer:
    """简历 AI 优化器"""

    SYSTEM_PROMPT = """你是一名资深猎头与简历优化专家。请基于目标岗位 JD 与用户求职诉求，对简历进行五维度智能优化。

输出要求：
1. 严格输出 JSON 格式
2. 每个维度给出"建议项列表"，每项包含：target(目标对象)、original(原文)、suggested(建议修改为)、reason(修改理由)
3. 不修改事实，仅做话术优化、关键词植入、结构重组
4. 删减建议需谨慎，仅删除与目标岗位明显无关的内容
5. 自我评价要融合用户求职诉求（薪资、作息、地域）+岗位招聘要求

JSON 输出结构：
{
  "keyword_suggestions": [
    {"target": "经历对象标识（如 experience:1）", "field": "description", "original": "原文片段", "suggested": "改写后内容", "reason": "理由"}
  ],
  "deletion_suggestions": [
    {"target": "experience:2", "reason": "与目标岗位无关", "detail": "建议删除的具体内容"}
  ],
  "skill_suggestions": [
    {"name": "建议补充的技能名", "level": "熟悉/熟练", "category": "工具/框架", "reason": "岗位刚需，用户具备能力但未显性标注"}
  ],
  "evaluation_suggestions": {
    "suggested": "建议的自我评价全文",
    "highlights": ["要点1", "要点2"]
  },
  "format_suggestions": [
    {"target": "experience:1", "issues": ["未使用 STAR 结构", "缺少量化结果"], "suggested": "重构后内容"}
  ]
}"""

    @classmethod
    def generate_suggestions(cls, resume: Resume, jd: str, template=None) -> Dict[str, Any]:
        """
        生成五维度优化建议

        Args:
            resume: 简历对象
            jd: 目标岗位 JD
            template: 求职诉求模板（可选）

        Returns:
            {keyword_suggestions, deletion_suggestions, skill_suggestions,
             evaluation_suggestions, format_suggestions}（均为 JSON 字符串）
        """
        # 构建简历摘要
        resume_data = resume.to_dict()

        # 为各经历项建立索引标识
        for i, exp in enumerate(resume_data.get("experiences", []), 1):
            exp["_index"] = f"experience:{i}"
        for i, proj in enumerate(resume_data.get("projects", []), 1):
            proj["_index"] = f"project:{i}"

        # 构建求职诉求
        appeal_text = ""
        if template:
            t = template.to_dict()
            appeal_text = f"""求职诉求：
- 目标岗位：{t.get('position', '未指定')}
- 期望城市：{', '.join(t.get('cities', []))}
- 期望薪资：{t.get('salary_min', '未指定')}-{t.get('salary_max', '未指定')}元
- 工作类型：{t.get('job_type', '不限')}
- 双休要求：{'是' if t.get('require_weekend_off') else '不限'}
- 不加班：{'是' if t.get('require_no_overtime') else '不限'}
- 包住宿：{'是' if t.get('require_accommodation') else '不限'}
- 其他要求：{t.get('other_requirements', '无')}
- 关键词：{', '.join(t.get('keywords', []))}"""

        user_content = f"""# 简历内容
{json.dumps(resume_data, ensure_ascii=False, indent=2)}

# 目标岗位 JD
{jd}

# 用户求职诉求
{appeal_text or '未提供'}

请基于以上信息，输出五维度优化建议 JSON。"""

        result = DeepSeekService.chat_json(cls.SYSTEM_PROMPT, user_content, temperature=0.4)

        # 序列化为字符串存储
        return {
            "keyword_suggestions": json.dumps(result.get("keyword_suggestions", []), ensure_ascii=False),
            "deletion_suggestions": json.dumps(result.get("deletion_suggestions", []), ensure_ascii=False),
            "skill_suggestions": json.dumps(result.get("skill_suggestions", []), ensure_ascii=False),
            "evaluation_suggestions": json.dumps(result.get("evaluation_suggestions", {}), ensure_ascii=False),
            "format_suggestions": json.dumps(result.get("format_suggestions", []), ensure_ascii=False),
        }

    @classmethod
    def apply_suggestions(cls, resume: Resume, log: ResumeOptimizationLog,
                          fields: Dict[str, Any]):
        """
        应用用户确认的优化建议

        Args:
            resume: 简历对象
            log: 优化记录
            fields: 用户确认应用的字段
                - self_evaluation: 新的自我评价
                - add_skills: [{name, level, category}] 待补充技能
                - update_experiences: [{id, description}] 更新工作经历描述
                - update_projects: [{id, description}] 更新项目描述
                - delete_experiences: [id] 删除的工作经历 ID
                - delete_projects: [id] 删除的项目 ID
        """
        # 1. 更新自我评价
        if fields.get("self_evaluation"):
            resume.self_evaluation = fields["self_evaluation"]

        # 2. 补充技能
        for sk in fields.get("add_skills", []):
            if sk.get("name"):
                existing = ResumeSkill.query.filter_by(
                    resume_id=resume.id, name=sk["name"]
                ).first()
                if not existing:
                    db.session.add(ResumeSkill(
                        resume_id=resume.id,
                        name=sk["name"],
                        level=sk.get("level", "熟悉"),
                        category=sk.get("category", "其他"),
                    ))

        # 3. 更新工作经历描述
        for upd in fields.get("update_experiences", []):
            if upd.get("id"):
                exp = ResumeExperience.query.filter_by(
                    id=upd["id"], resume_id=resume.id
                ).first()
                if exp and upd.get("description"):
                    exp.description = upd["description"]

        # 4. 更新项目描述
        for upd in fields.get("update_projects", []):
            if upd.get("id"):
                proj = ResumeProject.query.filter_by(
                    id=upd["id"], resume_id=resume.id
                ).first()
                if proj and upd.get("description"):
                    proj.description = upd["description"]

        # 5. 删除无关经历
        for eid in fields.get("delete_experiences", []):
            exp = ResumeExperience.query.filter_by(id=eid, resume_id=resume.id).first()
            if exp:
                db.session.delete(exp)
        for pid in fields.get("delete_projects", []):
            proj = ResumeProject.query.filter_by(id=pid, resume_id=resume.id).first()
            if proj:
                db.session.delete(proj)

        db.session.commit()
        logger.info("简历 %s 优化建议已应用", resume.id)
