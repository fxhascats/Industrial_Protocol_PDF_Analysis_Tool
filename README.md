# 工业协议 PDF 分析工具

从工业协议文档 PDF 中自动提取信息并生成结构化阅读模板的工具。

## 功能特性

- **PDF 文本提取**：使用 PyMuPDF 解析 PDF 文档
- **LLM 智能提取**：支持多种大语言模型（OpenAI API、Qwen 本地模型等）
- **模板填充**：自动生成结构化的工业协议阅读模板 PDF
- **多格式支持**：支持 JSON 数据导出和 PDF 报告生成

## 项目结构

```
pdf/
├── pdf_extractor.py        # 核心工具（OpenAI API 兼容）
├── pdf_extractor_qwen.py   # Qwen 本地模型版本
├── generate_pdf.py         # 简单 PDF 模板生成器
├── config.json             # OpenAI API 配置
├── config_qwen.json        # Qwen 本地模型配置
├── 输入.pdf                # 示例输入文件
├── 工业协议阅读模板.pdf      # 模板文件
└── outputs/                # 输出目录
```

## 依赖安装

```bash
pip install PyMuPDF openai reportlab

# Qwen 版本额外依赖
pip install transformers torch accelerate bitsandbytes
```

## 快速开始

### 1. 使用 OpenAI 兼容 API（推荐）

```bash
python pdf_extractor.py
```

### 2. 使用 Qwen 本地模型

```bash
python pdf_extractor_qwen.py config_qwen.json
```

## 配置说明

### config.json（API 方式）

```json
{
    "llm": {
        "provider": "openai",
        "model": "claude-sonnet-4-5-20250929",
        "api_key": "your-api-key",
        "base_url": "https://your-api-endpoint/api/v1"
    },
    "paths": {
        "input_pdf": "./输入.pdf",
        "output_dir": "./outputs"
    }
}
```

### config_qwen.json（本地模型）

```json
{
    "llm": {
        "provider": "huggingface",
        "model": "Qwen/Qwen-7B-Chat",
        "device": "auto",
        "quantization": "4bit",
        "max_length": 6000
    },
    "paths": {
        "input_pdf": "./输入.pdf",
        "output_dir": "./outputs"
    }
}
```

## LLM 配置参数

| 参数 | 说明 |
|------|------|
| `provider` | 提供者类型：`openai`、`local`、`huggingface` |
| `model` | 模型名称（如 `gpt-4o`、`claude-sonnet-...`、`Qwen/Qwen-7B-Chat`） |
| `api_key` | API 密钥 |
| `base_url` | API 端点地址 |
| `device` | 设备选择：`auto`、`cuda`、`cpu` |
| `quantization` | 量化选项：`4bit`、`8bit`、`null` |

## 输出文件

运行后会在 `output_dir` 目录下生成：

| 文件 | 说明 |
|------|------|
| `extracted_data.json` | 提取的结构化数据 |
| `工业协议_filled_*.pdf` | 填充后的 PDF 报告 |
| `llm_response_debug_*.txt` | 模型原始输出（调试用） |

## 提取的信息字段

1. **协议概述**：名称、版本、作者、日期、说明
2. **通信方式**：协议类型、IP/端口、配置说明
3. **信号定义表**：序号、名称、地址、类型、单位、备注
4. **数据格式**：JSON/二进制/ASCII 等说明
5. **时间戳**：格式说明
6. **错误码**：错误代码及处理策略
7. **数据示例**：示例报文
8. **附录**：参考文档

## 硬件要求（本地模型）

| 配置 | 显存需求 | 适用场景 |
|------|----------|----------|
| 4bit 量化 | ~4GB | 大多数情况（推荐） |
| 8bit 量化 | ~7GB | 显存充足时 |
| 无量化 | ~14GB | 高端 GPU |
| CPU | - | 无 GPU 时备用 |

## 常见问题

**Q: 显存不足**
```
A: 设置 "quantization": "4bit" 或 "device": "cpu"
```

**Q: 模型下载慢**
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

**Q: JSON 解析失败**
```
A: 检查 outputs/ 目录下的调试文件，或尝试增加 max_length
```
