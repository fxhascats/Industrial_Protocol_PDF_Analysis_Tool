#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业协议 PDF 信息抽取与模板填充工具

依赖安装：
    pip install PyMuPDF openai reportlab

使用方法：
    python pdf_extractor.py

配置说明：
    修改 config.json 中的配置项，包括：
    - llm.api_key: OpenAI API 密钥
    - llm.provider: 可选 openai / local (本地模型)
    - llm.base_url: API 端点 (用于本地模型或代理)
    - paths: 输入输出路径配置
"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional

import fitz  # PyMuPDF
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ============================================================
# 模块 1: PDF 文本解析
# ============================================================

class PDFParser:
    """PDF 文本解析器"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = None

    def open(self):
        """打开 PDF 文档"""
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF 文件不存在: {self.pdf_path}")
        self.doc = fitz.open(self.pdf_path)
        return self

    def close(self):
        """关闭 PDF 文档"""
        if self.doc:
            self.doc.close()

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def extract_text_by_page(self) -> List[Dict[str, Any]]:
        """按页提取文本"""
        pages = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text("text")
            pages.append({
                "page_number": page_num + 1,
                "text": text,
                "char_count": len(text)
            })
        return pages

    def extract_full_text(self) -> str:
        """提取完整文本"""
        full_text = ""
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            full_text += f"\n--- 第 {page_num + 1} 页 ---\n"
            full_text += page.get_text("text")
        return full_text

    def extract_text_blocks(self) -> List[Dict[str, Any]]:
        """按文本块提取（保留位置信息）"""
        blocks = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            page_blocks = page.get_text("dict")["blocks"]
            for block in page_blocks:
                if block["type"] == 0:  # 文本块
                    text = ""
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text += span.get("text", "")
                        text += "\n"
                    blocks.append({
                        "page": page_num + 1,
                        "bbox": block["bbox"],
                        "text": text.strip()
                    })
        return blocks


# ============================================================
# 模块 2: LLM 抽象层 (支持多种大模型)
# ============================================================

class BaseLLM(ABC):
    """LLM 抽象基类"""

    @abstractmethod
    def extract_protocol_info(self, text: str, template_fields: Dict) -> Dict:
        """从文本中抽取协议信息"""
        pass


class OpenAILLM(BaseLLM):
    """OpenAI API 实现"""

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str = None):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url if base_url else "https://api.openai.com/v1"
        )
        self.model = model

    def extract_protocol_info(self, text: str, template_fields: Dict) -> Dict:
        """使用 ChatGPT 抽取协议信息"""

        prompt = f"""你是一个工业协议文档分析专家。请从以下文档内容中提取信息，并按照指定的 JSON 格式输出。

文档内容：
{text}

请提取以下字段并以 JSON 格式返回：
{{
    "protocol_name": "协议名称",
    "protocol_version": "协议版本号",
    "author": "作者或单位名称",
    "doc_date": "文档日期",
    "doc_description": "文档简要说明（50字以内）",
    "communication_type": "通信方式（如 OPC UA / Modbus / MQTT 等）",
    "ip_port": "IP地址和端口（如有）",
    "protocol_config": "协议配置说明",
    "signals": [
        {{"id": "1", "name": "信号名称", "address": "地址或节点", "type": "数据类型", "unit": "单位", "remark": "备注"}}
    ],
    "data_format": "数据格式说明（JSON/二进制/ASCII等）",
    "timestamp": "时间戳格式说明",
    "error_codes": "错误码说明",
    "data_example": "数据示例（简短）",
    "appendix": "附录或参考文档"
}}

