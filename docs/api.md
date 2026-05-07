# API 文档（v0.6-prompt-rules-doc）

基础地址：`http://127.0.0.1:8000`

## 1. 测试对象管理

### `test_target` 字段说明（v0.2）

- `target_type` 可选值：`prompt` / `agent_http` / `rag_http`
- `method`：HTTP 方法，支持 `GET` / `POST`，为空时默认 `POST`
- `headers_json`：字符串类型，要求是 JSON 对象字符串（例如 `{"Content-Type":"application/json"}`）
- `body_template`：字符串模板，`POST` 时生效，支持 `{input_text}` 占位符替换
- `GET` 时不会使用 `body_template`，会自动把当前用例输入拼接为查询参数 `input_text`

### POST `/api/test-targets`
请求示例（Prompt）：

```json
{
  "name": "通用 Prompt 被测对象",
  "target_type": "prompt",
  "description": "用于测试 prompt runner",
  "prompt_content": "你是一个测试助手"
}
```

请求示例（agent_http POST）：

```json
{
  "name": "示例Agent POST接口",
  "target_type": "agent_http",
  "description": "用于测试外部Agent接口",
  "endpoint_url": "http://127.0.0.1:9000/chat",
  "method": "POST",
  "headers_json": "{\"Content-Type\":\"application/json\"}",
  "body_template": "{\"message\":\"{input_text}\"}",
  "prompt_content": ""
}
```

请求示例（rag_http POST）：

```json
{
  "name": "示例RAG POST检索接口",
  "target_type": "rag_http",
  "description": "用于测试外部RAG检索接口",
  "endpoint_url": "http://127.0.0.1:9000/search",
  "method": "POST",
  "headers_json": "{\"Content-Type\":\"application/json\"}",
  "body_template": "{\"query\":\"{input_text}\",\"top_k\":5}",
  "prompt_content": ""
}
```

请求示例（rag_http GET）：

```json
{
  "name": "示例RAG GET检索接口",
  "target_type": "rag_http",
  "description": "用于测试GET类型RAG检索接口",
  "endpoint_url": "http://127.0.0.1:9000/search",
  "method": "GET",
  "headers_json": "",
  "body_template": "",
  "prompt_content": ""
}
```

返回示例：

```json
{
  "id": 1,
  "name": "通用 Prompt 被测对象",
  "target_type": "prompt",
  "description": "用于测试 prompt runner",
  "endpoint_url": null,
  "method": "POST",
  "headers_json": null,
  "body_template": null,
  "prompt_content": "你是一个测试助手",
  "created_at": "2026-04-29T06:00:00.000000"
}
```

### GET `/api/test-targets`
返回示例：

```json
[
  {
    "id": 1,
    "name": "通用 Prompt 被测对象",
    "target_type": "prompt",
    "description": "用于测试 prompt runner",
    "endpoint_url": null,
    "method": "POST",
    "headers_json": null,
    "body_template": null,
    "prompt_content": "你是一个测试助手",
    "created_at": "2026-04-29T06:00:00.000000"
  }
]
```

### GET `/api/test-targets/{target_id}`
返回示例：

```json
{
  "id": 1,
  "name": "通用 Prompt 被测对象",
  "target_type": "prompt",
  "description": "用于测试 prompt runner",
  "endpoint_url": null,
  "method": "POST",
  "headers_json": null,
  "body_template": null,
  "prompt_content": "你是一个测试助手",
  "created_at": "2026-04-29T06:00:00.000000"
}
```

## 2. 用例管理

### POST `/api/test-cases/upload`
请求类型：`multipart/form-data`

字段：
- `file`：CSV 文件
- `suite_name`：可选
- `description`：可选

CSV 固定表头：

```text
case_id,case_name,input_text,assert_type,expected_value
```

返回示例：

```json
{
  "suite_id": 1,
  "case_count": 3
}
```

### GET `/api/test-suites`
返回示例：

```json
[
  {
    "id": 1,
    "name": "Demo Suite",
    "description": "Uploaded from CSV",
    "case_count": 3,
    "created_at": "2026-04-29T06:02:00.000000"
  }
]
```

### GET `/api/test-suites/{suite_id}/cases`
返回示例：

```json
[
  {
    "id": 1,
    "suite_id": 1,
    "case_id": "TC001",
    "case_name": "基础包含断言",
    "input_text": "请根据输入返回测试响应",
    "assert_type": "contains",
    "expected_value": "Mock"
  }
]
```

## 3. 测试执行

### POST `/api/test-runs`
请求示例：

```json
{
  "target_id": 1,
  "suite_id": 1
}
```

返回示例：

```json
{
  "run_id": 1,
  "total": 3,
  "passed": 2,
  "failed": 1
}
```

说明：
- 当 runner 返回 `HTTP_ERROR:` 开头文本时，表示 HTTP Runner 执行失败（如网络错误、超时、headers_json 解析失败、非法 method 等）。
- 该用例会直接判定失败，`reason` 会保存完整 `HTTP_ERROR` 文本。

