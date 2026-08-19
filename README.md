# look_at 工具 + multimodal-delegation Skill

从 [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode) 提取的多模态分析工具 `look_at` 及其配套的 `multimodal-delegation` skill，作为独立快照仓库。

> **注意**：本仓库是**源码快照 + 依赖说明**，不保证独立编译。`look_at` 深度耦合 oh-my-opencode 的运行时（模型解析、会话管理、provider 缓存等），完整可运行实现请参考上游仓库。

## 目录结构

```
look_at-repo/
├── src/
│   ├── tools/look-at/          # look_at 工具源码（24 个 .ts + 测试）
│   ├── shared/                 # look_at 直接依赖的 shared 模块（16 个）
│   └── plugin-state.ts         # VisionCapableModel 类型定义
├── skill/
│   └── multimodal-delegation/  # 多模态委托 skill
│       ├── SKILL.md
│       └── scripts/pdf_to_images.py   # PDF → PNG 栅格化脚本
├── DEPENDENCIES.md             # 完整依赖树 + 外部包声明
└── README.md
```

## look_at 工具是什么

`look_at` 是 oh-my-opencode 提供的多模态分析工具，通过主 agent 调用，内部委托给 `multimodal-looker` 子智能体（`cloud-ai/qwen-3.7-plus` 视觉模型）分析媒体文件。

**核心能力（实测）：**

| 格式 | 方式 | 状态 |
|------|------|------|
| 图片（png/jpg/webp/gif/bmp/tiff） | 直接 `look_at` | ✅ 可用 |
| PDF | 先转 PNG 再 `look_at` | ✅ 可用（见 skill） |
| 视频 | 需 ffmpeg 抽帧 | ⚠️ 后端不支持直接输入 |
| 音频 | 需转写工具 | ⚠️ 后端不支持直接输入 |

## 工具源码模块（`src/tools/look-at/`）

| 模块 | 职责 |
|------|------|
| `tools.ts` | `createLookAt` 入口，注册 tool + 参数 schema |
| `look-at-arguments.ts` | 参数归一化 + 校验（file_path / file_paths / image_data） |
| `look-at-input-preparer.ts` | 输入预处理：文件 → file part（mime + url），图片格式转换 |
| `mime-type-inference.ts` | 从文件扩展名/base64 推断 MIME 类型 |
| `image-converter.ts` | 非标准图片格式（heic/raw 等）→ JPEG 转换 |
| `look-at-prompt.ts` | 构建发给 multimodal-looker 的 prompt |
| `look-at-session-runner.ts` | 创建子会话、派发 prompt、等待结果 |
| `session-poller.ts` | 轮询子会话直到 idle，提取结果 |
| `multimodal-agent-metadata.ts` | 解析 multimodal-looker agent 的模型/变体 |
| `multimodal-fallback-chain.ts` | 构建视觉模型回退链 |
| `assistant-message-extractor.ts` | 从会话消息提取 assistant 文本 |
| `missing-file-error.ts` | 文件缺失错误分类 |
| `constants.ts` / `types.ts` | 常量 + 类型定义 |

## 关键设计要点

1. **文件以 file part 传递**：`look_at` 将文件作为 `{type:"file", mime, url, filename}` 传给模型，其中 URL 为 `file://` 本地路径。
2. **仅图片会 base64 编码**：OpenAI-compatible 后端只接受 image part 的 base64；PDF/视频/音频以原始 mime 传递时会被后端忽略（这是 PDF 必须转图片的根因）。
3. **`modalities` 声明 ≠ 能力保证**：模型配置里的 `modalities.input` 只是声明，实际支持取决于后端模型本身。

## 使用方法

### 图片分析

```
look_at(file_path="path/to/image.png", goal="描述图片内容")
```

### PDF 分析（需先转图片）

```bash
python skill/multimodal-delegation/scripts/pdf_to_images.py input.pdf --outdir out --dpi 144
# 然后对每页 PNG 调 look_at
```

## License

源码提取自 [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode)，遵循其原始许可证。本仓库仅作快照归档与学习用途。
