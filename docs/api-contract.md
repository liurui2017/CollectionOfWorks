# API 契约与前后端一致化方案

配套阅读：[data-model.md](./data-model.md)（表结构与 Pydantic 模型定义）

---

## 1. 契约单一事实来源

```
backend/app/schemas/*.py   （Pydantic v2 模型）
        │
        ▼  FastAPI 启动时自动导出的 /openapi.json
        │
        ▼  openapi-typescript（npm script，一键生成）
        │
frontend/src/api/schema.d.ts   （自动生成，禁止手改）
        │
        ▼
frontend/src/api/client.ts     （薄封装：带 baseURL / JWT / 错误处理）
```

约定：

1. 后端改动了 `schemas` 或路由，即视为契约变更，提交前必须重新生成前端类型。
2. 生成产物 `schema.d.ts` **纳入版本管理**，并在前端 CI 中校验「重新生成后无 diff」，防止契约漂移。
3. 前端**禁止**手写与后端接口重复的 `interface`，一律引用 `components['schemas'][...]`。

生成命令（写入 `frontend/package.json`）：

```json
{
  "scripts": {
    "gen:api": "openapi-typescript http://localhost:8000/openapi.json -o src/api/schema.d.ts"
  }
}
```

前端引用方式：

```ts
import type { components } from '@/api/schema';

type WorkListItem = components['schemas']['WorkListItem'];
type WorkType = components['schemas']['WorkType'];   // 'video' | 'article' | 'note' | 'gallery'
```

---

## 2. 接口清单

统一前缀 `/api/v1`，媒体文件走 `/media` 静态路由。除登录外，`/admin/**` 全部要求
`Authorization: Bearer <access_token>`。

### 2.1 公开接口（前台，只返回 `published` 数据）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/works` | 作品列表。参数：`type`、`category`（slug）、`tag`（slug）、`q`（关键词）、`featured`、`sort`（`latest`/`oldest`/`views`）、`page`、`page_size` → `Paginated[WorkListItem]` |
| GET | `/api/v1/works/{slug}` | 作品详情 → `WorkDetail`；不存在或非 published 返回 404；命中成功时 `view_count` 自增 |
| GET | `/api/v1/categories` | 分类列表 → `list[CategoryOut]` |
| GET | `/api/v1/tags` | 标签列表（可按 `limit` 取热门）→ `list[TagOut]` |
| GET | `/media/{path}` | 静态媒体文件（视频/图片） |

### 2.2 鉴权

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/auth/login` | 入参 `LoginRequest`，出参 `TokenOut`；失败返回 401，同一 IP 连续失败做简单限流 |
| GET | `/api/v1/auth/me` | 当前管理员信息 → `AdminUserOut` |

Token 策略：JWT（HS256），`exp` 默认 24 小时；密钥来自环境变量 `JWT_SECRET`。前端存 `localStorage`，
请求拦截器注入 Header，收到 401 时清除 token 并跳回登录页。

### 2.3 管理接口（后台）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/admin/works` | 管理列表，可带 `status`/`type`/`category_id`/`q`，返回含草稿的 `Paginated[WorkListItem]` |
| POST | `/api/v1/admin/works` | 新建 → 入参 `WorkCreate`，出参 `WorkDetail` |
| GET | `/api/v1/admin/works/{id}` | 回填编辑表单 → `WorkDetail` |
| PUT | `/api/v1/admin/works/{id}` | 全量更新 → 入参 `WorkCreate`（`slug` 冲突返回 409） |
| DELETE | `/api/v1/admin/works/{id}` | 删除作品（关联 `work_media`/`work_tags` 级联清理，媒体文件保留在库中） |
| POST | `/api/v1/admin/works/{id}/publish` | 转已发布，`published_at` 为空则写入当前时间 |
| POST | `/api/v1/admin/works/{id}/unpublish` | 转草稿 |
| POST | `/api/v1/admin/media` | `multipart/form-data` 上传单个文件 → `MediaOut`（视频用后台任务解析时长/分辨率） |
| DELETE | `/api/v1/admin/media/{id}` | 从媒体库删除（若被作品引用返回 409） |
| GET/POST/PUT/DELETE | `/api/v1/admin/categories` | 分类增删改查（POST 入参 `{name, slug, description, sort_order}`） |
| GET/POST/PUT/DELETE | `/api/v1/admin/tags` | 标签增删改查 |