### GET `/api/test-runs`
返回示例：

```json
[
  {
    "id": 1,
    "target_id": 1,
    "suite_id": 1,
    "status": "completed",
    "total": 3,
    "passed": 2,
    "failed": 1,
    "created_at": "2026-04-29T06:05:00.000000"
  }
]
```

### GET `/api/test-runs/{run_id}/results`
返回示例：

```json
[
  {
    "id": 1,
    "run_id": 1,
    "case_id": "TC001",
    "case_name": "基础包含断言",
    "input_text": "请根据输入返回测试响应",
    "actual_output": "MockPromptResponse: 请根据输入返回测试响应",
    "assert_type": "contains",
    "expected_value": "Mock",
    "passed": true,
    "reason": "contains matched",
    "latency_ms": 0
  }
]
```

### GET `/api/test-runs/{run_id}/export-csv`
接口说明：导出指定 `run_id` 的测试结果 CSV（UTF-8 with BOM），可直接用 Excel 打开。

请求示例：

```http
GET /api/test-runs/1/export-csv
```

返回说明：
- 成功：返回下载文件 `test_run_{run_id}_results.csv`
- `Content-Type`: `text/csv; charset=utf-8-sig`
- `Content-Disposition`: `attachment; filename="test_run_{run_id}_results.csv"`
- 如果 `run_id` 不存在：返回 `404`，错误信息 `test run not found`
- 如果 `run_id` 存在但没有 results：返回仅包含表头的 CSV

CSV 字段说明：
- `run_id`：测试运行 ID
- `case_id`：用例业务 ID
- `case_name`：用例名称
- `input_text`：测试输入
- `actual_output`：实际输出
- `assert_type`：断言类型
- `expected_value`：期望值
- `passed`：执行结果（`true` -> `通过`，`false` -> `失败`）
- `reason`：通过/失败原因
- `latency_ms`：耗时（毫秒）

## 4. Prompt 版本管理（v0.6）

### POST `/api/prompt-versions`
接口说明：创建 Prompt 版本。

请求示例：

```json
{
  "prompt_name": "需求收集Prompt",
  "version": "V1.7",
  "prompt_content": "你是一个需求分析助手，请根据用户输入提取关键信息。",
  "is_baseline": true,
  "baseline_version_id": null,
  "status": "active",
  "remark": "首次基线版本"
}
```

返回示例：

```json
{
  "id": 1,
  "prompt_name": "需求收集Prompt",
  "version": "V1.7",
  "prompt_content": "你是一个需求分析助手，请根据用户输入提取关键信息。",
  "is_baseline": true,
  "baseline_version_id": null,
  "status": "active",
  "remark": "首次基线版本",
  "created_at": "2026-05-06T10:00:00.000000",
  "updated_at": "2026-05-06T10:00:00.000000"
}
```

### GET `/api/prompt-versions`
接口说明：查询 Prompt 版本列表（第一版不分页，按 `id` 倒序）。

返回示例：

```json
[
  {
    "id": 2,
    "prompt_name": "需求收集Prompt",
    "version": "V1.8",
    "prompt_content": "...",
    "is_baseline": false,
    "baseline_version_id": 1,
    "status": "draft",
    "remark": "基于 V1.7 微调",
    "created_at": "2026-05-06T11:00:00.000000",
    "updated_at": "2026-05-06T11:00:00.000000"
  }
]
```

### GET `/api/prompt-versions/{prompt_version_id}`
接口说明：查询 Prompt 版本详情。

返回示例：

```json
{
  "id": 1,
  "prompt_name": "需求收集Prompt",
  "version": "V1.7",
  "prompt_content": "...",
  "is_baseline": true,
  "baseline_version_id": null,
  "status": "active",
  "remark": "首次基线版本",
  "created_at": "2026-05-06T10:00:00.000000",
  "updated_at": "2026-05-06T10:00:00.000000"
}
```

不存在时：`404 prompt version not found`

### PUT `/api/prompt-versions/{prompt_version_id}`
接口说明：更新 Prompt 版本（全量更新）。

请求示例：

```json
{
  "prompt_name": "需求收集Prompt",
  "version": "V1.7",
  "prompt_content": "你是一个需求分析助手，请根据用户输入提取并结构化输出。",
  "is_baseline": true,
  "baseline_version_id": null,
  "status": "active",
  "remark": "更新输出格式要求"
}
```

返回示例：

```json
{
  "id": 1,
  "prompt_name": "需求收集Prompt",
  "version": "V1.7",
  "prompt_content": "你是一个需求分析助手，请根据用户输入提取并结构化输出。",
  "is_baseline": true,
  "baseline_version_id": null,
  "status": "active",
  "remark": "更新输出格式要求",
  "created_at": "2026-05-06T10:00:00.000000",
  "updated_at": "2026-05-06T12:00:00.000000"
}
```

不存在时：`404 prompt version not found`

