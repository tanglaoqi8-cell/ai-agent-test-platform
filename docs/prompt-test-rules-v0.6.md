# Prompt 测试规则设计 v0.6

## 1. 文档目标

本文档用于指导“通用 AI 测试评估平台”在 v0.6 阶段的 Prompt 测试能力建设，明确测试对象、数据字段、执行流程、结果判定与报告规则，作为后续后端与前端分步开发依据。

## 2. v0.6 范围边界

- v0.6 以单轮 Prompt 测试为主。
- 数据结构和规则设计需预留多轮扩展能力，但第一阶段不实现完整多轮执行。
- 第一阶段先完成规则文档，不直接开发功能。
- LLM 自动评分只作为辅助判断，不作为唯一准入依据。
- 最终是否准入由人工判断。
- 必须保持与当前 v0.5 能力边界兼容，不破坏已有能力。

## 3. Prompt 测试对象

v0.6 支持两种 Prompt 测试对象：

1. Prompt 文本本身
2. Prompt 封装后的 HTTP 接口

规则说明：

- v0.6 第一优先级：Prompt 文本本身（主路径）。
- HTTP 接口方式：兼容扩展路径，用于适配已有服务。
- 测试规则不绑定具体业务类型（如客服、代码、RAG、Agent），保持通用性。

## 4. Prompt 版本与基线版本规则

Prompt 版本管理与对比规则如下：

- 每个 Prompt 必须有版本号（`version`），可与 `prompt_name` 组合唯一定位。
- 每次对比必须明确一个基线版本（`is_baseline=true` 或显式关联 `baseline_version_id`）。
- 当前待评估版本必须与同一基线版本对比，避免多基线混用导致结论不稳定。
- 对比前提尽量一致：同一批用例、同一评分标准、同一模型配置。

示例：

- 某次发版选择 `V1.7` 作为基线版本。
- 下一轮候选版本 `V2.1` 到 `V2.9` 分别对比 `V1.7`。
- 结合断言、评分与人工复核，选择综合效果更好的版本进入后续流程。

## 5. Prompt 测试用例规则

### 5.1 用例等级

支持等级：

- P0
- P1
- P2

规则：

- 第一阶段仅用于统计与报告展示。
- 不直接作为强制准入规则。
- 是否准入最终由人工判断。

### 5.2 用例分类

建议分类：

- normal
- insufficient_info
- delegation
- conflict
- format
- abnormal
- safety
- stability

规则：

- 第一阶段用于筛选、统计、报告分组。
- 不直接作为强制准入规则。

### 5.3 tags 标签

规则：

- `tags` 使用逗号分隔（示例：`finance,tool_call,strict_format`）。
- 用于筛选、统计、报告聚合。
- 第一阶段不做标签管理页面。

### 5.4 expected_behavior

规则：

- `expected_behavior` 用于人工复核参考。
- 同时可作为 LLM 自动评分输入上下文。
- 第一阶段建议填写，但不强制每条用例必填。

## 6. 字段规划

### 6.1 Prompt 版本字段

| 字段名 | 类型建议 | 必填 | 说明 |
|---|---|---|---|
| prompt_version_id | string | 是 | Prompt 版本唯一 ID |
| prompt_name | string | 是 | Prompt 名称 |
| version | string | 是 | 版本号（如 V1.7） |
| prompt_content | text | 是 | Prompt 文本内容 |
| is_baseline | boolean | 是 | 是否基线版本 |
| baseline_version_id | string | 否 | 关联基线版本 ID |
| status | string | 是 | 状态（draft/active/archived 等） |
| created_at | datetime | 是 | 创建时间 |
| updated_at | datetime | 是 | 更新时间 |
| remark | string | 否 | 备注 |

### 6.2 模型配置字段

| 字段名 | 类型建议 | 必填 | 说明 |
|---|---|---|---|
| provider | string | 是 | 模型服务提供方 |
| base_url | string | 是 | 调用地址 |
| model | string | 是 | 模型名称 |
| temperature | number | 是 | 温度参数 |
| top_p | number | 是 | top_p 参数 |
| max_tokens | integer | 是 | 最大输出 token |

对比公平性要求：

- 同一批用例。
- 同一个评分标准。
- 同一个模型配置。
- 避免因模型差异造成对比不公平。

### 6.3 Prompt 测试用例字段

| 字段名 | 类型建议 | 必填 | 说明 |
|---|---|---|---|
| case_id | string | 是 | 用例唯一 ID |
| case_name | string | 是 | 用例名称 |
| input_text | text | 是 | 输入内容 |
| expected_behavior | text | 否 | 期望行为描述 |
| assert_type | string | 是 | 断言类型 |
| expected_value | text | 否 | 断言目标值 |
| priority | string | 是 | P0/P1/P2 |
| category | string | 是 | 用例分类 |
| tags | string | 否 | 逗号分隔标签 |
| enabled | boolean | 是 | 是否启用 |
| remark | string | 否 | 备注 |

当前已有断言类型必须保留：

- `contains`
- `regex`
- `json_valid`

兼容说明：

- 用例可继续支持 CSV 导入思路，字段与 CSV 列一一映射。

### 6.4 执行批次字段

| 字段名 | 类型建议 | 必填 | 说明 |
|---|---|---|---|
| run_id | string | 是 | 执行批次 ID |
| prompt_version_id | string | 是 | 当前版本 ID |
| baseline_version_id | string | 否 | 基线版本 ID |
| suite_id | string | 是 | 用例集 ID |
| model_config_snapshot | json | 是 | 执行时模型配置快照 |
| repeat_count | integer | 是 | 重复执行次数 |
| scoring_template_id | string | 是 | 评分模板 ID（v0.6 可为默认模板 ID） |
| started_at | datetime | 是 | 开始时间 |
| finished_at | datetime | 否 | 完成时间 |
| status | string | 是 | running/success/failed/partial |