请求/响应示例：

```http
GET /api/v1/works?type=video&category=short-film&q=city&page=1&page_size=12
```

```json
{
  "items": [
    {
      "id": 1,
      "title": "夜行：城市的另一面",
      "slug": "night-city",
      "type": "video",
      "summary": "凌晨两点到四点的城市，霓虹、雨水与空无一人的街道。",
      "cover": { "id": 3, "kind": "image", "url": "/media/2026/09/ab12.jpg",
                 "original_name": "cover.jpg", "mime_type": "image/jpeg",
                 "size_bytes": 421233, "width": 1920, "height": 1080, "duration_seconds": null },
      "category": { "id": 1, "name": "短片", "slug": "short-film" },
      "tags": [{ "id": 2, "name": "夜景", "slug": "night" }],
      "is_featured": true,
      "view_count": 1243,
      "published_at": "2026-09-12T20:00:00+08:00"
    }
  ],
  "meta": { "page": 1, "page_size": 12, "total": 16, "total_pages": 2 }
}
```

---

## 3. 错误码约定

| 状态码 | 场景 |
| --- | --- |
| 400 | 入参校验失败（FastAPI `RequestValidationError`，`detail` 为字段错误数组） |
| 401 | 未登录 / token 失效 / 密码错误 |
| 403 | 已登录但无权限（预留，未来多角色时使用） |
| 404 | 资源不存在（含未发布作品对外访问） |
| 409 | 资源冲突（slug 重复、删除仍被引用的媒体） |
| 413 | 上传文件超出大小限制 |
| 415 | 上传 MIME 类型不在白名单 |
| 500 | 服务端异常 |

前端统一在 `client.ts` 中拦截非 2xx，抛出带 `status` 与 `detail` 的错误对象。

---

## 4. 项目结构（拟）

```
workspace/
├─ backend/
│  ├─ app/
│  │  ├─ main.py                 # FastAPI 实例 + CORS + StaticFiles
│  │  ├─ core/                   # config / security(JWT) / db(session)
│  │  ├─ models/                 # SQLAlchemy ORM（对应 data-model.md 各表）
│  │  ├─ schemas/                # Pydantic（契约源）★
│  │  ├─ api/v1/                 # works / auth / admin / categories / tags
│  │  └─ services/               # 业务逻辑 + 媒体上传解析
│  ├─ alembic/                   # 数据库迁移
│  └─ pyproject.toml
├─ frontend/
│  ├─ src/
│  │  ├─ api/schema.d.ts         # openapi-typescript 生成 ★
│  │  ├─ api/client.ts
│  │  ├─ pages/                  # 前台 5 页 + 后台 4 页
│  │  ├─ components/
│  │  └─ styles/                 # 直接复用原型 assets/style.css 的设计 token
│  └─ package.json
├─ docker-compose.yml            # postgres + backend + frontend(nginx)
├─ docs/
│  ├─ data-model.md
│  └─ api-contract.md
└─ prototype/                    # 本设计稿（评审通过后可保留作为视觉基线）
```

---

## 5. 开发顺序（契约优先）

1. 后端 `models` + `schemas` 落地 → 起服务 → `/docs` 人工核对接口形状。
2. 前端 `npm run gen:api` 生成类型 → 用假数据（MSW）跑通页面。
3. 后端补 service 与真实接口 → 前端切真实数据。
4. 鉴权链路（登录 → 存 token → 拦截器 → 401 跳转）单独验证。
5. 上传链路（大文件上传、进度、失败重试）单独验证。
6. Docker 打包与部署验证。
