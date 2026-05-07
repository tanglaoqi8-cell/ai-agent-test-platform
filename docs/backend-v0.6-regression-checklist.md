# v0.6 后端接口最小回归清单

## 1. 文档目的

本清单用于 v0.6 后端能力修改后的最小回归验证，不替代完整测试报告。

## 2. 验证前准备

1. 启动项目：`C:\Projects\ai-agent-test-platform\deploy\start-dev.bat`
2. 打开 Swagger：`http://127.0.0.1:8000/docs`
3. 确认 API Key：后端模型调用依赖 Windows 用户环境变量 `AI_TEST_MODEL_API_KEY`
4. 说明：
- 本文中的 `prompt_version_id`、`model_config_id`、`run_id` 以本地实际数据为准
- 不要把 `api_key/token` 写入请求体、数据库或文档

## 3. 必测接口清单

### 3.1 Prompt 版本管理

接口：
- `POST /api/prompt-versions`
- `GET /api/prompt-versions`
- `GET /api/prompt-versions/{prompt_version_id}`
- `PUT /api/prompt-versions/{prompt_version_id}`

接口用途：维护 Prompt 版本基础信息。

最小验证方式：
1. 创建一个 Prompt 版本
2. 查询列表
3. 查询详情
4. 更新 `remark` 或 `status`

预期结果：
1. 创建成功
2. 列表能看到数据
3. 详情字段完整
4. 更新后字段生效

测试级别：必测

### 3.2 模型配置管理

接口：
- `POST /api/model-configs`
- `GET /api/model-configs`
- `GET /api/model-configs/{model_config_id}`
- `PUT /api/model-configs/{model_config_id}`

接口用途：维护模型配置（不含密钥）。

最小验证方式：
1. 创建或确认已有模型配置
2. 查询列表
3. 查询详情
4. 更新 `remark` 或 `status`

预期结果：
1. `provider`、`base_url`、`model` 等字段正常保存
2. 不保存 `api_key/token`
3. 查询结果字段完整

测试级别：必测

### 3.3 Prompt 单轮执行

接口：
- `POST /api/prompt-test-runs/run-once`

接口用途：执行一次 Prompt 并保存 run/result。

最小验证方式：
1. 选择 `prompt_version_id`
2. 选择 `model_config_id`
3. 输入 `input_text`
4. 可带 `contains` 断言

预期结果：
1. 返回 `run_id`
2. `status` 为 `success` 或明确错误
3. `result` 正常保存
4. `assertion` 正常返回
5. `input_snapshot` 正常返回

测试级别：必测

### 3.4 动态输入字段 input_variables

接口：
- `POST /api/prompt-test-runs/run-once`

接口用途：支持多字段动态输入并渲染 Prompt。

最小验证方式：
1. 传入 `input_variables`（示例字段）：
```json
{
  "product_name": "智能台灯",
  "use_scene": "学生宿舍"
}
```
2. 可同时传 `input_text`

预期结果：
1. 占位符能被替换
2. `rendered_prompt` 能保存
3. `input_variables` 能返回
4. 兼容 `input_text`

测试级别：必测

### 3.5 repeat_count 重复执行

接口：
- `POST /api/prompt-test-runs/run-repeat`

接口用途：同一输入重复执行并保存多条结果。

最小验证方式：
1. `repeat_count=3`
2. 执行同一个 Prompt

预期结果：
1. 返回 `run_id`
2. `results` 数量为 3
3. `repeat_index` 为 `1,2,3`
4. `summary.total=3`
5. 每次断言结果正常

测试级别：必测

### 3.6 执行详情查询

接口：
- `GET /api/prompt-test-runs`
- `GET /api/prompt-test-runs/{run_id}`

接口用途：查询 run 列表与详情。

最小验证方式：
1. 查询 run 列表
2. 查询某个 run 详情

预期结果：
1. 列表能看到执行记录
2. 详情包含 `result/results`
3. 详情包含 `assertion`
4. 详情包含 `input_snapshot`
5. 详情包含 `latest_score`
6. 详情包含 `latest_manual_review`

测试级别：必测

### 3.7 LLM 自动评分

接口：
- `POST /api/prompt-test-runs/{run_id}/score`
- `GET /api/prompt-test-runs/{run_id}/scores`

接口用途：对已执行结果进行人工触发评分并查看历史。

最小验证方式：
1. 对一个已有 run 发起评分
2. 查询评分记录

预期结果：
1. `total_score` 为 0-100
2. `dimension_scores` 有五个维度
3. `score_reason` 有内容
4. `problem_points/suggestion` 字段存在
5. 成功时 `raw_response` 为 `null`
6. 失败时保留必要错误信息

测试级别：必测

### 3.8 人工复核

接口：
- `POST /api/prompt-test-runs/{run_id}/manual-review`
- `GET /api/prompt-test-runs/{run_id}/manual-reviews`

接口用途：提交和查询人工复核记录。

最小验证方式：
1. 提交 `manual_status`
2. 填写 `manual_remark`
3. 填写 `reviewer`
4. 查询复核记录

