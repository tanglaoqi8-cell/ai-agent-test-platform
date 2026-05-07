# v0.6 后端冗余与风险扫描报告

## 1. 扫描范围

本次只读扫描以下范围：

- `backend/app/main.py`
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/crud.py`
- `backend/app/routers/*.py`
- `backend/app/services/*.py`
- `docs/api.md`
- `docs/backend-v0.6-regression-checklist.md`

未修改任何代码文件。

## 2. 总体结论

1. 当前后端主链路完整，**可以进入前端 F1 联调阶段**。
2. 未发现必须立刻停机修复的功能性阻断（无明显会直接导致核心链路全部不可用的缺陷）。
3. 不建议现在做大重构；但建议在前端 F1 并行期间做少量低风险整理。
4. 后续优先关注：
- `prompt_test_runs.py` 复杂度上升
- 文本编码/中文乱码风险（用户可见）
- 无 Alembic 下的数据库迁移风险

## 3. 疑似冗余代码

| 位置 | 类型 | 说明 | 风险等级 | 建议 |
|---|---|---|---|---|
| `backend/app/services/assertions.py` 与 `backend/app/services/assertion_evaluator.py` | 重复逻辑 | 两套断言实现（contains/regex/json_valid）并存，分别服务老流程与 Prompt 流程 | P1 | 保留现状（兼容），后续可统一到一个 evaluator 并做适配层 |
| `backend/app/routers/prompt_test_runs.py` | 可抽取 helper | `summary` 构建逻辑被 `report-markdown/compare` 间接复用，但仍集中在 router | P1 | 后续抽到 service（如 `prompt_report_builder.py`），本轮不动 |
| `backend/app/schemas.py` | Schema 体量偏大 | 历史 test-run + v0.6 prompt-run schemas 全放在同一文件 | P2 | 后续按领域拆分 schema 文件（不影响接口时再做） |
| `backend/app/crud.py` | CRUD 聚合过多 | 传统 test 与 prompt test 全部 CRUD 在一个文件 | P2 | 后续按域拆分（`crud_prompt.py` 等），当前可不做 |
| `backend/app/schemas.py: validate_assert_regex` | 疑似未使用函数 | 本次扫描未见调用点 | P2 | 保留；后续清理时确认调用关系再处理 |

## 4. 文件复杂度风险

| 文件 | 现状 | 风险 | 建议等级 | 建议 |
|---|---|---|---|---|
| `backend/app/routers/prompt_test_runs.py` | 单文件承载 run-once/run-repeat/detail/score/manual-review/summary/report/compare | 复杂度持续上升，修改时容易引发回归 | P1 | 前端 F1 期间保持不大改；后续按“执行/评分/复核/报告”拆分路由或 service |
| `backend/app/schemas.py` | 数据模型与接口模型集中 | 命名冲突/字段语义漂移风险增加 | P1 | 后续分模块管理 schemas，并补字段语义注释 |
| `backend/app/crud.py` | 方法数量较多，跨域混合 | 新人维护成本上升，误改概率提高 | P2 | 后续渐进拆分，不建议当前立刻动 |
| `backend/app/models.py` | 表结构清晰，新增表均独立 | 主要风险来自“无迁移工具”而非建模本身 | P1 | 暂不改结构；先建立手工迁移纪律和版本说明 |

## 5. Schema / Pydantic 风险

1. **Pydantic v2 保留字段风险已部分规避**：
- `PromptTestRunSummaryResponse` 使用 `model_config_info` + `alias="model_config"`，方向正确。

2. **alias 使用注意点（真实风险）**：
- 代码内部需持续使用 `model_config_info` 赋值；若后续新增代码误用 `model_config=`，可能再次触发保留名问题。

3. **Python 3.9 兼容性**：
- 未见 `A | None` 写法；`Optional[...]` 使用正常。
- 使用 `list[...]`（PEP 585）在 Python 3.9 可用。

4. **字段一致性风险**：
- detail/summary/report/compare 四条链路字段含义总体一致，但都依赖同一大 router 中的拼装逻辑，后续改动需同步回归。

## 6. 数据库与敏感信息风险

1. **api_key/token 保存风险**：
- 扫描未发现把 `api_key/token` 持久化到数据库。
- API key 通过环境变量读取，符合当前约束。

2. **敏感信息输出风险（中等）**：
- `raw_response` 会保存到 `prompt_score_results.raw_response` 与 `prompt_test_results.raw_response`；接口层已做“成功不返回、失败返回”控制，但数据库体量可能增长。

3. **数据库结构问题**：
- 新增表职责划分清晰（评分、复核、断言、输入快照独立）。

4. **无 Alembic 风险（真实）**：
- 当前 `Base.metadata.create_all` 只负责创建，不处理变更迁移。
- 后续升级若改字段/索引，存在环境不一致风险。

## 7. 接口一致性风险

重点检查 `detail/summary/report-markdown/compare`：

1. 一致性较好：
- `compare` 复用 `summary` 结果，避免重复统计口径。
- `report-markdown` 基于 `summary` 输出，指标来源一致。

2. 主要风险点：
- `prompt_test_runs.py` 存在中文字符串编码异常（源码内出现乱码文本），会导致部分 `manual_check_suggestion`/报告文案可读性下降，属于用户可见质量风险。
- 错误码大体统一（404/400），但不同端点 detail 文案细节不完全一致（可接受）。

## 8. 可测试性风险

1. Swagger 手工验证总体可行，关键链路可覆盖。
2. 风险点：
- 对 `run_id/result_id` 依赖较强，手工测试步骤顺序必须严格（先 run-once 或 run-repeat，再 score/review/compare）。
- 评分与模型调用依赖外部可用性，失败时要区分“平台逻辑问题”与“外部模型问题”。
- 重复执行会产生多条记录，若测试环境长期复用，容易出现数据污染与误取历史 ID。

建议：
- 每轮最小回归先创建“本轮专用 run”，避免复用旧 run。
- 用 `docs/backend-v0.6-regression-checklist.md` 固定顺序执行。

## 9. 后续建议清单

| 优先级 | 建议事项 | 原因 | 是否建议现在做 |
|---|---|---|---|
| P0 | 无 | 未发现必须立即修复且会阻断主链路的问题 | 否 |
| P1 | 修复 `prompt_test_runs.py` 中用户可见中文乱码文本 | 影响报告与建议信息可读性，属于质量风险 | 是（小修复可尽快做） |
| P1 | 将 summary/report/compare 聚合逻辑下沉到 service | 降低 router 复杂度与后续改动回归风险 | 否（前端 F1 后做） |
| P1 | 明确 `model_config` alias 使用规范并补注释 | 避免再次触发 Pydantic 保留字段问题 | 是（小改可做） |
| P2 | 合并两套断言逻辑（`assertions.py` / `assertion_evaluator.py`） | 减少重复维护成本 | 否 |
| P2 | 拆分 `schemas.py` / `crud.py` 按领域管理 | 结构更清晰，降低长期维护成本 | 否 |
| P2 | 制定无 Alembic 的手工迁移模板文档 | 降低多环境 schema 偏差风险 | 是（文档先行） |

## 10. 不建议现在处理的事项

1. 大范围拆分 router
2. 大范围改 schema
3. 立即引入 Alembic（涉及迁移链路与历史库适配，风险较高）
4. 引入新依赖
5. 重做接口返回结构
6. 删除历史能力代码（老 `test-targets/test-runs` 体系）

---

## 补充结论（是否立刻停下来修后端）

- **不建议立刻停下来大修后端**。
- 建议按“小步快跑”策略：
  1. 先进入前端 F1；
  2. 并行处理 1-2 个低风险小问题（如乱码文案）；
  3. 大的结构性优化放到后续稳定窗口。