注意：
1. 如果文档中没有某字段信息，填写 "未提供"
2. signals 数组提取代表性的信号定义，涵盖不同类型（输入/输出/寄存器等），最多 25 条
3. 所有输出必须是有效的 JSON 格式，确保 JSON 完整闭合
4. 只输出 JSON，不要有其他内容
"""

        # 尝试使用 response_format，如果失败则不使用
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的工业协议文档分析助手，擅长从技术文档中提取结构化信息。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
        except Exception as e:
            # Claude 等模型不支持 response_format，移除该参数
            print(f"    注意: 不支持 response_format，使用标准模式")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的工业协议文档分析助手，擅长从技术文档中提取结构化信息。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )

        result_text = response.choices[0].message.content

        # 清理可能的 markdown 代码块
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]

        try:
            return json.loads(result_text.strip())
        except json.JSONDecodeError as e:
            print(f"    警告: JSON 解析失败 - {e}")
            print(f"    尝试修复 JSON...")

            # 保存原始响应用于调试
            debug_file = "outputs/llm_response_debug.txt"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(result_text)
            print(f"    原始响应已保存至: {debug_file}")

            # 尝试截断到最后一个完整的对象
            try:
                # 找到最后一个完整的 signals 数组
                if '"signals"' in result_text:
                    # 简单策略：限制 signals 数组大小
                    data = json.loads(result_text.strip())
                    return data
            except:
                pass

            # 如果修复失败，返回默认结构
            print("    使用默认结构")
            return {
                "protocol_name": "解析失败",
                "protocol_version": "未提供",
                "author": "未提供",
                "doc_date": "未提供",
                "doc_description": "JSON 解析失败，请检查 outputs/llm_response_debug.txt",
                "communication_type": "未提供",
                "ip_port": "未提供",
                "protocol_config": "未提供",
                "signals": [],
                "data_format": "未提供",
                "timestamp": "未提供",
                "error_codes": "未提供",
                "data_example": "未提供",
                "appendix": "未提供"
            }


class LocalLLM(BaseLLM):
    """本地大模型实现（兼容 OpenAI API 格式）"""

    def __init__(self, base_url: str, model: str = "qwen2.5", api_key: str = "not-needed"):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url  # 例如: http://localhost:11434/v1 (Ollama)
        )
        self.model = model

    def extract_protocol_info(self, text: str, template_fields: Dict) -> Dict:
        """使用本地模型抽取协议信息"""

        prompt = f"""你是一个工业协议文档分析专家。请从以下文档内容中提取信息，并按照指定的 JSON 格式输出。

文档内容：
{text[:8000]}  # 限制长度以适应本地模型

请提取以下字段并以 JSON 格式返回：
{{
    "protocol_name": "协议名称",
    "protocol_version": "协议版本号",
    "author": "作者或单位名称",
    "doc_date": "文档日期",
    "doc_description": "文档简要说明",
    "communication_type": "通信方式",
    "ip_port": "IP地址和端口",
    "protocol_config": "协议配置说明",
    "signals": [{{"id": "1", "name": "信号名称", "address": "地址", "type": "类型", "unit": "单位", "remark": "备注"}}],
    "data_format": "数据格式说明",
    "timestamp": "时间戳格式",
    "error_codes": "错误码说明",
    "data_example": "数据示例",
    "appendix": "附录"
}}

只输出 JSON，不要有其他内容。
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        result_text = response.choices[0].message.content
        # 尝试从响应中提取 JSON
        try:
            # 清理可能的 markdown 代码块
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            return json.loads(result_text.strip())
        except json.JSONDecodeError:
            return {"error": "JSON 解析失败", "raw": result_text}


def create_llm(config: Dict) -> BaseLLM:
    """LLM 工厂函数"""
    provider = config.get("provider", "openai")

    if provider == "openai":
        return OpenAILLM(
            api_key=config.get("api_key", ""),
            model=config.get("model", "gpt-4o"),
            base_url=config.get("base_url")
        )
    elif provider == "local":
        return LocalLLM(
            base_url=config.get("base_url", "http://localhost:11434/v1"),
            model=config.get("model", "qwen2.5"),
            api_key=config.get("api_key", "not-needed")
        )
    else:
        raise ValueError(f"不支持的 LLM 提供者: {provider}")


