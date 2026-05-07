# deploy 启动脚本说明

本目录用于本地开发环境启动，不包含业务代码修改。

## 脚本列表

- `start-backend.bat`
  - 进入 `backend/` 目录。
  - 检查 `.venv` 是否存在（具体为 `.venv\Scripts\python.exe`）。
  - 若不存在，仅提示先按项目 README 创建虚拟环境并安装依赖，不会自动安装。
  - 若存在，使用以下命令启动后端：
    - `..venv\Scripts\python.exe -m uvicorn app.main:app --reload`

- `start-frontend.bat`
  - 进入 `frontend/` 目录。
  - 检查 `node_modules/` 是否存在。
  - 若不存在，仅提示先执行 `npm install`，不会自动安装。
  - 若存在，使用以下命令启动前端：
    - `npm run dev`

- `start-dev.bat`
  - 一键启动开发环境。
  - 会打开两个新的 `cmd` 窗口：
    - 一个运行 `start-backend.bat`
    - 一个运行 `start-frontend.bat`
  - 当前窗口会输出：
    - 后端地址：`http://127.0.0.1:8000/docs`
    - 前端地址：`http://127.0.0.1:5173`

## 首次使用前

请先完成依赖安装（手动执行）：

1. 后端：按项目 README 在 `backend/` 下创建 `.venv` 并安装依赖
2. 前端：在 `frontend/` 下执行 `npm install`

脚本不会自动安装依赖。

## 日常启动建议

推荐直接运行：

- `start-dev.bat`