## 5. 模型配置管理（v0.6 D2-1）

### POST `/api/model-configs`
接口说明：创建模型配置（不保存 api_key / token）。

请求示例：

```json
{
  "config_name": "通义千问默认配置",
  "provider": "dashscope",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "model": "qwen-plus",
  "temperature": 0.7,
  "top_p": 1.0,
  "max_tokens": 2048,
  "is_default": true,
  "status": "active",
  "remark": "默认 Prompt 测试模型配置"
}
```

返回示例：

```json
{
  "id": 1,
  "config_name": "通义千问默认配置",
  "provider": "dashscope",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "model": "qwen-plus",
  "temperature": 0.7,
  "top_p": 1.0,
  "max_tokens": 2048,
  "is_default": true,
  "status": "active",
  "remark": "默认 Prompt 测试模型配置",
  "created_at": "2026-05-06T13:00:00.000000",
  "updated_at": "2026-05-06T13:00:00.000000"
}
```

### GET `/api/model-configs`
接口说明：查询模型配置列表（第一版不分页，按 `id` 倒序）。

返回示例：

```json
[
  {
    "id": 2,
    "config_name": "OpenAI 通用配置",
    "provider": "openai",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4.1",
    "temperature": 0.3,
    "top_p": 0.95,
    "max_tokens": 1024,
    "is_default": false,
    "status": "active",
    "remark": "用于对比测试",
    "created_at": "2026-05-06T13:30:00.000000",
    "updated_at": "2026-05-06T13:30:00.000000"
  }
]
```

### GET `/api/model-configs/{model_config_id}`
接口说明：查询模型配置详情。

返回示例：

```json
{
  "id": 1,
  "config_name": "通义千问默认配置",
  "provider": "dashscope",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "model": "qwen-plus",
  "temperature": 0.7,
  "top_p": 1.0,
  "max_tokens": 2048,
  "is_default": true,
  "status": "active",
  "remark": "默认 Prompt 测试模型配置",
  "created_at": "2026-05-06T13:00:00.000000",
  "updated_at": "2026-05-06T13:00:00.000000"
}
```

不存在时：`404 model config not found`

### PUT `/api/model-configs/{model_config_id}`
接口说明：更新模型配置，支持部分更新。

部分更新请求示例（仅更新 `remark`）：

```json
{
  "remark": "更新备注"
}
```

全量更新请求示例：

```json
{
  "config_name": "本地模型配置",
  "provider": "local",
  "base_url": "http://127.0.0.1:8001/v1",
  "model": "local-chat-model",
  "temperature": 0.5,
  "top_p": 0.9,
  "max_tokens": 4096,
  "is_default": false,
  "status": "active",
  "remark": "用于本地调试"
}
```

返回示例：

```json
{
  "id": 1,
  "config_name": "通义千问默认配置",
  "provider": "dashscope",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "model": "qwen-plus",
  "temperature": 0.7,
  "top_p": 1.0,
  "max_tokens": 2048,
  "is_default": true,
  "status": "active",
  "remark": "更新备注",
  "created_at": "2026-05-06T13:00:00.000000",
  "updated_at": "2026-05-06T14:00:00.000000"
}
```

不存在时：`404 model config not found`

## 6. Prompt 文本单轮执行（v0.6 D3-1）

### POST `/api/prompt-test-runs/run-once`
接口说明：选择 `PromptVersion + ModelConfig`，执行一次 Prompt 单轮调用并保存 run/result。

请求示例：

```json
{
  "prompt_version_id": 1,
  "model_config_id": 1,
  "input_text": "我想做一个智能台灯"
}
```

返回示例（成功）：

```json
{
  "run_id": 1,
  "result_id": 1,
  "status": "success",
  "prompt_version_id": 1,
  "model_config_id": 1,
  "actual_output": "这是模型返回的内容",
  "duration_ms": 1234,
  "error_message": null
}
```

返回示例（未配置 API Key）：

```json
{
  "run_id": 2,
  "result_id": 2,
  "status": "failed",
  "prompt_version_id": 1,
  "model_config_id": 1,
  "actual_output": "MODEL_API_KEY_NOT_CONFIGURED",
  "duration_ms": 0,
  "error_message": "MODEL_API_KEY_NOT_CONFIGURED"
}
```

说明：
- 参数错误或资源不存在返回 4xx。
- 模型调用失败时，接口仍返回 200，`status=failed`，错误写入 `error_message`。
- API Key 环境变量读取顺序：
  1. `AI_TEST_MODEL_API_KEY`
  2. `OPENAI_API_KEY`
  3. `DASHSCOPE_API_KEY`

### GET `/api/prompt-test-runs`
接口说明：查询 Prompt 执行记录列表（第一版不分页，按 `id` 倒序）。

返回示例：

