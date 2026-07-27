"""
简历 PDF 生成器

基于 reportlab 实现，支持单页/多页自适应排版
"""
import os
import logging
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, black, grey
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)

from app.models.resume import Resume

logger = logging.getLogger(__name__)


class ResumePDFGenerator:
    """简历 PDF 生成器"""

    # 主题色
    PRIMARY_COLOR = HexColor("#2c5282")
    SUB_COLOR = HexColor("#4a5568")
    LIGHT_COLOR = HexColor("#e2e8f0")

    @classmethod
    def generate(cls, resume: Resume, pages: str = "single") -> str:
        """
        生成简历 PDF

        Args:
            resume: 简历对象
            pages: single - 紧凑单页；multi - 多页完整

        Returns:
            PDF 文件路径
        """
        from flask import current_app
        storage_cfg = current_app.config["STORAGE_CFG"]
        out_dir = Path(current_app.config["BASE_DIR"]) / storage_cfg["optimized_dir"]
        out_dir.mkdir(parents=True, exist_ok=True)

        filename = f"resume_{resume.id}_{resume.name}.pdf".replace(" ", "_").replace("/", "_")
        pdf_path = out_dir / filename

        # 字体注册（支持中文）
        cls._register_chinese_font()

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.2 * cm,
            bottomMargin=1.2 * cm,
            title=f"{resume.name or '简历'}",
        )

        styles = cls._build_styles(pages == "single")
        story = []

        # 顶部：姓名 + 求职意向
        story.extend(cls._build_header(resume, styles))
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=1, color=cls.PRIMARY_COLOR))
        story.append(Spacer(1, 8))

        # 基础信息
        story.extend(cls._build_basic_info(resume, styles))

        # 教育经历
        educations = list(resume.educations)
        if educations:
            story.append(Spacer(1, 6))
            story.append(Paragraph("教育经历", styles["section_title"]))
            for edu in educations:
                story.extend(cls._build_education(edu, styles))

        # 工作/实习经历
        experiences = list(resume.experiences)
        if experiences:
            story.append(Spacer(1, 6))
            story.append(Paragraph("工作经历", styles["section_title"]))
            for exp in experiences:
                story.extend(cls._build_experience(exp, styles))

        # 项目经历
        projects = list(resume.projects)
        if projects:
            story.append(Spacer(1, 6))
            story.append(Paragraph("项目经历", styles["section_title"]))
            for proj in projects:
                story.extend(cls._build_project(proj, styles))

        # 专业技能
        skills = list(resume.skills)
        if skills:
            story.append(Spacer(1, 6))
            story.append(Paragraph("专业技能", styles["section_title"]))
            story.extend(cls._build_skills(skills, styles))

        # 自我评价
        if resume.self_evaluation:
            story.append(Spacer(1, 6))
            story.append(Paragraph("自我评价", styles["section_title"]))
            story.append(Paragraph(cls._escape(resume.self_evaluation), styles["body"]))

        doc.build(story)
        logger.info("简历 PDF 已生成: %s", pdf_path)
        return str(pdf_path)

    @staticmethod
    def _register_chinese_font():
        """注册中文字体"""
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # 尝试多个常见中文字体路径
        candidates = [
            ("c:/windows/fonts/simhei.ttf", "SimHei"),
            ("c:/windows/fonts/msyh.ttc", "MSYH"),
            ("c:/windows/fonts/simsun.ttc", "SimSun"),
            ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "WQY"),
            ("/System/Library/Fonts/PingFang.ttc", "PingFang"),
        ]
        for path, name in candidates:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(name, path))
                    ResumePDFGenerator._font_name = name
                    return
                except Exception:
                    continue
        # 找不到中文字体的兜底（中文会显示为方块，但能正常生成）
        ResumePDFGenerator._font_name = "Helvetica"

    _font_name = "Helvetica"

    @classmethod
    def _build_styles(cls, compact: bool):
        """构建段落样式"""
        font = cls._font_name
        body_size = 9 if compact else 10
        title_size = 16 if compact else 18
        section_size = 11 if compact else 12

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="Name", fontName=font, fontSize=title_size,
            textColor=cls.PRIMARY_COLOR, alignment=TA_CENTER, spaceAfter=2,
            leading=title_size + 2,
        ))
        styles.add(ParagraphStyle(
            name="TargetLine", fontName=font, fontSize=body_size,
            textColor=cls.SUB_COLOR, alignment=TA_CENTER, spaceAfter=2,
        ))
        styles.add(ParagraphStyle(
            name="ContactLine", fontName=font, fontSize=body_size - 1,
            textColor=cls.SUB_COLOR, alignment=TA_CENTER,
        ))
        styles.add(ParagraphStyle(
            name="SectionTitle", fontName=font, fontSize=section_size,
            textColor=cls.PRIMARY_COLOR, spaceBefore=4, spaceAfter=2,
            borderWidth=0, borderColor=cls.PRIMARY_COLOR,
        ))
        styles.add(ParagraphStyle(
            name="ItemTitle", fontName=font, fontSize=body_size,
            textColor=black, spaceAfter=1, leading=body_size + 2,
        ))
        styles.add(ParagraphStyle(
            name="ItemMeta", fontName=font, fontSize=body_size - 1,
            textColor=cls.SUB_COLOR, alignment=TA_LEFT, leading=body_size,
        ))
        styles.add(ParagraphStyle(
            name="Body", fontName=font, fontSize=body_size - 1,
            textColor=black, alignment=TA_JUSTIFY, leading=body_size + 2,
            firstLineIndent=0, spaceAfter=2,
        ))
        return {
            "name": styles["Name"],
            "target": styles["TargetLine"],
            "contact": styles["ContactLine"],
            "section_title": styles["SectionTitle"],
            "item_title": styles["ItemTitle"],
            "item_meta": styles["ItemMeta"],
            "body": styles["Body"],
        }

    @classmethod
    def _build_header(cls, resume: Resume, styles):
        items = []
        name = resume.real_name or resume.name or "简历"
        items.append(Paragraph(cls._escape(name), styles["name"]))

        target_parts = []
        if resume.target_position:
            target_parts.append(f"求职意向：{cls._escape(resume.target_position)}")
        if resume.target_city:
            target_parts.append(cls._escape(resume.target_city))
        if resume.expected_salary:
            target_parts.append(f"期望薪资：{cls._escape(resume.expected_salary)}")
        if target_parts:
            items.append(Paragraph(" | ".join(target_parts), styles["target"]))

        contact_parts = []
        if resume.phone:
            contact_parts.append(f"📞 {cls._escape(resume.phone)}")
        if resume.email:
            contact_parts.append(f"✉ {cls._escape(resume.email)}")
        if resume.gender or resume.age:
            info = []
            if resume.gender:
                info.append(cls._escape(resume.gender))
            if resume.age:
                info.append(f"{resume.age}岁")
            contact_parts.append(" | ".join(info))
        if resume.location:
            contact_parts.append(f"📍 {cls._escape(resume.location)}")
        if contact_parts:
            items.append(Paragraph(" | ".join(contact_parts), styles["contact"]))
        return items

    @classmethod
    def _build_basic_info(cls, resume: Resume, styles):
        return []  # 已在 header 中体现

    @classmethod
    def _build_education(cls, edu, styles):
        items = []
        title = cls._escape(edu.school or "")
        if edu.major:
            title += f" · {cls._escape(edu.major)}"
        if edu.degree:
            title += f" · {cls._escape(edu.degree)}"
        items.append(Paragraph(title, styles["item_title"]))

        meta = []
        if edu.start_date or edu.end_date:
            meta.append(f"{cls._escape(edu.start_date or '')} - {cls._escape(edu.end_date or '至今')}")
        if meta:
            items.append(Paragraph(" | ".join(meta), styles["item_meta"]))
        if edu.description:
            items.append(Paragraph(cls._escape(edu.description), styles["body"]))
        items.append(Spacer(1, 2))
        return items

    @classmethod
    def _build_experience(cls, exp, styles):
        items = []
        title = cls._escape(exp.company or "")
        if exp.position:
            title += f" · {cls._escape(exp.position)}"
        if exp.job_type:
            title += f" · {cls._escape(exp.job_type)}"
        items.append(Paragraph(title, styles["item_title"]))

        meta = []
        if exp.start_date or exp.end_date:
            meta.append(f"{cls._escape(exp.start_date or '')} - {cls._escape(exp.end_date or '至今')}")
        if meta:
            items.append(Paragraph(" | ".join(meta), styles["item_meta"]))
        if exp.description:
            items.append(Paragraph(cls._escape(exp.description), styles["body"]))
        items.append(Spacer(1, 2))
        return items

    @classmethod
    def _build_project(cls, proj, styles):
        items = []
        title = cls._escape(proj.name or "")
        if proj.role:
            title += f" · {cls._escape(proj.role)}"
        items.append(Paragraph(title, styles["item_title"]))

        meta = []
        if proj.start_date or proj.end_date:
            meta.append(f"{cls._escape(proj.start_date or '')} - {cls._escape(proj.end_date or '至今')}")
        if proj.tech_stack:
            meta.append(f"技术栈：{cls._escape(proj.tech_stack)}")
        if meta:
            items.append(Paragraph(" | ".join(meta), styles["item_meta"]))
        if proj.description:
            items.append(Paragraph(cls._escape(proj.description), styles["body"]))
        items.append(Spacer(1, 2))
        return items

    @classmethod
    def _build_skills(cls, skills, styles):
        items = []
        # 按分类分组
        groups = {}
        for sk in skills:
            cat = sk.category or "其他"
            groups.setdefault(cat, []).append(sk)

        rows = []
        for cat, sks in groups.items():
            skill_text = "、".join(
                f"{cls._escape(sk.name)}({cls._escape(sk.level or '')})"
                for sk in sks
            )
            rows.append([Paragraph(cls._escape(cat), styles["item_meta"]),
                         Paragraph(skill_text, styles["body"])])

        if rows:
            table = Table(rows, colWidths=[2.5 * cm, 14 * cm])
            table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]))
            items.append(table)
        return items

    @staticmethod
    def _escape(text) -> str:
        """转义 reportlab 段落中的特殊字符"""
        if text is None:
            return ""
        s = str(text)
        # 转义 XML 特殊字符，但保留中文
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # 换行转 <br/>
        s = s.replace("\n", "<br/>")
        return s