# ============================================================
# 模块 3: PDF 生成器
# ============================================================

class PDFGenerator:
    """PDF 模板填充生成器"""

    def __init__(self, output_path: str):
        self.output_path = output_path
        self._register_fonts()

    def _register_fonts(self):
        """注册中文字体"""
        # macOS 字体路径
        font_paths = [
            '/System/Library/Fonts/STHeiti Medium.ttc',
            '/System/Library/Fonts/PingFang.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
            # Linux 字体路径
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            # Windows 字体路径
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simhei.ttf',
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    self.font_name = 'ChineseFont'
                    return
                except:
                    continue

        # 如果没有找到中文字体，使用默认字体
        self.font_name = 'Helvetica'
        print("警告: 未找到中文字体，中文可能显示异常")

    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """创建样式"""
        return {
            'title': ParagraphStyle(
                name='Title',
                fontName=self.font_name,
                fontSize=18,
                leading=22,
                spaceAfter=12,
            ),
            'heading': ParagraphStyle(
                name='Heading',
                fontName=self.font_name,
                fontSize=14,
                leading=18,
                spaceAfter=6,
            ),
            'normal': ParagraphStyle(
                name='Normal',
                fontName=self.font_name,
                fontSize=10,
                leading=14,
            ),
            'table_cell': ParagraphStyle(
                name='TableCell',
                fontName=self.font_name,
                fontSize=8,
                leading=10,
                wordWrap='CJK',  # 支持中文换行
            ),
        }

    def generate(self, data: Dict) -> str:
        """根据数据生成 PDF"""

        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=18
        )

        styles = self._create_styles()
        elements = []

        # 标题
        elements.append(Paragraph("工业协议阅读模板（填充版）", styles['title']))
        elements.append(Spacer(1, 12))

        # 1. 协议概述
        elements.append(Paragraph("1. 协议概述", styles['heading']))
        overview_text = f"""
        协议名称：{data.get('protocol_name', '未提供')}<br/>
        协议版本：{data.get('protocol_version', '未提供')}<br/>
        作者/单位：{data.get('author', '未提供')}<br/>
        文档日期：{data.get('doc_date', '未提供')}<br/>
        文档说明：{data.get('doc_description', '未提供')}
        """
        elements.append(Paragraph(overview_text, styles['normal']))
        elements.append(Spacer(1, 12))

        # 2. 通信方式
        elements.append(Paragraph("2. 通信方式", styles['heading']))
        comm_text = f"""
        通信协议：{data.get('communication_type', '未提供')}<br/>
        IP/端口：{data.get('ip_port', '未提供')}<br/>
        协议配置说明：{data.get('protocol_config', '未提供')}
        """
        elements.append(Paragraph(comm_text, styles['normal']))
        elements.append(Spacer(1, 12))

        # 3. 信号定义表
        elements.append(Paragraph("3. 信号定义表", styles['heading']))

        # 表格表头样式
        header_style = ParagraphStyle(
            name='TableHeader',
            fontName=self.font_name,
            fontSize=9,
            leading=11,
            alignment=1,  # 居中
        )

        # 构建表格数据（使用 Paragraph 支持自动换行）
        table_data = [[
            Paragraph('序号', header_style),
            Paragraph('信号名称', header_style),
            Paragraph('地址/节点', header_style),
            Paragraph('类型', header_style),
            Paragraph('单位', header_style),
            Paragraph('备注', header_style)
        ]]

        signals = data.get('signals', [])

        if signals and isinstance(signals, list):
            # 不限制数量，显示所有信号
            for i, sig in enumerate(signals, 1):
                if isinstance(sig, dict):
                    table_data.append([
                        Paragraph(str(i), styles['table_cell']),
                        Paragraph(sig.get('name', ''), styles['table_cell']),
                        Paragraph(sig.get('address', ''), styles['table_cell']),
                        Paragraph(sig.get('type', ''), styles['table_cell']),
                        Paragraph(sig.get('unit', ''), styles['table_cell']),
                        Paragraph(sig.get('remark', ''), styles['table_cell'])
                    ])

        # 如果没有信号，添加一行空行提示
        if len(table_data) == 1:
            table_data.append([
                Paragraph('', styles['table_cell']),
                Paragraph('无信号数据', styles['table_cell']),
                Paragraph('', styles['table_cell']),
                Paragraph('', styles['table_cell']),
                Paragraph('', styles['table_cell']),
                Paragraph('', styles['table_cell'])
            ])

        # 调整列宽：序号(25), 信号名称(90), 地址(70), 类型(45), 单位(35), 备注(150)
        # 总宽度约 535pt (A4 页面宽度 595 - 左右边距 60)
        # repeatRows=1 表示每页都重复表头
        table = Table(table_data, colWidths=[25, 90, 70, 45, 35, 150], repeatRows=1)
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # 序号列居中
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # 顶部对齐
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        # 4. 数据格式
        elements.append(Paragraph("4. 数据格式", styles['heading']))
        elements.append(Paragraph(data.get('data_format', '未提供'), styles['normal']))
        elements.append(Spacer(1, 12))

        # 5. 时间戳
        elements.append(Paragraph("5. 时间戳", styles['heading']))
        elements.append(Paragraph(data.get('timestamp', '未提供'), styles['normal']))
        elements.append(Spacer(1, 12))

        # 6. 错误码
        elements.append(Paragraph("6. 错误码", styles['heading']))
        elements.append(Paragraph(data.get('error_codes', '未提供'), styles['normal']))
        elements.append(Spacer(1, 12))

        # 7. 数据示例
        elements.append(Paragraph("7. 数据示例", styles['heading']))
        elements.append(Paragraph(data.get('data_example', '未提供'), styles['normal']))
        elements.append(Spacer(1, 12))

        # 8. 附录
        elements.append(Paragraph("8. 附录", styles['heading']))
        elements.append(Paragraph(data.get('appendix', '未提供'), styles['normal']))
        elements.append(Spacer(1, 12))

        # 生成时间戳
        elements.append(Spacer(1, 24))
        elements.append(Paragraph(
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles['normal']
        ))

        # 构建 PDF
        doc.build(elements)
        return self.output_path