```json
[
  {
    "id": 2,
    "prompt_version_id": 1,
    "model_config_id": 1,
    "input_text": "我想做一个智能台灯",
    "prompt_content_snapshot": "你是一个产品需求助手...",
    "model_config_snapshot": "{\"id\":1,\"config_name\":\"通义千问默认配置\"}",
    "repeat_count": 1,
    "status": "failed",
    "started_at": "2026-05-06T15:00:00.000000",
    "finished_at": "2026-05-06T15:00:01.000000",
    "duration_ms": 1000,
    "error_message": "MODEL_API_KEY_NOT_CONFIGURED"
  }
]
```

### GET `/api/prompt-test-runs/{run_id}`
接口说明：查询 Prompt 执行记录详情（包含 run + result）。

返回示例：

```json
{
  "run": {
    "id": 1,
    "prompt_version_id": 1,
    "model_config_id": 1,
    "input_text": "我想做一个智能台灯",
    "prompt_content_snapshot": "你是一个产品需求助手...",
    "model_config_snapshot": "{\"id\":1,\"config_name\":\"通义千问默认配置\"}",
    "repeat_count": 1,
    "status": "success",
    "started_at": "2026-05-06T14:30:00.000000",
    "finished_at": "2026-05-06T14:30:01.000000",
    "duration_ms": 1200,
    "error_message": null
  },
  "result": {
    "id": 1,
    "run_id": 1,
    "repeat_index": 1,
    "actual_output": "这是模型返回的内容",
    "raw_response": "{\"choices\":[{\"message\":{\"content\":\"这是模型返回的内容\"}}]}",
    "error_message": null,
    "duration_ms": 1200,
    "created_at": "2026-05-06T14:30:01.000000"
  }
}
```

不存在时：`404 prompt test run not found`

### D3-2 断言能力补充（适用于 `POST /api/prompt-test-runs/run-once`）

新增可选请求字段：

- `assert_type`：`contains` / `regex` / `json_valid`
- `expected_value`：可选；当 `assert_type` 为 `contains` 或 `regex` 时必填

带断言请求示例：

```json
{
  "prompt_version_id": 1,
  "model_config_id": 1,
  "input_text": "我想做一个智能台灯",
  "assert_type": "contains",
  "expected_value": "智能台灯"
}
```

响应新增字段：`assertion`

- `assert_type`
- `expected_value`
- `assertion_status`：`passed` / `failed` / `skipped`
- `assertion_passed`：`true` / `false` / `null`
- `assertion_reason`

断言通过响应示例：

```json
{
  "run_id": 10,
  "result_id": 10,
  "status": "success",
  "prompt_version_id": 1,
  "model_config_id": 3,
  "actual_output": "这是一个智能台灯方案",
  "duration_ms": 3000,
  "error_message": null,
  "assertion": {
    "assert_type": "contains",
    "expected_value": "智能台灯",
    "assertion_status": "passed",
    "assertion_passed": true,
    "assertion_reason": "contains assertion passed"
  }
}
```

模型调用失败且传入断言时：

```json
{
  "run_id": 11,
  "result_id": 11,
  "status": "failed",
  "prompt_version_id": 1,
  "model_config_id": 3,
  "actual_output": "MODEL_API_KEY_NOT_CONFIGURED",
  "duration_ms": 0,
  "error_message": "MODEL_API_KEY_NOT_CONFIGURED",
  "assertion": {
    "assert_type": "contains",
    "expected_value": "智能台灯",
    "assertion_status": "skipped",
    "assertion_passed": null,
    "assertion_reason": "model execution failed, assertion skipped"
  }
}
```

不传 `assert_type` 时：

- 原调用保持兼容
- `assertion` 返回 `null`

参数校验规则：

- 不支持的 `assert_type` 返回 `400 unsupported assert_type`
- `assert_type=contains/regex` 且 `expected_value` 为空时返回 `400 expected_value is required for contains/regex`

### GET `/api/prompt-test-runs/{run_id}`（D3-2 补充）

详情返回增加 `assertion` 字段（如该 run 有断言记录）。

### D3-3 动态输入字段 input_variables（适用于 `POST /api/prompt-test-runs/run-once`）

在 D3-2 基础上，run-once 新增：

- `input_variables`（可选，JSON object）
- `input_text` 保持兼容（可选）
- `input_text` 与 `input_variables` 至少一个有值

请求示例（新方式）：

```json
{
  "prompt_version_id": 1,
  "model_config_id": 3,
  "input_text": "我想做一个智能台灯",
  "input_variables": {
    "product_name": "智能台灯",
    "use_scene": "学生宿舍",
    "target_user": "大学生",
    "main_function": "自动调光",
    "chip_preference": "ESP32"
  },
  "assert_type": "contains",
  "expected_value": "ESP32"
}
```

渲染规则：

- Prompt 占位符仅识别：`{变量名}`，变量名规则：`[a-zA-Z_][a-zA-Z0-9_]*`
- `input_variables` 中同名字段会替换占位符
- `input_text` 会自动加入变量池，可通过 `{input_text}` 使用
- 若存在缺失变量，返回 `400`：`missing prompt variables: xxx`

