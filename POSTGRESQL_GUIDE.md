# PostgreSQL 使用教程

这份文档适用于当前 `manus-lite-lab` 仓库的本地开发环境，重点覆盖你这台 Mac 上通过 `Homebrew + postgresql@16` 使用 PostgreSQL 的实际路径。

当前项目的 Python 后端位于 `llm-python/`，默认数据库配置还是 SQLite，但后续为了接入更真实的业务数据和 RAG 相关元数据，推荐逐步切换到 PostgreSQL。

## 为什么这个项目要从 SQLite 转向 PostgreSQL

`SQLite` 很适合单机、轻量、快速起步，但它更像一个嵌入式数据库文件。随着项目进入以下场景，`PostgreSQL` 会更合适：

- 需要真实的数据库服务，而不是单个本地文件
- 需要更稳定的并发读写能力
- 需要更清晰的用户、权限、数据库隔离
- 后续准备接入 RAG 文档元数据、任务状态、检索日志等表结构
- 想让本地开发环境更接近真实部署环境

在这个项目里，后续可以把会话、消息、文档元数据、知识库管理数据都放进 PostgreSQL，而向量索引则交给 ChromaDB。

## 安装与验证

当前本机采用的是 `Homebrew + postgresql@16` 安装方式。

### 1. 安装 PostgreSQL

```bash
brew install postgresql@16
```

### 2. 确认安装路径

```bash
brew --prefix postgresql@16
```

当前机器上验证到的路径是：

```bash
/opt/homebrew/opt/postgresql@16
```

### 3. 验证核心命令存在

```bash
ls -la /opt/homebrew/opt/postgresql@16/bin
```

你应该能看到这些常用工具：

- `psql`
- `pg_isready`
- `createdb`
- `createuser`
- `pg_ctl`

### 4. 验证客户端版本

```bash
/opt/homebrew/opt/postgresql@16/bin/psql --version
```

当前机器上验证通过的输出示例：

```bash
psql (PostgreSQL) 16.13 (Homebrew)
```

### 5. 启动 PostgreSQL 服务

```bash
brew services start postgresql@16
```

### 6. 查看服务状态

如果机器上没有 `rg`，可以直接用 `grep`：

```bash
brew services list | grep postgres
```

正常情况下会看到类似：

```bash
postgresql@16 started
```

### 7. 验证数据库是否接受连接

```bash
/opt/homebrew/opt/postgresql@16/bin/pg_isready
```

验证通过时通常会看到：

```bash
/tmp:5432 - accepting connections
```

这说明 PostgreSQL 服务已经真正启动并监听本地连接。

## 服务管理

下面这些命令是本地开发时最常用的服务管理操作。

启动服务：

```bash
brew services start postgresql@16
```

停止服务：

```bash
brew services stop postgresql@16
```

重启服务：

```bash
brew services restart postgresql@16
```

查看服务状态：

```bash
brew services list | grep postgres
```

检查数据库是否活着：

```bash
/opt/homebrew/opt/postgresql@16/bin/pg_isready
```

## 连接数据库

最基础的连接方式是直接进入本机默认数据库：

```bash
/opt/homebrew/opt/postgresql@16/bin/psql postgres
```

进入后会看到类似：

```sql
postgres=#
```

退出命令：

```sql
\q
```

### 初次连接建议执行的检查语句

```sql
select version();
select current_user;
select 1;
```

当前机器上实际验证过的结果是：

- PostgreSQL 版本：`PostgreSQL 16.13 (Homebrew)`
- 当前用户：`cong`
- `select 1;` 成功返回 `1`

## 常用 SQL / psql 命令

这部分适合平时快速查库和排错。

查看 PostgreSQL 版本：

```sql
select version();
```

查看当前登录用户：

```sql
select current_user;
```

查看当前数据库：

```sql
select current_database();
```

测试 SQL 是否正常执行：

```sql
select 1;
```

查看所有数据库：

```sql
\l
```

查看所有用户 / 角色：

```sql
\du
```

查看当前数据库中的表：

```sql
\dt
```

查看表结构：

```sql
\d 表名
```

切换数据库：

```sql
\c 数据库名
```

退出：

```sql
\q
```

## 用户、数据库、密码分别是什么

这是初学 PostgreSQL 时最容易混淆的三件事。

- 用户：谁在登录数据库
- 密码：这个用户登录时使用的认证信息
- 数据库：真正存放表和数据的地方

