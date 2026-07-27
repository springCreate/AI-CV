"""
面试题生成服务
"""
import logging
from typing import List, Dict

from app.extensions import db
from app.models.resume import Resume
from app.models.job import Job
from app.models.interview import InterviewQuestion
from app.services.ai_service import DeepSeekService

logger = logging.getLogger(__name__)


class InterviewService:
    """面试题生成服务"""

    @staticmethod
    def generate_questions(resume: Resume, job: Job) -> List[Dict]:
        """
        根据岗位JD和个人简历生成面试问题

        Returns:
            [{
                "question": "问题内容",
                "type": "behavioral|technical|project|skill|culture",
                "difficulty": "easy|medium|hard",
                "key_points": ["考察点1", "考察点2"],
                "answer_approach": "回答思路",
                "sample_answer": "示例答案",
                "bonus_points": ["加分点1", "加分点2"]
            }]
        """
        resume_data = resume.to_dict()
        skills = [s.get("name", "") for s in resume_data.get("skills", [])]
        projects = resume_data.get("projects", [])
        experiences = resume_data.get("experiences", [])

        system_prompt = """你是资深技术面试官和职业规划专家。请根据候选人简历和岗位JD，预测面试官可能提问的问题，并提供详细的回答思路和示例答案。

题目类型说明：
- behavioral：行为面试题（考察软技能、职业素养）
- technical：技术考察题（考察专业技能、技术深度）
- project：项目经验题（考察项目经历、解决问题能力）
- skill：技能深挖题（针对特定技能的深入考察）
- culture：文化匹配题（考察价值观、团队适配）

输出格式：严格返回 JSON 数组，每个问题包含以下字段：
{
  "question": "问题内容",
  "type": "题目类型",
  "difficulty": "easy|medium|hard",
  "key_points": ["考察要点1", "考察要点2"],
  "answer_approach": "回答思路和结构",
  "sample_answer": "示例答案",
  "bonus_points": ["加分点1", "加分点2"]
}

要求：
1. 生成 8-10 道问题，覆盖不同类型
2. 问题要针对候选人简历和岗位JD的特点
3. 回答思路要具体可执行
4. 示例答案要真实、有说服力"""

        user_content = f"""# 岗位信息
岗位名称：{job.title}
公司：{job.company}
薪资：{job.salary_text or '面议'}
工作年限要求：{job.work_years or '不限'}
学历要求：{job.education or '不限'}

## 岗位JD
{job.jd_text or '暂无详细JD'}

# 候选人简历摘要
姓名：{resume_data.get('real_name', '未知')}
目标岗位：{resume_data.get('target_position', '未知')}

## 专业技能
{', '.join(skills) if skills else '未填写'}

## 项目经历（共 {len(projects)} 个）
""" + "\n".join([
            f"- {p.get('name', '')}（{p.get('role', '')}）：{p.get('description', '')[:200]}"
            for p in projects[:5]
        ]) + f"""

## 工作/实习经历（共 {len(experiences)} 段）
""" + "\n".join([
            f"- {e.get('company', '')} {e.get('position', '')}：{e.get('description', '')[:200]}"
            for e in experiences[:5]
        ]) + f"""

请根据以上信息生成面试题。"""

        try:
            result = DeepSeekService.chat_json(system_prompt, user_content, temperature=0.4)
            if isinstance(result, list):
                return result[:10]
            return []
        except Exception as e:
            logger.exception("面试题生成失败")
            return InterviewService._fallback_questions(resume, job)

    @staticmethod
    def _fallback_questions(resume: Resume, job: Job) -> List[Dict]:
        """AI失败时的兜底问题"""
        resume_data = resume.to_dict()
        skills = [s.get("name", "") for s in resume_data.get("skills", [])]
        skills_str = ", ".join(skills[:3]) if skills else "相关技能"

        questions = [
            {
                "question": f"请介绍一下你自己，以及你为什么申请 {job.title} 这个岗位？",
                "type": "behavioral",
                "difficulty": "easy",
                "key_points": ["自我认知", "岗位匹配度", "求职动机"],
                "answer_approach": "简单介绍背景 -> 突出与岗位相关的技能和经验 -> 说明为什么想加入该公司",
                "sample_answer": f"您好，我是一名具有多年经验的技术从业者，主要擅长 {skills_str}。我对 {job.title} 岗位很感兴趣，因为我的技能背景与岗位要求高度匹配，而且我一直向往贵公司的技术氛围和发展机会。",
                "bonus_points": ["提到公司文化或产品", "展示对行业的理解"],
            },
            {
                "question": f"请详细描述一个你参与的项目，你在其中的角色和贡献是什么？",
                "type": "project",
                "difficulty": "medium",
                "key_points": ["项目经验", "技术能力", "团队协作"],
                "answer_approach": "用 STAR 法则：背景 -> 任务 -> 行动 -> 结果",
                "sample_answer": "在XX项目中，我负责核心模块的设计与开发...",
                "bonus_points": ["量化成果", "提到技术难点和解决方案"],
            },
            {
                "question": f"你如何学习新的技术？请举例说明你最近学习的一项新技术。",
                "type": "skill",
                "difficulty": "medium",
                "key_points": ["学习能力", "技术热情", "自我驱动"],
                "answer_approach": "描述学习方法 -> 举例具体技术 -> 说明应用场景",
                "sample_answer": "我通过官方文档、技术博客和实践项目来学习新技术...",
                "bonus_points": ["展示持续学习的习惯", "提到具体的学习资源"],
            },
        ]
        return questions

    @staticmethod
    def save_questions(user_id: int, resume_id: int, job_id: int, questions: List[Dict]) -> int:
        """保存面试问题到数据库"""
        saved = 0
        for q in questions:
            question = InterviewQuestion(
                user_id=user_id,
                resume_id=resume_id,
                job_id=job_id,
                question=q.get("question", ""),
                type=q.get("type", "behavioral"),
                difficulty=q.get("difficulty", "medium"),
                key_points=",".join(q.get("key_points", [])),
                answer_approach=q.get("answer_approach", ""),
                sample_answer=q.get("sample_answer", ""),
                bonus_points=",".join(q.get("bonus_points", [])),
            )
            db.session.add(question)
            saved += 1
        db.session.commit()
        return saved