模型消息规则：

- system message：使用 `rendered_prompt`
- user message：优先使用 `input_text`
- 若 `input_text` 为空且有 `input_variables`，user message 使用 `input_variables` 的 JSON 字符串

run-once 响应新增 `input_snapshot`：

```json
{
  "run_id": 20,
  "result_id": 20,
  "status": "success",
  "prompt_version_id": 1,
  "model_config_id": 3,
  "actual_output": "...",
  "duration_ms": 30000,
  "error_message": null,
  "assertion": {
    "assert_type": "contains",
    "expected_value": "ESP32",
    "assertion_status": "passed",
    "assertion_passed": true,
    "assertion_reason": "contains assertion passed"
  },
  "input_snapshot": {
    "input_text": "我想做一个智能台灯",
    "input_variables": {
      "product_name": "智能台灯",
      "use_scene": "学生宿舍",
      "target_user": "大学生",
      "main_function": "自动调光",
      "chip_preference": "ESP32"
    },
    "rendered_prompt": "替换后的最终 Prompt..."
  }
}
```

错误规则补充：

- `input_text` 与 `input_variables` 同时为空：`400 input_text or input_variables is required`
- `input_variables` 不是 object：`400 input_variables must be an object`
- 缺失占位符变量：`400 missing prompt variables: xxx`

### GET `/api/prompt-test-runs/{run_id}`（D3-3 补充）

详情返回增加 `input_snapshot` 字段（如果有）。

## 7. Prompt 执行结果 LLM 自动评分（v0.6 D4-1）

### POST `/api/prompt-test-runs/{run_id}/score`
接口说明：对指定 `run_id` 的 Prompt 单轮执行结果进行一次手动触发评分。

请求示例：

```json
{
  "scorer_model_config_id": 3,
  "expected_behavior": "输出应围绕智能台灯需求进行分析，并提出需要补充的关键信息。",
  "remark": "D4-1 单次结果评分测试"
}
```

返回示例（成功）：

```json
{
  "id": 5,
  "run_id": 20,
  "result_id": 20,
  "scorer_model_config_id": 3,
  "scoring_template_id": "default_prompt_score_v0.6",
  "expected_behavior": "输出应围绕智能台灯需求进行分析，并提出需要补充的关键信息。",
  "dimension_scores": {
    "relevance": 5,
    "completeness": 4,
    "format_correctness": 4,
    "constraint_following": 5,
    "stability_usability": 4
  },
  "total_score": 88,
  "score_reason": "回答与需求相关，结构清晰，但实现细节不足。",
  "problem_points": [
    "硬件选型不够明确",
    "步骤拆解不够细"
  ],
  "suggestion": "建议补充芯片、传感器和通信协议建议。",
  "status": "success",
  "error_message": null,
  "duration_ms": 2200,
  "remark": "D4-1 单次结果评分测试",
  "created_at": "2026-05-06T16:30:00.000000"
}
```

返回示例（未配置 API Key）：

```json
{
  "id": 6,
  "run_id": 20,
  "result_id": 20,
  "scorer_model_config_id": 3,
  "scoring_template_id": "default_prompt_score_v0.6",
  "expected_behavior": null,
  "dimension_scores": null,
  "total_score": null,
  "score_reason": null,
  "problem_points": null,
  "suggestion": null,
  "status": "failed",
  "error_message": "MODEL_API_KEY_NOT_CONFIGURED",
  "duration_ms": 0,
  "remark": null,
  "created_at": "2026-05-06T16:31:00.000000"
}
```

错误规则：
- run 不存在：`404 prompt test run not found`
- run 对应 result 不存在：`404 prompt test result not found`
- `scorer_model_config_id` 不存在：`404 model config not found`

### GET `/api/prompt-test-runs/{run_id}/scores`
接口说明：查询指定 run 的评分历史（按 id 倒序）。

返回示例：

```json
[
  {
    "id": 6,
    "run_id": 20,
    "result_id": 20,
    "scorer_model_config_id": 3,
    "scoring_template_id": "default_prompt_score_v0.6",
    "expected_behavior": null,
    "dimension_scores": null,
    "total_score": null,
    "score_reason": null,
    "problem_points": null,
    "suggestion": null,
    "status": "failed",
    "error_message": "MODEL_API_KEY_NOT_CONFIGURED",
    "duration_ms": 0,
    "remark": null,
    "created_at": "2026-05-06T16:31:00.000000"
  },
  {
    "id": 5,
    "run_id": 20,
    "result_id": 20,
    "scorer_model_config_id": 3,
    "scoring_template_id": "default_prompt_score_v0.6",
    "expected_behavior": "输出应围绕智能台灯需求进行分析，并提出需要补充的关键信息。",
    "dimension_scores": {
      "relevance": 5,
      "completeness": 4,
      "format_correctness": 4,
      "constraint_following": 5,
      "stability_usability": 4
    },
    "total_score": 88,
    "score_reason": "回答与需求相关，结构清晰，但实现细节不足。",
    "problem_points": ["硬件选型不够明确", "步骤拆解不够细"],
    "suggestion": "建议补充芯片、传感器和通信协议建议。",
    "status": "success",
    "error_message": null,
    "duration_ms": 2200,
    "remark": "D4-1 单次结果评分测试",
    "created_at": "2026-05-06T16:30:00.000000"
  }
]
```