# ============================================================
# 主程序
# ============================================================

def load_config(config_path: str = "config.json") -> Dict:
    """加载配置文件"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """主函数"""
    print("=" * 50)
    print("工业协议 PDF 信息抽取与模板填充工具")
    print("=" * 50)

    # 1. 加载配置
    print("\n[1/4] 加载配置...")
    config = load_config()

    input_pdf = config['paths']['input_pdf']
    output_dir = config['paths']['output_dir']

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 2. 解析 PDF
    print(f"\n[2/4] 解析 PDF: {input_pdf}")
    with PDFParser(input_pdf) as parser:
        full_text = parser.extract_full_text()
        print(f"    提取文本长度: {len(full_text)} 字符")

    # 3. LLM 抽取
    print(f"\n[3/4] 使用 {config['llm']['provider']} 抽取信息...")
    llm = create_llm(config['llm'])
    extracted_data = llm.extract_protocol_info(full_text, config['template_fields'])

    # 保存抽取的 JSON
    json_output = os.path.join(output_dir, "extracted_data.json")
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=2)
    print(f"    抽取结果已保存: {json_output}")

    # 4. 生成 PDF
    print("\n[4/4] 生成填充后的 PDF...")
    output_pdf = os.path.join(output_dir, f"工业协议_filled_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    generator = PDFGenerator(output_pdf)
    generator.generate(extracted_data)

    print(f"\n完成! 输出文件: {output_pdf}")
    print("=" * 50)

    return output_pdf


if __name__ == "__main__":
    main()
