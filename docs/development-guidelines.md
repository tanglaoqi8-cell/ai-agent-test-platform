# 开发约束文档

## 1. 项目定位

本项目是一个本地部署的通用 AI 测试评估平台，支持 Prompt、Agent、RAG 的测试对象管理、用例上传、测试执行、结果查看和报告导出。

后续功能要保持易扩展，不能为了某个单独场景把逻辑写死。

## 2. 前端开发约束

前端代码只允许放在 frontend/ 目录。

规则：

- 页面放在 frontend/src/views/
- 接口封装放在 frontend/src/api/
- 路由放在 frontend/src/router/
- 页面不要直接写死后端地址
- 统一使用 /api 调用后端接口
- 不要把复杂业务逻辑全部写在页面组件里

后续如果增加登录注册，建议新增：

- frontend/src/views/Login.vue
- frontend/src/views/Register.vue
- frontend/src/api/auth.js

不要把登录逻辑混进测试执行页面。

## 3. 后端开发约束

后端代码只允许放在 backend/ 目录。

规则：

- 接口路由放在 backend/app/routers/
- 复杂业务逻辑放在 backend/app/services/
- 数据库模型放在 backend/app/models.py
- 请求和响应结构放在 backend/app/schemas.py
- 不要随意修改已验证通过的接口路径
- 不要随意修改数据库结构

后续如果增加登录注册，建议新增：

- backend/app/routers/auth.py
- backend/app/routers/users.py
- backend/app/services/auth_service.py

不要把登录逻辑混进测试对象、用例、执行结果模块里。

## 4. 测试对象扩展规则

当前测试对象类型包括：

- prompt
- agent_http
- rag_http

后续如果增加新类型，例如：

- model_http
- workflow_agent
- multi_turn_agent

应优先扩展 runner，不要复制一套新的执行流程。

## 5. 禁止事项

后续开发禁止：

1. 禁止随意修改已验证接口路径
2. 禁止把后端地址写死到前端页面
3. 禁止一次性大范围重构
4. 禁止新增依赖但不说明原因
5. 禁止把某个具体 Prompt、Agent、RAG 业务写死
6. 禁止修改非任务指定目录
7. 禁止破坏当前可运行版本

## 6. Codex 开发要求

每次给 Codex 派任务时，必须说明：

1. 允许修改哪些文件
2. 禁止修改哪些文件
3. 是否允许新增依赖
4. 是否允许改数据库
5. 是否允许改接口路径
6. 完成后必须返回修改文件列表和验证步骤

## 7. 当前稳定版本

当前已完成：

- v0.1：前后端可运行、Mock 执行、一键启动
- v0.2：真实 HTTP Runner，支持 Agent/RAG GET/POST
- v0.3：测试结果 CSV 导出

后续开发原则：

先小改，再验证，再备份。