### GET `/api/prompt-test-runs/{run_id}`（D4-1 补充）
详情接口在原有 `run / result / assertion / input_snapshot` 基础上新增：

- `latest_score`：该 run 最新一条评分结果；无评分时为 `null`。

### D4-1 解析鲁棒性补充

评分解析兼容以下返回形式：

- 纯 JSON
- ```json ... ``` 代码块
- ``` ... ``` 代码块
- JSON 前后有少量解释文本

并支持：

- `dimension_scores` 中文字段映射：
  - 相关性 -> relevance
  - 完整性 -> completeness
  - 格式正确性 -> format_correctness
  - 约束遵守 -> constraint_following
  - 稳定可用性 -> stability_usability
- 维度分数字符串（如 "4"）自动转数字并裁剪到 1-5
- `total_score` 缺失时自动按 5 维分计算
- `score_reason`/`suggestion` 缺失时默认空字符串
- `problem_points` 缺失时默认空数组

评分响应新增 `raw_response` 字段，便于本地排查模型原始返回。

## 8. 人工复核（v0.6 D5-1）

### POST `/api/prompt-test-runs/{run_id}/manual-review`
接口说明：对指定 run 提交人工复核结论。

请求示例：

```json
{
  "manual_status": "passed",
  "manual_remark": "输出符合预期，可以作为通过样本。",
  "reviewer": "tester"
}
```

`manual_status` 仅支持：
- `passed`
- `failed`
- `pending`

返回示例：

```json
{
  "id": 1,
  "run_id": 20,
  "result_id": 20,
  "manual_status": "passed",
  "manual_remark": "输出符合预期，可以作为通过样本。",
  "reviewer": "tester",
  "created_at": "2026-05-06T18:00:00.000000"
}
```

错误规则：
- run 不存在：`404 prompt test run not found`
- run 对应 result 不存在：`404 prompt test result not found`
- 非法状态：`400 unsupported manual_status`

### GET `/api/prompt-test-runs/{run_id}/manual-reviews`
接口说明：查询人工复核历史（按 id 倒序）。

返回示例：

```json
[
  {
    "id": 2,
    "run_id": 20,
    "result_id": 20,
    "manual_status": "failed",
    "manual_remark": "需要补充技术细节",
    "reviewer": "tester2",
    "created_at": "2026-05-06T18:05:00.000000"
  },
  {
    "id": 1,
    "run_id": 20,
    "result_id": 20,
    "manual_status": "passed",
    "manual_remark": "输出符合预期，可以作为通过样本。",
    "reviewer": "tester",
    "created_at": "2026-05-06T18:00:00.000000"
  }
]
```

### GET `/api/prompt-test-runs/{run_id}`（D5-1 补充）
详情接口在原有 `run / result / assertion / input_snapshot / latest_score` 基础上新增：

- `latest_manual_review`：最新一条人工复核；无复核时为 `null`。

## 9. 重复执行（v0.6 D6-1）

### POST `/api/prompt-test-runs/run-repeat`
接口说明：一次请求对同一 Prompt 重复执行多次，保存多条结果。

请求示例：

```json
{
  "prompt_version_id": 1,
  "model_config_id": 3,
  "input_text": "我想做一个智能台灯",
  "input_variables": {
    "product_name": "智能台灯",
    "use_scene": "学生宿舍",
    "target_user": "大学生",
    "main_function": "自动调光",
    "chip_preference": "ESP32"
  },
  "assert_type": "contains",
  "expected_value": "智能台灯",
  "repeat_count": 3
}
```

字段规则：
- `repeat_count` 范围 1-5，超范围返回 `400 repeat_count must be between 1 and 5`
- `input_text` 与 `input_variables` 至少一项有值
- `input_variables` 必须是 object
- 断言规则沿用 run-once（contains/regex/json_valid）

返回示例：