预期结果：
1. 可提交 `passed/failed/pending`
2. 可多次提交
3. 查询能看到记录
4. run 详情返回 `latest_manual_review`

测试级别：必测

### 3.9 Summary 摘要接口

接口：
- `GET /api/prompt-test-runs/{run_id}/summary`

接口用途：聚合单个 run 的执行摘要信息。

最小验证方式：
1. 用已有 `run_id` 查询 summary
2. 用 `repeat_count=3` 的 run 查询 summary

预期结果：
1. 返回 `run_info`
2. 返回 `prompt_version`
3. 返回 `model_config`
4. 返回 `input_snapshot`
5. 返回 `result_summary`
6. 返回 `latest_score`
7. 返回 `latest_manual_review`
8. 返回 `manual_check_suggestion`
9. 返回 `failure_summary`
10. `repeat_count=3` 时 `result_summary.total=3`

测试级别：必测

### 3.10 Markdown 报告接口

接口：
- `GET /api/prompt-test-runs/{run_id}/report-markdown`

接口用途：输出单个 run 的 Markdown 报告。

最小验证方式：
1. 用已有 `run_id` 查询
2. 查看返回内容是否为 Markdown 文本

预期结果（至少包含章节）：
1. Prompt 测试执行报告
2. 执行基本信息
3. Prompt 版本信息
4. 模型配置信息
5. 输入信息摘要
6. 执行结果摘要
7. LLM 自动评分
8. 人工复核
9. 建议人工确认项
10. 失败摘要

同时确认：
1. 不输出 `api_key/token`
2. 不输出完整 `prompt_content`
3. `rendered_prompt` 过长时有截断

测试级别：必测

### 3.11 Run 对比接口

接口：
- `GET /api/prompt-test-runs/{run_id}/compare?baseline_run_id=xxx`

接口用途：对比当前 run 与指定 baseline run 的摘要指标。

最小验证方式：
1. 使用两个不同 `run_id` 对比
2. 测 `run_id == baseline_run_id`
3. 测不存在的 `run_id`
4. 测不存在的 `baseline_run_id`

预期结果：
1. 正常对比返回 `current_summary`
2. 正常对比返回 `baseline_summary`
3. 返回 `comparison`
4. 返回 `manual_check_suggestion`
5. 返回 `baseline_relation_matched`
6. `run_id == baseline_run_id` 返回 400
7. 不存在 run 返回 404
8. `comparison.result` 只能是：`better/worse/equal/need_manual_check`

测试级别：必测

## 4. 抽测接口清单

以下内容建议抽测：
1. `contains/regex/json_valid` 三种断言分别抽测一条
2. 评分失败场景抽测
3. 人工复核多次提交抽测
4. 对比接口缺少评分时 `need_manual_check` 抽测
5. 模型配置不同导致人工确认提示抽测
6. 执行次数不同导致人工确认提示抽测

## 5. 本轮不测内容

1. 前端页面
2. CSV 导出
3. 老的 `test-targets/test-runs` 主流程（除非本轮改到相关代码）
4. 权限审批流
5. 自动准入判断
6. 自动查找 baseline run
7. Markdown 对比报告
8. 全量性能测试

## 6. 常见异常判断

| 现象 | 快速判断 |
| --- | --- |
| 401 / 模型调用失败 | 优先检查 `AI_TEST_MODEL_API_KEY` 是否已配置 |
| 404 run not found | 检查 `run_id` 是否存在、是否误用历史环境 ID |
| Pydantic `model_config` 报错 | 检查是否把 `model_config` 直接用作 Pydantic 字段名 |
| `total_score_diff` 为 `null` | 通常是一方缺少 LLM 评分 |
| `comparison.result=need_manual_check` | 通常是缺少评分、缺少人工复核、执行次数不同、模型配置不同或存在失败 |

## 7. 最小回归通过标准

一次 v0.6 后端小改动后，满足以下条件可认为最小回归通过：

1. 后端能启动
2. Swagger 能打开
3. run-once 正常
4. run-repeat 正常
5. summary 正常
6. report-markdown 正常
7. compare 正常
8. 本轮修改相关接口必测通过
9. 未出现数据库结构误改
10. 未出现 `api_key/token` 泄露

## 8. 备份建议

通过最小回归后，再考虑备份。

备份命名格式示例：
- `C:\Projects\ai-agent-test-platform-backup-v0.6-xxx`

当前建议保留：
1. 当前项目主目录
2. 最新稳定备份
3. 上一个稳定备份
4. 当前大阶段完成点
5. 上一个大版本稳定点

当前已保留：
1. `C:\Projects\ai-agent-test-platform`
2. `C:\Projects\ai-agent-test-platform-backup-v0.6-d8-run-compare-api`
3. `C:\Projects\ai-agent-test-platform-backup-v0.6-d7-markdown-report-api`
4. `C:\Projects\ai-agent-test-platform-backup-v0.6-d6-repeat-count-api`
5. `C:\Projects\ai-agent-test-platform-backup-v0.5-ui-chinese`
