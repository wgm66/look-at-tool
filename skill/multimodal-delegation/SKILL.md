---
name: multimodal-delegation
description: "多模态任务委托技能 - 当其他智能体需要处理图片、视频、PDF等多模态内容时，自动委托给 Nonlinguistic 智能体处理。Nonlinguistic 使用 cloud-ai/qwen-3.7-plus 模型，支持多模态输入和最大强度推理。"
---

# 多模态任务委托技能

## 使用场景

当任务涉及以下内容时，**必须**委托给 Nonlinguistic 智能体：

- 图片分析、识别、描述、OCR
- 视频内容理解、关键帧提取、字幕识别
- PDF 文档阅读、表格提取、图文混排解析
- 多模态文件对比、去重、分类

## 核心工具：look_at

多模态分析通过主 agent 的 **`look_at`** 工具完成。`look_at` 内部自动委托给 `multimodal-looker` 子智能体（使用 `cloud-ai/qwen-3.7-plus` 视觉模型）。

**支持直接传入 `look_at` 的格式（已实测验证）：**
- ✅ 图片（.png, .jpg, .jpeg, .webp, .gif, .bmp, .tiff）

**必须预处理后再传 `look_at` 的格式：**
- 📄 **PDF** → 先渲染成 PNG 图片，再 `look_at` 每页图片
- 🎬 **视频** → 后端不支持（需 ffmpeg 抽帧后 `look_at` 关键帧）
- 🎵 **音频** → 后端不支持（需转写工具，超出当前能力）

## PDF 处理流程（已实测验证）

`look_at` 直接传 `.pdf` 会失败——因为 OpenAI-compatible 后端**不接受 `application/pdf` file part**（只接受 image part 的 base64）。必须先把 PDF 每页栅格化成 PNG：

```bash
python "C:\Users\YHZ_zt\.config\opencode\skills\multimodal-delegation\scripts\pdf_to_images.py" <input.pdf> --outdir <输出目录> --dpi 144
```

脚本会输出每页 PNG 路径（stdout 一行一个），然后对每页调用 `look_at(file_path="...png", goal="...")`。

## 委托协议

### 1. 识别多模态需求
在任务开始前或执行中，检查是否涉及：
- 文件路径指向图片（.png, .jpg, .jpeg, .webp, .gif, .bmp, .tiff）
- 文件路径指向视频（.mp4, .mov, .avi, .mkv, .webm）
- 文件路径指向 PDF（.pdf）
- 用户明确要求"看图"、"识别图片"、"分析视频"、"读取PDF"

### 2. 自动委托格式
```json
{
  "agent": "Nonlinguistic",
  "task": "具体任务描述",
  "files": ["文件路径1", "文件路径2"],
  "context": "上下文信息（可选）"
}
```

### 3. 接收结果并继续
Nonlinguistic 返回结构化结果后，原智能体继续后续处理。

## 触发关键词

- "识别"、"看图"、"分析图片"、"图片内容"
- "视频分析"、"视频内容"、"关键帧"
- "读取PDF"、"PDF解析"、"PDF表格"
- "多模态"、"图文混排"、"OCR"

## 禁用方式

若要禁用多模态委托，在 `oh-my-openagent.json` 把 `multimodal-looker` 的 `model` 改回文本模型（如 `cloud-ai/deepseek-v4-pro-tg`）即可事实禁用——`look_at` 工具仍可调用，但视觉能力退化为文本模型的描述能力。

## 错误透明化（常见失败模式）

| 场景 | 现象 | 根因 | 解决 |
|------|------|------|------|
| `look_at` 传 .pdf | "未包含 PDF 内容" / 超时 | OpenAI-compatible 后端不接受 `application/pdf` file part | 先用 `pdf_to_images.py` 转 PNG 再 `look_at` |
| `look_at` 传 .mp4 | "No response from multimodal-looker agent" | 后端不支持视频 file part | 需 ffmpeg 抽帧成 PNG 再 `look_at` |
| `look_at` 传 .wav/.mp3 | "当前模型不支持音频输入" | qwen-3.7-plus 后端不支持音频 | 需转写工具（超出当前能力） |
| 主 agent 收到粘贴图片但无 vision | API 报错 / 乱码 | 图片字节进入主 context | 主动委托 Nonlinguistic（见下方"图片粘贴保护"） |

## 图片粘贴保护（重要）

**当前无自动 hook 拦截**（oh-my-opencode 的 hooks 是插件内部机制，用户层无法注册）。当用户在 TUI 粘贴图片时，图片字节会**直接进入主 agent 的 context**。若主 agent 模型不支持 vision（如 deepseek-v4-pro-tg），会触发 API 错误或输出乱码。

**主 agent 必须主动识别图片粘贴场景并立即委托 Nonlinguistic**：
- 检测到 message 中含 image_data / image part → 立即 `look_at(image_data=..., goal="分析图片内容")`
- 不要尝试用文本模型直接描述图片
- 不要把图片字节留在主 context 里继续推理

**未来改进**：需要给上游 oh-my-opencode 提 PR，在 `experimental.chat.messages.transform` hook 里加入图片拦截逻辑（参考 oh-my-opencode-slim 的 Observer 实现）。

## 禁止行为

- ❌ 其他智能体直接用文本模型处理多模态文件（会因模型不支持而失败）
- ❌ 直接 `look_at` 传 .pdf 文件（会失败，必须先转图片）
- ❌ 忽略多模态需求直接用文本模型处理
- ❌ 不通过委托协议直接调用 Nonlinguistic

## 正确流程示例

### 图片
用户："帮我识别这张图片里的文字"

1. 识别到"识别"+"图片" → 触发多模态委托
2. `look_at(file_path="path/to/image.png", goal="OCR识别图片文字")`
3. 模型返回识别结果，基于结果回答

### PDF
用户："读取这份 PDF 的内容"

1. 识别到 PDF → 先转图片：
   ```bash
   python "C:\Users\YHZ_zt\.config\opencode\skills\multimodal-delegation\scripts\pdf_to_images.py" "path/to/doc.pdf" --outdir "path/to/out"
   ```
2. 对每页 PNG 调 `look_at(file_path="path/to/out/doc_page_1.png", goal="提取文字内容")`
3. 汇总各页结果，回答用户

---

**记住：所有多模态任务必须走 Nonlinguistic（look_at 工具），这是架构强制要求。PDF 必须先转图片再 look_at。**