```json
{
  "run_id": 30,
  "status": "success",
  "prompt_version_id": 1,
  "model_config_id": 3,
  "repeat_count": 3,
  "summary": {
    "total": 3,
    "success_count": 3,
    "failed_count": 0,
    "assertion_passed_count": 3,
    "assertion_failed_count": 0,
    "assertion_skipped_count": 0
  },
  "results": [
    {
      "result_id": 31,
      "repeat_index": 1,
      "status": "success",
      "actual_output": "...",
      "duration_ms": 1200,
      "error_message": null,
      "assertion": {
        "assert_type": "contains",
        "expected_value": "智能台灯",
        "assertion_status": "passed",
        "assertion_passed": true,
        "assertion_reason": "contains assertion passed"
      }
    },
    {
      "result_id": 32,
      "repeat_index": 2,
      "status": "success",
      "actual_output": "...",
      "duration_ms": 1300,
      "error_message": null,
      "assertion": {
        "assert_type": "contains",
        "expected_value": "智能台灯",
        "assertion_status": "passed",
        "assertion_passed": true,
        "assertion_reason": "contains assertion passed"
      }
    },
    {
      "result_id": 33,
      "repeat_index": 3,
      "status": "success",
      "actual_output": "...",
      "duration_ms": 1250,
      "error_message": null,
      "assertion": {
        "assert_type": "contains",
        "expected_value": "智能台灯",
        "assertion_status": "passed",
        "assertion_passed": true,
        "assertion_reason": "contains assertion passed"
      }
    }
  ],
  "input_snapshot": {
    "input_text": "我想做一个智能台灯",
    "input_variables": {
      "product_name": "智能台灯"
    },
    "rendered_prompt": "..."
  }
}
```

### GET `/api/prompt-test-runs/{run_id}`（D6-1 补充）
详情接口在原有字段基础上新增：

- `results`：该 run 下所有执行结果，按 `repeat_index` 升序。

说明：
- 兼容旧 run-once：`result` 字段继续保留。
- 多次执行场景下，`results` 可查看每次结果与对应断言。

## 10. 执行摘要报告（v0.6 D7-1）

### GET `/api/prompt-test-runs/{run_id}/summary`
接口说明：查询单个 Prompt 测试执行批次的摘要/报告，用于人工判断前的快速聚合信息查看。

该接口返回：
- `run_info`：run 基本信息
- `prompt_version`：Prompt 版本信息
- `model_config`：模型配置信息
- `input_snapshot`：输入快照（`input_text` / `input_variables` / `rendered_prompt`）
- `result_summary`：执行与断言统计
- `latest_score`：最新评分（无则 `null`）
- `latest_manual_review`：最新人工复核（无则 `null`）
- `manual_check_suggestion`：是否建议人工确认及原因
- `failure_summary`：失败/异常摘要（最多前 5 条）

请求示例：

```http
GET /api/prompt-test-runs/30/summary
```

返回示例：

```json
{
  "run_id": 30,
  "status": "partial_success",
  "prompt_version_id": 1,
  "model_config_id": 3,
  "run_info": {
    "id": 30,
    "status": "partial_success",
    "prompt_version_id": 1,
    "model_config_id": 3,
    "started_at": "2026-05-07T09:00:00.000000",
    "finished_at": "2026-05-07T09:00:12.000000",
    "duration_ms": 12000,
    "error_message": "partial repeats failed"
  },
  "prompt_version": {
    "id": 1,
    "prompt_name": "需求收集Prompt",
    "version": "V1.7",
    "is_baseline": false,
    "baseline_version_id": null,
    "status": "active"
  },
  "model_config": {
    "id": 3,
    "config_name": "通义千问默认配置",
    "provider": "dashscope",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen-plus",
    "temperature": 0.7,
    "top_p": 1.0,
    "max_tokens": 2048,
    "is_default": true,
    "status": "active"
  },
  "input_snapshot": {
    "input_text": "我想做一个智能台灯",
    "input_variables": {
      "product_name": "智能台灯"
    },
    "rendered_prompt": "你是一个需求分析助手..."
  },
  "result_summary": {
    "total": 3,
    "success_count": 2,
    "failed_count": 1,
    "assertion_passed_count": 2,
    "assertion_failed_count": 0,
    "assertion_skipped_count": 1,
    "success_rate": 0.6666666667,
    "assertion_pass_rate": 0.6666666667
  },
  "latest_score": null,
  "latest_manual_review": null,
  "manual_check_suggestion": {
    "need_manual_check": true,
    "reasons": [
      "存在执行失败结果",
      "当前 run 尚未进行 LLM 评分",
      "当前 run 尚未进行人工复核",
      "当前 run 状态不是 success"
    ]
  },
  "failure_summary": [
    {
      "result_id": 101,
      "repeat_index": 3,
      "status": "failed",
      "assertion_status": "skipped",
      "reason_summary": "HTTP_ERROR: timeout | model execution failed, assertion skipped",
      "actual_output_summary": "HTTP_ERROR: timeout"
    }
  ]
}
```

错误规则：
- run 不存在：`404 prompt test run not found`
- run 无结果：正常返回，`result_summary.total = 0`

说明：
- 该接口不做基线对比。
- 该接口不做自动准入判断，只提供人工判断所需摘要信息。

## 11. 执行报告 Markdown（v0.6 D7-2A）

### GET `/api/prompt-test-runs/{run_id}/report-markdown`
接口说明：导出单个 Prompt 执行批次的 Markdown 报告文本，便于复制到 Word、飞书文档或测试汇报材料。

返回类型：
- `text/markdown; charset=utf-8`