可以把它理解成：

- 用户像“账号”
- 密码像“登录凭证”
- 数据库像“这个账号要进入的工作空间”

举个和当前项目相关的例子：

- 用户：`manus`
- 密码：你自己设置的本地开发密码
- 数据库：`manus_rag_demo`

## 为项目创建独立用户和数据库

不建议一直直接使用默认用户 `cong` 做项目开发。更推荐的方式是为项目单独创建一个数据库用户和数据库，这样更清晰，也更接近真实环境。

本项目推荐使用：

- 用户名：`manus`
- 数据库名：`manus_rag_demo`

### 1. 进入 PostgreSQL

```bash
/opt/homebrew/opt/postgresql@16/bin/psql postgres
```

### 2. 创建项目用户

下面示例中的密码请替换成你自己的本地开发密码：

```sql
create user manus with password 'manus123456';
```

### 3. 创建项目数据库

```sql
create database manus_rag_demo owner manus;
```

### 4. 授权

```sql
grant all privileges on database manus_rag_demo to manus;
```

### 5. 验证用户和数据库是否创建成功

```sql
\du
\l
```

### 6. 用项目用户测试连接

将下面命令中的密码替换为你实际设置的密码：

```bash
PGPASSWORD='manus123456' /opt/homebrew/opt/postgresql@16/bin/psql -U manus -d manus_rag_demo -h localhost
```

连接成功后，建议执行：

```sql
select current_user;
select current_database();
select 1;
```

理想结果应该分别是：

- 当前用户：`manus`
- 当前数据库：`manus_rag_demo`
- SQL 返回：`1`

## 项目中的 DB_URL 写法

当前 `llm-python` 项目后续如果切换到 PostgreSQL，推荐连接串格式如下：

```bash
postgresql+asyncpg://用户名:密码@localhost:5432/数据库名
```

结合上面的示例，项目里可以写成：

```bash
postgresql+asyncpg://manus:manus123456@localhost:5432/manus_rag_demo
```

如果后面要写进 `.env`，可以整理成：

```bash
DB_URL=postgresql+asyncpg://manus:manus123456@localhost:5432/manus_rag_demo
```

## 常见问题排查

### 1. `psql: command not found`

说明 PostgreSQL 已安装但命令没有进当前 shell 的 `PATH`，或者还没安装成功。

优先用绝对路径验证：

```bash
/opt/homebrew/opt/postgresql@16/bin/psql --version
```

如果这条能通，说明 PostgreSQL 已经装好了，只是 PATH 还没配置。

### 2. 服务未启动

如果连接时报数据库不可用，先执行：

```bash
brew services list | grep postgres
/opt/homebrew/opt/postgresql@16/bin/pg_isready
```

如果没有 `started` 或没有 `accepting connections`，就先启动服务：

```bash
brew services start postgresql@16
```

### 3. `password authentication failed`

说明用户存在，但密码不对。

排查顺序：

- 确认你连接时使用的是正确用户
- 确认 `PGPASSWORD` 使用的是创建用户时设置的密码
- 如果忘记密码，重新登录管理员账号后执行 `alter user ... with password ...`

### 4. `database does not exist`

说明你要连接的数据库名不存在。

先进入 PostgreSQL 后查看：

```sql
\l
```

确认目标数据库是否已经创建，例如 `manus_rag_demo`。

### 5. `role does not exist`

说明要连接的数据库用户还没有创建。

先进入 PostgreSQL 后查看：

```sql
\du
```

如果没有目标用户，就执行：

```sql
create user manus with password '你的密码';
```

### 6. 为什么 `pg_isready` 里显示的是 `/tmp:5432`

这是 PostgreSQL 在本机 Unix socket 上响应的表现，属于正常现象。

对 Python 项目配置来说，通常仍然建议写：

```bash
localhost:5432
```

因为这更直观，也更符合后续迁移到远程数据库时的连接方式。

### 7. 为什么当前项目里还有 SQLite

当前代码里默认数据库配置仍然是 SQLite，这是已有实现的现状。PostgreSQL 这份文档的目的，是为后续把 `llm-python` 切换到真实数据库做准备。

后续真正改代码时，需要同步更新：

- `llm-python/app/core/config.py`
- `llm-python/app/db/session.py`
- `.env` 中的 `DB_URL`

---
Last updated from hands-on setup on 2026-03-18