### 6.5 执行结果字段

执行结果必须记录：

- 输入内容
- Prompt 版本
- 是否基线版本
- 模型配置
- 完整原始输出
- 断言结果
- LLM 评分
- 人工复核
- 执行耗时
- 错误信息

建议字段：

| 字段名 | 类型建议 | 必填 | 说明 |
|---|---|---|---|
| result_id | string | 是 | 结果 ID |
| run_id | string | 是 | 所属批次 ID |
| case_id | string | 是 | 用例 ID |
| repeat_index | integer | 是 | 第几次重复执行（从 1 开始） |
| actual_output | text | 否 | 实际输出原文 |
| assertion_passed | boolean | 否 | 规则断言是否通过 |
| assertion_reason | text | 否 | 断言说明（失败原因/命中详情） |
| llm_total_score | number | 否 | LLM 总分 |
| llm_dimension_scores | json | 否 | 各维度分数 |
| llm_score_reason | text | 否 | 评分理由与问题点 |
| manual_status | string | 否 | 人工结论（pass/fail/pending） |
| manual_remark | text | 否 | 人工备注 |
| duration_ms | integer | 否 | 执行耗时毫秒 |
| error_message | text | 否 | 错误信息 |

## 7. 断言规则

v0.6 断言采用两层机制：

第一层：规则断言

- `contains`
- `regex`
- `json_valid`

第二层：LLM 自动评分

- 由大模型从质量维度给分。
- 输出评分、评分原因、主要问题点。
- 用于辅助判断 Prompt 质量。

关键原则：

- LLM 评分不能作为唯一准入依据。
- 必须结合规则断言结果与人工复核结论综合判定。

## 8. LLM 自动评分规则

评分输出结构：

- 多维度评分
- 总分
- 评分理由

v0.6 第一版评分维度：

1. 相关性
2. 完整性
3. 格式正确性
4. 约束遵守
5. 稳定可用性

版本约束：

- v0.6 先内置一套默认评分模板。
- 暂不做自定义评分模板管理页面。
- 后续版本可扩展评分模板管理能力。

## 9. 人工复核规则

v0.6 第一版采用轻量人工复核：

1. 人工判定：通过 / 失败 / 待确认
2. 人工备注

v0.6 暂不实现：

- 完整审批流
- 权限控制
- 强制复核人管理

## 10. repeat_count 稳定性测试

规则：

- Prompt 测试需支持重复执行（`repeat_count`）。
- 第一版推荐 3 次或 5 次。
- 第一阶段只做统计分析，不直接作为强制准入规则。

建议统计项：

- 多次执行通过率
- 输出稳定性（如格式一致性、关键字段一致性）
- LLM 平均分
- LLM 最低分
- 是否出现偶发失败

## 11. 执行流程

1. 选择 Prompt 版本。
2. 选择测试用例集。
3. 选择模型配置。
4. 设置 `repeat_count`。
5. 执行 Prompt 测试。
6. 执行规则断言。
7. 执行 LLM 自动评分。
8. 保存完整执行结果。
9. 人工复核。
10. 生成批次摘要。
11. 与基线版本对比。
12. 人工决定是否准入。

## 12. 结果判定规则

判定原则：

- 结果判定不能只看单一指标。

建议综合指标：

- 规则断言结果
- LLM 自动评分
- P0 / P1 / P2 通过率
- 分类通过率
- repeat_count 稳定性
- 人工复核结论
- 当前版本 vs 基线版本表现

最终状态建议：

- 优于基线
- 持平
- 低于基线
- 需要人工确认

## 13. 测试报告规则

v0.6 第一版 Prompt 测试报告需支持：

- 批次摘要
- 基线版本对比

报告至少展示：

1. 总数
2. 通过数
3. 失败数
4. 通过率
5. 平均 LLM 分
6. 最低 LLM 分
7. 各维度平均分
8. P0 / P1 / P2 通过率
9. 分类通过率
10. 失败摘要
11. 当前版本 vs 基线版本
12. 优于基线 / 持平 / 低于基线 / 需要人工确认

## 14. v0.6 后续开发拆分

采用小步快跑，逐步验证，不一次性开发。

- D1：Prompt 版本数据结构设计
- D2：模型配置数据结构设计
- D3：Prompt 文本单轮执行
- D4：LLM 自动评分
- D5：人工复核
- D6：重复执行 `repeat_count`
- D7：批次摘要报告
- D8：基线版本对比报告

执行原则：

- 每次只做一个小步。
- 每个阶段完成后必须本地验证。
- 验证稳定后再做备份。

## 15. 暂不做内容

v0.6 第一阶段暂不做：

- 不做完整多轮对话测试执行
- 不做复杂审批流
- 不做权限管理
- 不做评分模板管理页面
- 不做标签管理页面
- 不做复杂 Prompt 发布流程
- 不做大范围数据库重构
- 不绑定具体业务 Prompt

## 附录 A：与 v0.5 现有能力兼容要求

v0.6 规则设计必须保留并兼容以下已有能力：

- 断言类型：`contains`、`regex`、`json_valid`
- 测试运行：`test run`
- 结果记录：`result`
- 用例来源：CSV 用例思路

兼容目标：

- 不破坏当前 v0.5 可用能力。
- 在现有能力上增加 Prompt 版本对比、LLM 评分、人工复核与稳定性统计规则。