请求示例：

```http
GET /api/prompt-test-runs/30/report-markdown
```

返回内容包含：
- 执行基本信息
- Prompt 版本信息
- 模型配置信息
- 输入信息摘要
- 执行结果摘要
- LLM 自动评分
- 人工复核
- 建议人工确认项
- 失败摘要（最多 5 条）

说明：
- 不做基线对比。
- 不做自动准入判断。
- 不包含 api_key/token。
- 不输出完整 prompt_content。
- rendered_prompt 仅输出摘要（超长截断）。

错误规则：
- run 不存在：`404 prompt test run not found`

## 12. 执行批次对比（v0.6 D8-1A）

### GET `/api/prompt-test-runs/{run_id}/compare?baseline_run_id=xxx`
接口说明：对比当前 Prompt 执行批次（`run_id`）与指定基线执行批次（`baseline_run_id`）的摘要指标。

说明：
- 本接口只对比两个 run 的摘要指标。
- 不自动查找 baseline run。
- 不做自动准入判断。
- 不做前端页面。
- 不生成 Markdown 对比报告。

对比内容：
- `success_rate` 差值
- `assertion_pass_rate` 差值
- `latest_score.total_score` 差值（任一缺失则为 `null`）
- `latest_manual_review`（当前与基线均在 summary 中返回）
- `baseline_relation_matched`
- `manual_check_suggestion`

请求示例：

```http
GET /api/prompt-test-runs/18/compare?baseline_run_id=16
```

返回示例：

```json
{
  "current_run_id": 18,
  "baseline_run_id": 16,
  "current_summary": {
    "run_id": 18,
    "status": "success",
    "prompt_version_id": 5,
    "model_config_id": 3,
    "run_info": {
      "id": 18,
      "status": "success",
      "prompt_version_id": 5,
      "model_config_id": 3,
      "started_at": "2026-05-07T10:00:00.000000",
      "finished_at": "2026-05-07T10:00:05.000000",
      "duration_ms": 5000,
      "error_message": null
    },
    "prompt_version": {
      "id": 5,
      "prompt_name": "需求收集Prompt",
      "version": "V1.8",
      "is_baseline": false,
      "baseline_version_id": 4,
      "status": "active"
    },
    "model_config": {
      "id": 3,
      "config_name": "通义千问默认配置",
      "provider": "dashscope",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "model": "qwen-plus",
      "temperature": 0.7,
      "top_p": 1.0,
      "max_tokens": 2048,
      "is_default": true,
      "status": "active"
    },
    "input_snapshot": null,
    "result_summary": {
      "total": 3,
      "success_count": 3,
      "failed_count": 0,
      "assertion_passed_count": 3,
      "assertion_failed_count": 0,
      "assertion_skipped_count": 0,
      "success_rate": 1.0,
      "assertion_pass_rate": 1.0
    },
    "latest_score": null,
    "latest_manual_review": null,
    "manual_check_suggestion": {
      "need_manual_check": true,
      "reasons": []
    },
    "failure_summary": []
  },
  "baseline_summary": {
    "run_id": 16,
    "status": "success",
    "prompt_version_id": 4,
    "model_config_id": 3,
    "run_info": {
      "id": 16,
      "status": "success",
      "prompt_version_id": 4,
      "model_config_id": 3,
      "started_at": "2026-05-07T09:00:00.000000",
      "finished_at": "2026-05-07T09:00:04.000000",
      "duration_ms": 4000,
      "error_message": null
    },
    "prompt_version": null,
    "model_config": null,
    "input_snapshot": null,
    "result_summary": {
      "total": 3,
      "success_count": 3,
      "failed_count": 0,
      "assertion_passed_count": 3,
      "assertion_failed_count": 0,
      "assertion_skipped_count": 0,
      "success_rate": 1.0,
      "assertion_pass_rate": 1.0
    },
    "latest_score": null,
    "latest_manual_review": null,
    "manual_check_suggestion": {
      "need_manual_check": true,
      "reasons": []
    },
    "failure_summary": []
  },
  "comparison": {
    "success_rate_diff": 0.0,
    "assertion_pass_rate_diff": 0.0,
    "total_score_diff": null,
    "result": "need_manual_check",
    "reasons": [
      "当前 run 缺少 LLM 评分",
      "基线 run 缺少 LLM 评分"
    ]
  },
  "manual_check_suggestion": {
    "need_manual_check": true,
    "reasons": [
      "对比结果需要人工确认",
      "当前 run 缺少 LLM 评分",
      "基线 run 缺少 LLM 评分",
      "当前 run 缺少人工复核",
      "基线 run 缺少人工复核"
    ]
  },
  "baseline_relation_matched": true
}
```

错误规则：
- `run_id` 不存在：`404 prompt test run not found`
- `baseline_run_id` 不存在：`404 prompt test run not found`
- `run_id == baseline_run_id`：`400 run_id and baseline_run_id cannot be the same`
