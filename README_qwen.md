# 工业协议 PDF 分析工具 - Qwen-7B-Chat 版本

这是支持 Qwen-7B-Chat 本地大模型的 PDF 分析工具版本。

## 📦 依赖安装

```bash
# 基础依赖
pip install PyMuPDF reportlab

# Qwen 模型依赖
pip install transformers torch accelerate bitsandbytes

# 可选：OpenAI API（如果还想使用在线模型）
pip install openai
```

## 🚀 快速开始

### 1. 使用 Qwen-7B-Chat 模型

```bash
python pdf_extractor_qwen.py config_qwen.json
```

### 2. 使用默认配置（OpenAI API）

```bash
python pdf_extractor_qwen.py
# 或
python pdf_extractor_qwen.py config.json
```

## ⚙️ 配置说明

### config_qwen.json - Qwen 模型配置

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
        "input_pdf": "/path/to/your/input.pdf",
        "output_dir": "/path/to/output"
    }
}
```

#### LLM 配置参数说明

- **provider**: LLM 提供者类型
  - `"huggingface"`: 使用 HuggingFace 本地模型（如 Qwen）
  - `"openai"`: 使用 OpenAI API
  - `"local"`: 使用本地 API 服务器（如 Ollama）

- **model**: 模型名称
  - HuggingFace: `"Qwen/Qwen-7B-Chat"`, `"Qwen/Qwen-14B-Chat"` 等
  - OpenAI: `"gpt-4o"`, `"claude-sonnet-4-5-20250929"` 等

- **device**: 设备选择（仅 HuggingFace）
  - `"auto"`: 自动检测（推荐）
  - `"cuda"`: 强制使用 GPU
  - `"cpu"`: 使用 CPU（速度较慢）

- **quantization**: 量化选项（仅 HuggingFace）
  - `"4bit"`: 4bit 量化（推荐，约 4GB 显存）
  - `"8bit"`: 8bit 量化（约 7GB 显存）
  - `null`: 不使用量化（约 14GB 显存）

- **max_length**: 最大输入文本长度（字符数）
  - 默认: 6000
  - 建议范围: 4000-8000（取决于模型和显存）

## 💡 使用建议

### 硬件要求

| 配置 | 显存需求 | 推理速度 | 推荐场景 |
|------|----------|----------|----------|
| 4bit 量化 | ~4GB | 较快 | 大多数情况（推荐） |
| 8bit 量化 | ~7GB | 中等 | 显存充足时 |
| 无量化 | ~14GB | 快 | 高端 GPU |
| CPU | - | 很慢 | 无 GPU 时备用 |

### 首次运行

首次运行会从 HuggingFace Hub 下载模型（约 7GB），请确保：
1. 网络连接稳定
2. 有足够的磁盘空间（至少 15GB）
3. 如遇下载问题，可设置 HuggingFace 镜像：
   ```bash
   export HF_ENDPOINT=https://hf-mirror.com
   ```

### 性能优化

1. **显存不足**：
   - 使用 4bit 量化
   - 减少 `max_length`
   - 使用 CPU（速度会很慢）

2. **推理速度慢**：
   - 确保使用 GPU
   - 减少 `max_length`
   - 考虑升级硬件

3. **输出质量不佳**：
   - 增加 `max_length`（在显存允许的情况下）
   - 调整 prompt（在代码中修改）
   - 尝试更大的模型（如 Qwen-14B-Chat）

## 📊 输出文件

运行后会在 `output_dir` 目录下生成：

1. **extracted_data.json**: 提取的结构化数据
2. **工业协议_filled_YYYYMMDD_HHMMSS.pdf**: 填充后的 PDF 报告
3. **llm_response_debug_qwen.txt**: 模型原始输出（仅在解析失败时）

## 🔍 故障排除

### 常见问题

**Q: 显存不足 (CUDA out of memory)**
```
A: 修改 config_qwen.json，设置 "quantization": "4bit" 或 "device": "cpu"
```

**Q: 模型下载失败**
```
A: 1. 检查网络连接
   2. 设置镜像: export HF_ENDPOINT=https://hf-mirror.com
   3. 手动下载模型到本地，修改 model 路径
```

**Q: JSON 解析失败**
```
A: 1. 检查 outputs/llm_response_debug_qwen.txt 查看原始输出
   2. 模型可能需要更多上下文，尝试增加 max_length
   3. 考虑使用更强的模型或在线 API
```

**Q: CPU 推理太慢**
```
A: 1. CPU 推理可能需要几分钟甚至更长时间，请耐心等待
   2. 建议使用 GPU 或在线 API
   3. 减少 max_length 可以加快速度
```

## 🆚 版本对比

| 特性 | Qwen-7B (本地) | OpenAI API |
|------|----------------|------------|
| 成本 | 免费 | 按使用付费 |
| 隐私 | 数据不出本地 | 需上传数据 |
| 速度 | 取决于硬件 | 通常较快 |
| 质量 | 中等 | 优秀 |
| 硬件要求 | 需要 GPU | 无要求 |

## 📝 示例命令

```bash
# 1. 使用 4bit 量化的 Qwen-7B-Chat（推荐）
python pdf_extractor_qwen.py config_qwen.json

# 2. 创建自定义配置使用 CPU
# 修改 config_qwen.json: "device": "cpu", "quantization": null
python pdf_extractor_qwen.py config_qwen.json

# 3. 使用更大的模型（需要更多显存）
# 修改 config_qwen.json: "model": "Qwen/Qwen-14B-Chat"
python pdf_extractor_qwen.py config_qwen.json
```

## 🔧 进阶配置

如需修改 prompt、调整生成参数等，请直接编辑 `pdf_extractor_qwen.py` 中的 `HuggingFaceLLM` 类。

主要可调参数位于 `extract_protocol_info` 方法中：
- `max_new_tokens`: 最大生成 token 数（默认 2048）
- `temperature`: 生成温度（默认 0.1）
- `top_p`: nucleus sampling 参数（默认 0.8）

---

**祝使用愉快！如有问题请查看代码注释或联系开发者。**
