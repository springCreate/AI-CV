"""
岗位匹配引擎

实现 PRD 5.2 节双层匹配机制：
1. 硬性条件精准过滤（不满足直接剔除）
2. 软性技能 AI 智能打分（0-100 分）
"""
import json
import logging
import re
from typing import List, Dict, Tuple, Optional

from app.extensions import db
from app.models.resume import Resume
from app.models.template import JobTemplate
from app.models.job import Job, JobMatchRecord, Blacklist
from app.services.ai_service import DeepSeekService
from app.services.job_platform import JobRawItem, PlatformManager

logger = logging.getLogger(__name__)


class JobMatcher:
    """岗位匹配引擎"""

    @staticmethod
    def save_jobs_to_db(user_id: int, raw_items: List[JobRawItem]) -> Tuple[int, List[Job]]:
        """
        将原始岗位数据落库（去重）
        返回 (新增数量, 全部岗位列表)
        """
        new_count = 0
        all_jobs = []
        for raw in raw_items:
            # 去重：同 user + 同 platform + 同 platform_job_id
            existing = Job.query.filter_by(
                user_id=user_id,
                platform=raw.platform,
                platform_job_id=raw.platform_job_id,
            ).first()
            if existing:
                # 更新最近抓取时间
                existing.last_fetched_at = db.func.now()
                all_jobs.append(existing)
                continue

            job = Job(
                user_id=user_id,
                platform=raw.platform,
                platform_job_id=raw.platform_job_id,
                title=raw.title,
                company=raw.company,
                city=raw.city,
                district=raw.district,
                salary_min=raw.salary_min,
                salary_max=raw.salary_max,
                salary_text=raw.salary_text,
                work_years=raw.work_years,
                education=raw.education,
                job_type=raw.job_type,
                is_weekend_off=raw.is_weekend_off,
                has_accommodation=raw.has_accommodation,
                jd_text=raw.jd_text,
                company_size=raw.company_size,
                company_industry=raw.company_industry,
                hr_name=raw.hr_name,
                publish_time=raw.publish_time,
                job_url=raw.job_url,
            )
            db.session.add(job)
            db.session.flush()
            all_jobs.append(job)
            new_count += 1
        db.session.commit()
        return new_count, all_jobs

    @staticmethod
    def filter_blacklisted(user_id: int, jobs: List[Job]) -> List[Job]:
        """过滤黑名单公司"""
        blacklist = {b.company for b in Blacklist.query.filter_by(user_id=user_id).all()}
        if not blacklist:
            return jobs
        return [j for j in jobs if j.company not in blacklist]

    @staticmethod
    def hard_filter(job: Job, template: JobTemplate) -> Tuple[bool, str]:
        """
        硬性条件过滤
        返回 (是否通过, 未通过原因)
        """
        # 城市
        if template.cities:
            allowed = [c.strip() for c in template.cities.split(",") if c.strip()]
            if job.city and job.city not in allowed:
                return False, f"城市不匹配（{job.city} 不在 {','.join(allowed)}）"

        # 薪资下限
        if template.salary_min and job.salary_min:
            if job.salary_min < template.salary_min:
                return False, f"薪资不达标（{job.salary_min} < {template.salary_min}）"

        # 工作类型
        if template.job_type and job.job_type:
            if template.job_type != job.job_type:
                return False, f"工作类型不符（{job.job_type} ≠ {template.job_type})"

        # 双休
        if template.require_weekend_off and job.is_weekend_off is False:
            return False, "不满足双休要求"

        # 包住宿
        if template.require_accommodation and job.has_accommodation is False:
            return False, "不满足包住宿要求"

        # 工作年限（粗匹配：从 work_years 字符串中提取数字）
        if template.work_years_min and job.work_years and job.work_years != "不限":
            years = JobMatcher._parse_work_years(job.work_years)
            if years is not None and template.work_years_min > years:
                return False, f"工作年限不足（要求 {template.work_years_min}，岗位 {years}）"

        return True, ""

    @staticmethod
    def _parse_work_years(years_text: str) -> Optional[int]:
        """从 '3-5年' / '1-3年' 等文本中提取上限年限"""
        if not years_text:
            return None
        match = re.findall(r"(\d+)", years_text)
        if match:
            return int(match[-1])
        return None

    @staticmethod
    def soft_score(job: Job, resume: Resume, template: JobTemplate = None) -> Dict:
        """
        AI 软性打分：比对简历技能与岗位 JD，生成 0-100 分

        Returns:
            {
                "score": int,
                "summary": str,
                "missing_skills": [str],
                "details": {维度: 子分}
            }
        """
        resume_data = resume.to_dict()
        skills = [s.get("name", "") for s in resume_data.get("skills", [])]
        projects = resume_data.get("projects", [])
        experiences = resume_data.get("experiences", [])

        system_prompt = """你是资深技术招聘评估专家。请基于候选人简历与岗位 JD，进行匹配度评分。

评分规则：
1. 总分 0-100，分数越高匹配度越强
2. 评分维度：技能匹配度(40分)、项目经验相关度(30分)、工作经历相关度(20分)、综合素质(10分)
3. 输出严格 JSON 格式
4. missing_skills 列出岗位要求但简历未体现的关键技能（最多5个）

JSON 输出结构：
{
  "score": 85,
  "summary": "候选人技能栈与岗位高度匹配，3年相关经验...",
  "missing_skills": ["Kubernetes", "Redis"],
  "details": {
    "skill_match": 35,
    "project_relevance": 28,
    "experience_relevance": 18,
    "overall_quality": 8
  }
}"""

        user_content = f"""# 候选人简历摘要
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

# 目标岗位信息
岗位名称：{job.title}
公司：{job.company}
薪资：{job.salary_text or '面议'}
工作年限要求：{job.work_years or '不限'}

## 岗位 JD
{job.jd_text or '无'}

请基于以上信息输出匹配度评分 JSON。"""

        try:
            result = DeepSeekService.chat_json(system_prompt, user_content, temperature=0.2)
            score = int(result.get("score", 0))
            score = max(0, min(100, score))
            return {
                "score": score,
                "summary": result.get("summary", ""),
                "missing_skills": result.get("missing_skills", []),
                "details": result.get("details", {}),
            }
        except Exception as e:
            logger.exception("AI 打分失败")
            # 兜底：基于关键词简单匹配
            return JobMatcher._fallback_score(job, resume)

    @staticmethod
    def _fallback_score(job: Job, resume: Resume) -> Dict:
        """AI 失败时的兜底简单打分（基于关键词重叠）"""
        jd_text = (job.jd_text or "").lower()
        skills = [s.name.lower() for s in resume.skills]
        if not skills or not jd_text:
            return {"score": 50, "summary": "基础匹配（兜底评分）", "missing_skills": [], "details": {}}

        hit = sum(1 for s in skills if s in jd_text)
        score = min(100, int(hit / max(len(skills), 1) * 70) + 20)
        return {
            "score": score,
            "summary": f"关键词匹配度 {hit}/{len(skills)}（兜底评分）",
            "missing_skills": [],
            "details": {"keyword_hit": hit},
        }

    @staticmethod
    def match_jobs(user_id: int, resume: Resume, template: JobTemplate,
                   jobs: List[Job] = None, ai_score: bool = True) -> List[JobMatchRecord]:
        """
        执行完整匹配流程：硬性过滤 + 软性打分

        Args:
            user_id: 用户 ID
            resume: 简历对象
            template: 求职诉求模板
            jobs: 待匹配岗位列表（None 则取该用户所有岗位）
            ai_score: 是否调用 AI 打分（批量时可选关闭以加速）

        Returns:
            匹配记录列表
        """
        if jobs is None:
            jobs = Job.query.filter_by(user_id=user_id).all()

        # 过滤黑名单
        jobs = JobMatcher.filter_blacklisted(user_id, jobs)
        records = []

        for job in jobs:
            # 硬性过滤
            passed, reason = JobMatcher.hard_filter(job, template)

            record = JobMatchRecord(
                user_id=user_id,
                job_id=job.id,
                resume_id=resume.id,
                template_id=template.id,
                hard_filter_passed=passed,
                hard_filter_reason=reason if not passed else None,
                match_score=0 if not passed else 100,
            )

            if passed and ai_score:
                # AI 软性打分
                try:
                    result = JobMatcher.soft_score(job, resume, template)
                    record.match_score = result["score"]
                    record.match_summary = result["summary"]
                    record.missing_skills = ",".join(result.get("missing_skills", []))
                    record.score_details = json.dumps(result.get("details", {}), ensure_ascii=False)
                except Exception as e:
                    logger.exception("岗位 %s 打分失败", job.id)
                    record.match_summary = f"打分失败: {e}"

            db.session.add(record)
            records.append(record)

        db.session.commit()
        return records

    @staticmethod
    def match_single_job(user_id: int, resume: Resume, job: Job, template: JobTemplate) -> Dict:
        """
        单岗位智能匹配（选择简历+岗位+模板）
        返回匹配度评分、摘要、缺失技能和技能提升建议
        """
        passed, hard_reason = JobMatcher.hard_filter(job, template)

        match_score = 0
        match_summary = ""
        missing_skills = []
        skill_suggestions = []

        if passed:
            try:
                score_result = JobMatcher.soft_score(job, resume, template)
                match_score = score_result["score"]
                match_summary = score_result["summary"]
                missing_skills = score_result.get("missing_skills", [])

                if missing_skills:
                    suggestions = JobMatcher.generate_skill_suggestions(job, resume, missing_skills)
                    skill_suggestions = suggestions
            except Exception as e:
                logger.exception("岗位 %s 打分失败", job.id)
                match_summary = f"打分失败: {e}"
        else:
            match_summary = f"硬性条件未通过: {hard_reason}"

        record = JobMatchRecord(
            user_id=user_id,
            job_id=job.id,
            resume_id=resume.id,
            template_id=template.id,
            hard_filter_passed=passed,
            hard_filter_reason=hard_reason if not passed else None,
            match_score=match_score,
            match_summary=match_summary,
            missing_skills=",".join(missing_skills),
        )
        db.session.add(record)
        db.session.commit()

        return {
            "match_score": match_score,
            "match_summary": match_summary,
            "hard_filter_passed": passed,
            "hard_filter_reason": hard_reason if not passed else None,
            "missing_skills": missing_skills,
            "skill_suggestions": skill_suggestions,
            "job": job.to_dict(),
        }

    @staticmethod
    def generate_skill_suggestions(job: Job, resume: Resume, missing_skills: List[str]) -> List[str]:
        """
        根据岗位JD和缺失技能生成技能提升建议
        """
        if not missing_skills:
            return []

        resume_data = resume.to_dict()
        skills = [s.get("name", "") for s in resume_data.get("skills", [])]

        system_prompt = """你是资深技术职业规划师。请根据岗位要求和候选人现有技能，给出针对性的技能提升建议。

输出格式：返回一个建议列表（最多5条），每条建议要具体、可执行，包含学习方向和实践方法。

示例输出：
["建议学习 Redis 缓存设计，可通过搭建个人博客项目实践", "建议深入学习 Kubernetes 容器编排，推荐 CKAD 认证"]"""

        user_content = f"""# 岗位信息
岗位名称：{job.title}
公司：{job.company}

## 岗位要求（JD）
{job.jd_text[:500] if job.jd_text else '暂无详细JD'}

# 候选人现有技能
{', '.join(skills) if skills else '未填写'}

# 需要提升的技能
{', '.join(missing_skills)}

请给出具体的技能提升建议。"""

        try:
            result = DeepSeekService.chat_json(system_prompt, user_content, temperature=0.3)
            if isinstance(result, list):
                return result[:5]
            elif isinstance(result, dict) and "suggestions" in result:
                return result["suggestions"][:5]
            return []
        except Exception as e:
            logger.exception("技能建议生成失败")
            return [f"建议学习 {skill}，可通过项目实践或在线课程提升" for skill in missing_skills[:5]]
