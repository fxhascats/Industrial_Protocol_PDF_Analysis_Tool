from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 注册中文字体（macOS 系统字体）
pdfmetrics.registerFont(TTFont('STHeiti', '/System/Library/Fonts/STHeiti Medium.ttc'))

# 输出文件名
pdf_file = "工业协议阅读模板.pdf"

# 创建文档对象
doc = SimpleDocTemplate(pdf_file, pagesize=A4, rightMargin=30,leftMargin=30, topMargin=30,bottomMargin=18)

# 样式 - 使用中文字体
styles = getSampleStyleSheet()

# 自定义中文样式
styleH = ParagraphStyle(
    name='ChineseHeading1',
    fontName='STHeiti',
    fontSize=18,
    leading=22,
    spaceAfter=12,
)

styleH2 = ParagraphStyle(
    name='ChineseHeading2',
    fontName='STHeiti',
    fontSize=14,
    leading=18,
    spaceAfter=6,
)

styleN = ParagraphStyle(
    name='ChineseNormal',
    fontName='STHeiti',
    fontSize=10,
    leading=14,
)

# 文档内容列表
elements = []

# 标题
elements.append(Paragraph("工业协议阅读模板（简易版）", styleH))
elements.append(Spacer(1, 12))

# 1. 协议概述
elements.append(Paragraph("1. 协议概述", styleH2))
elements.append(Paragraph(
    "协议名称：\n"
    "协议版本：\n"
    "作者/单位：\n"
    "文档日期：\n"
    "文档说明：\n"
, styleN))
elements.append(Spacer(1, 12))

# 2. 通信方式
elements.append(Paragraph("2. 通信方式", styleH2))
elements.append(Paragraph(
    "- OPC UA / Modbus / MQTT / MTConnect（勾选或填写）\n"
    "- IP/端口：\n"
    "- 协议配置说明：\n"
, styleN))
elements.append(Spacer(1, 12))

# 3. 信号定义表
elements.append(Paragraph("3. 信号定义表", styleH2))
data = [
    ['序号','信号名称','地址/节点','类型','单位','备注'],
    ['1','','','','',''],
    ['2','','','','',''],
    ['3','','','','',''],
    ['4','','','','',''],
    ['5','','','','','']
]
table = Table(data, colWidths=[30,100,100,50,50,100])
table.setStyle(TableStyle([
    ('FONTNAME',(0,0),(-1,-1),'STHeiti'),
    ('FONTSIZE',(0,0),(-1,-1),10),
    ('GRID',(0,0),(-1,-1),0.5,colors.black),
    ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
    ('ALIGN',(0,0),(-1,-1),'CENTER'),
    ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
]))
elements.append(table)
elements.append(Spacer(1, 12))

# 4. 数据格式
elements.append(Paragraph("4. 数据格式", styleH2))
elements.append(Paragraph("示例：JSON / 二进制 / ASCII等格式说明", styleN))
elements.append(Spacer(1, 12))

# 5. 时间戳
elements.append(Paragraph("5. 时间戳", styleH2))
elements.append(Paragraph("设备端时间字段说明，时间单位，时钟同步方式", styleN))
elements.append(Spacer(1, 12))

# 6. 错误码
elements.append(Paragraph("6. 错误码", styleH2))
elements.append(Paragraph("协议错误码说明及处理策略", styleN))
elements.append(Spacer(1, 12))

# 7. 数据示例
elements.append(Paragraph("7. 数据示例", styleH2))
elements.append(Paragraph("在此填写示例报文或信号样例", styleN))
elements.append(Spacer(1, 12))

# 8. 附录
elements.append(Paragraph("8. 附录", styleH2))
elements.append(Paragraph("参考文档、图表或其他说明", styleN))
elements.append(Spacer(1, 12))

# 生成 PDF
doc.build(elements)

print(f"PDF 已生成: {pdf_file}")
