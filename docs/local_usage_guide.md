# 本地自用说明

## 1. 第一次使用

1. 安装依赖：`python -m pip install -r requirements.txt`
2. 复制配置文件：把 `config/user_config.example.json` 复制为 `config/user_config.json`
3. 填写模型 API 配置：API Key、Base URL、模型名
4. 填写 Zotero 配置：Library ID、Library Type、API Key
5. 填写 Obsidian Vault Path：填写你的 Obsidian 仓库根目录
6. 启动应用：运行 `streamlit run app.py` 或双击 `start_app.bat`

## 2. 配置文件说明

`config/user_config.example.json` 是可提交的示例配置，不应写入真实密钥。

`config/user_config.json` 是你的本地私人配置，包含 API Key、Zotero Key 和 Obsidian 路径，已被 `.gitignore` 排除，不要提交。

## 3. Obsidian 配置

`obsidian_vault_path` 填写 Obsidian Vault 的根目录，例如 `D:\Notes\MyVault`。

应用会自动创建：

- `AI-Literature-Agent/Inbox/`
- `AI-Literature-Agent/Analyzed/`
- `AI-Literature-Agent/Logs/`

新生成的论文笔记默认写入 `AI-Literature-Agent/Inbox/`。如果同名笔记已存在，系统会自动追加时间戳，不会覆盖旧文件。

## 4. Zotero 配置

需要填写：

- `zotero_library_id`
- `zotero_library_type`：通常是 `user`，团队库可用 `group`
- `zotero_api_key`

如果 Zotero 未配置，应用仍可检索、评分并生成本地 Obsidian 笔记。

## 5. 模型 API 配置

需要填写：

- `openai_api_key`
- `openai_base_url`
- `openai_model`

如果模型 API Key 缺失或模型调用失败，系统会降级为启发式评分，并在页面中提示。

## 6. 启动方式

命令行启动：

```powershell
streamlit run app.py
```

双击启动：

```powershell
start_app.bat
```

`start_app.bat` 会进入项目目录，优先使用 `.venv`，如果 `.venv` 不存在则使用当前 Python 环境。

## 7. 常见问题

页面能打开但不能写入 Obsidian：检查 `obsidian_vault_path` 是否为空或路径不存在。

Zotero 连接失败：检查 Library ID、Library Type、API Key，以及 API Key 是否有写入权限。

模型 API 失败：检查 API Key、Base URL、模型名和网络连接；失败时系统会使用启发式评分。

使用了启发式评分：说明模型 API 未配置或调用失败，结果只作为初筛参考。

生成了 mock 数据：说明 arXiv 检索失败或无结果，mock 数据不是真实论文。

配置文件不存在：复制 `config/user_config.example.json` 为 `config/user_config.json`，再填写个人配置。
