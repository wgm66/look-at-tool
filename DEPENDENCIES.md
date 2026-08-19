# 依赖说明

`look_at` 工具从 [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode) 的
`packages/omo-opencode/src/tools/look-at/` 提取。本文件记录其完整依赖关系，帮助理解为什么它不能零依赖剥离。

## 一、直接依赖的 shared 模块（本仓库已随附 `src/shared/`）

以下 16 个模块被 `look_at` 直接或间接引用，已完整复制到本仓库：

| 模块 | 被引用的符号 | 职责 |
|------|-------------|------|
| `model-requirements` | `AGENT_MODEL_REQUIREMENTS`, `FallbackEntry` | 多模态 agent 的模型需求定义 |
| `model-availability` | `fetchAvailableModels` | 获取可用模型列表 |
| `model-resolution-pipeline` | `resolveModelPipeline` | 解析模型管线（fallback 链） |
| `connected-providers-cache` | `readConnectedProvidersCache` | 已连接 provider 缓存读取 |
| `vision-capable-models-cache` | `read/set/clearVisionCapableModelsCache` | 视觉能力模型缓存 |
| `model-suggestion-retry` | `promptSyncWithModelSuggestionRetry`, `parseModelSuggestion` | 模型建议重试机制 |
| `prompt-failure-classifier` | `isAmbiguousPromptDispatchFailure` | prompt 派发失败分类 |
| `prompt-async-gate` | — | 异步 prompt 门控 |
| `prompt-timeout-context` | — | prompt 超时上下文 |
| `logger` | `log`, `configureSharedSubunitLogger` | 日志 |
| `data-path` | — | 数据目录路径解析 |
| `json-file-cache-store` | — | JSON 文件缓存存储 |
| `normalize-sdk-response` | — | SDK 响应归一化 |
| `opencode-server-auth` | — | 服务端认证 |
| `plugin-identity` | — | 插件身份 |
| `live-server-route` | — | 实时服务路由 |

另外随附 `src/plugin-state.ts`（定义 `VisionCapableModel` 类型）。

## 二、外部 npm 包依赖（本仓库未包含，需从上游获取）

`look_at` 及其依赖模块还引用了以下外部包：

| 包名 | 用途 |
|------|------|
| `@opencode-ai/plugin` | `tool()`, `PluginInput`, `ToolDefinition`, `ToolContext` |
| `@opencode-ai/sdk` | `createOpencodeClient`（会话创建/查询） |
| `@oh-my-opencode/utils` | `isRecord`, `resolveXdgDataDir`, `createLogger`, `createProductIdentity` 等 |
| `@oh-my-opencode/model-core` | `FallbackEntry`, `ModelRequirement`, `parseModelSuggestion` 等 |
| `node:*`（node:path/fs/os/url/child_process） | Node 内置模块 |

## 三、跨目录内部依赖（本仓库未包含，需从上游获取）

| 依赖 | 引用点 |
|------|--------|
| `../plugin-state`（`VisionCapableModel`） | `vision-capable-models-cache.ts`, `multimodal-agent-metadata.ts` |
| `../features/claude-code-session-state/state` | `live-server-route.ts` 引用 `subagentSessions` |

## 四、为什么不能独立编译

`look_at` 的完整运行依赖 oh-my-opencode 的：
1. **模型解析管线**（`model-resolution-pipeline` → `model-core` → provider 注册表）
2. **会话运行时**（`@opencode-ai/sdk` 的 `session.create/prompt/messages` API）
3. **缓存基础设施**（`json-file-cache-store`、`connected-providers-cache`、`vision-capable-models-cache`，依赖 `data-path` 定位 opencode 数据目录）
4. **日志与身份**（`plugin-identity`、`logger` 依赖 `@oh-my-opencode/utils`）

这些与 opencode 主进程的运行时状态强耦合，无法作为独立 npm 包编译。**完整可运行实现请使用上游 oh-my-opencode 插件。**

## 五、本仓库用途

- **学习/参考**：理解 `look_at` 工具的实现细节与设计权衡
- **归档**：快照关键源码，便于追溯行为（如 PDF 需转图片的原因）
- **复用片段**：`mime-type-inference.ts`、`image-converter.ts` 等低耦合模块可单独参考
