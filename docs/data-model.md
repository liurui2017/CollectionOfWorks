# 数据模型设计（PostgreSQL + Pydantic 契约源）

> 本文档是**开发的起点与唯一事实来源**。后端 Pydantic 模型按此实现，FastAPI 自动生成 OpenAPI，
> 前端通过 `openapi-typescript` 生成 TypeScript 类型，从而保证前后端字段永久一致。

---

## 1. 枚举定义

后端以 `str, Enum` 定义，序列化后为字符串，前端直接用生成类型联合。

| 枚举 | 取值 | 说明 |
| --- | --- | --- |
| `WorkType` | `video` / `article` / `note` / `gallery` | 短视频 / Markdown 文章 / 纯文本短文 / 图集 |
| `WorkStatus` | `draft` / `published` | 草稿 / 已发布 |
| `MediaKind` | `image` / `video` | 媒体种类 |
| `MediaRole` | `cover` / `video` / `gallery` | 媒体在作品中的用途 |

---

## 2. 表结构

### 2.1 `users` — 管理员

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | 登录名 |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt 哈希，禁止明文 |
| `last_login_at` | TIMESTAMPTZ | NULL | 最近登录时间 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

说明：单管理员设计。首次启动通过环境变量 `ADMIN_USERNAME` / `ADMIN_PASSWORD` 初始化一条记录（幂等，已存在则跳过）。

### 2.2 `categories` — 分类（一对一挂在作品上）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | 展示名 |
| `slug` | VARCHAR(50) | UNIQUE, NOT NULL | URL 用，如 `short-film` |
| `description` | VARCHAR(200) | NULL | |
| `sort_order` | INTEGER | NOT NULL, DEFAULT 0 | 数值越大越靠前 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

删除策略：分类被删除时，作品 `category_id` 置空（`ON DELETE SET NULL`），不连带删除作品。

### 2.3 `tags` — 标签（多对多）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | 展示名（不带 `#`） |
| `slug` | VARCHAR(50) | UNIQUE, NOT NULL | URL 用 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

### 2.4 `works` — 作品主表

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | |
| `title` | VARCHAR(200) | NOT NULL | 标题 |
| `slug` | VARCHAR(200) | UNIQUE, NOT NULL | 前台 URL：`/works/{slug}` |
| `type` | VARCHAR(16) | NOT NULL | `WorkType` |
| `summary` | VARCHAR(300) | NULL | 列表卡片与分享摘要 |
| `content` | TEXT | NULL | Markdown 或纯文本正文；`video`/`gallery` 类型可为空 |
| `status` | VARCHAR(16) | NOT NULL, DEFAULT `draft` | `WorkStatus` |
| `category_id` | BIGINT | FK `categories(id)` NULL, ON DELETE SET NULL | 单选分类 |
| `is_featured` | BOOLEAN | NOT NULL, DEFAULT false | 首页精选 |
| `sort_order` | INTEGER | NOT NULL, DEFAULT 0 | 数值越大越靠前，相同按 `published_at` 倒序 |
| `view_count` | INTEGER | NOT NULL, DEFAULT 0 | 详情页访问自增 |
| `published_at` | TIMESTAMPTZ | NULL | 草稿为 NULL；首次发布自动写入 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

索引：

```sql
CREATE UNIQUE INDEX uq_works_slug       ON works (slug);
CREATE        INDEX idx_works_feed      ON works (status, published_at DESC);
CREATE        INDEX idx_works_featured  ON works (is_featured, sort_order DESC) WHERE status = 'published';
CREATE        INDEX idx_works_category  ON works (category_id);
CREATE        INDEX idx_works_type      ON works (type);
```

前台查询恒带 `status = 'published'`，草稿永不出现在公开接口。

### 2.5 `media` — 媒体资源表（本地上传的视频与图片）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | |
| `kind` | VARCHAR(8) | NOT NULL | `MediaKind` |
| `filename` | VARCHAR(255) | UNIQUE, NOT NULL | 落盘文件名（UUID + 扩展名，避免中文/重名） |
| `original_name` | VARCHAR(255) | NOT NULL | 用户上传时的原始文件名 |
| `url` | VARCHAR(500) | NOT NULL | 访问路径，如 `/media/2026/09/ab12.mp4` |
| `mime_type` | VARCHAR(100) | NOT NULL | |
| `size_bytes` | BIGINT | NOT NULL | |
| `width` | INTEGER | NULL | 图片/视频宽度，后端解析 |
| `height` | INTEGER | NULL | 图片/视频高度，后端解析 |
| `duration_seconds` | NUMERIC(8,2) | NULL | 仅视频，后端解析后写入 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

存储约定：

- 磁盘目录：`MEDIA_ROOT`（默认 `./media`），按 `YYYY/MM/` 分目录。
- 访问方式：FastAPI `StaticFiles` 挂载在 `/media`，生产环境建议再由 Nginx 直接托管静态文件。
- 上传限制：图片 ≤ 10MB；视频 ≤ 2GB；白名单 MIME（jpg/png/webp/gif、mp4/mov/webm）。

### 2.6 `work_media` — 作品与媒体的关联（含用途与排序）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | |
| `work_id` | BIGINT | FK `works(id)` ON DELETE CASCADE, NOT NULL | |
| `media_id` | BIGINT | FK `media(id)` ON DELETE CASCADE, NOT NULL | |
| `role` | VARCHAR(16) | NOT NULL | `cover` / `video` / `gallery` |
| `sort_order` | INTEGER | NOT NULL, DEFAULT 0 | 图集排序；第一张即封面 |

约束与规则：

```sql
UNIQUE (work_id, media_id, role)
```

- 每个作品最多一条 `role = 'cover'`；每个 `video` 类型作品恰好一条 `role = 'video'`。
- `gallery` 类型作品的图片均为 `role = 'gallery'`，`sort_order` 决定展示顺序。

### 2.7 `work_tags` — 作品与标签多对多

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `work_id` | BIGINT | FK `works(id)` ON DELETE CASCADE |
| `tag_id` | BIGINT | FK `tags(id)` ON DELETE CASCADE |
| | | PRIMARY KEY (`work_id`, `tag_id`) |

---

## 3. 关系总览

```
users         （独立，仅鉴权）

categories 1 ──< works >── N tags
                   │            （via work_tags）
                   └──< work_media >── media
```

---

## 4. API 出参模型（Pydantic → OpenAPI → TS）

后端 `app/schemas/` 下的模型即为契约，字段命名统一 `snake_case`，时间统一 ISO 8601 带时区字符串。

### 4.1 媒体

```python
class MediaOut(BaseModel):
    id: int
    kind: MediaKind
    url: str
    original_name: str
    mime_type: str
    size_bytes: int
    width: int | None
    height: int | None
    duration_seconds: float | None
```

### 4.2 分类 / 标签

```python
class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    sort_order: int
    work_count: int          # 该分类下已发布作品数（聚合字段）

class TagOut(BaseModel):
    id: int
    name: str
    slug: str
    work_count: int
```

### 4.3 作品：列表项 / 详情 / 写入

```python
class WorkListItem(BaseModel):        # 列表卡片用，不含正文
    id: int
    title: str
    slug: str
    type: WorkType
    summary: str | None
    cover: MediaOut | None
    category: CategoryRef | None      # {id, name, slug}
    tags: list[TagRef]                # {id, name, slug}
    is_featured: bool
    view_count: int
    published_at: datetime | None

class WorkDetail(WorkListItem):        # 详情页用
    content: str | None                # article / note 才有值
    video: MediaOut | None             # video 类型才有值
    images: list[MediaOut]             # gallery 类型才有值
    status: WorkStatus                 # 后台可见，前台接口不返回

# 写入：创建与更新共用字段定义，更新为全量 PUT
class WorkCreate(BaseModel):
    title: str
    slug: str
    type: WorkType
    summary: str | None = None
    content: str | None = None
    category_id: int | None = None
    tag_ids: list[int] = []
    cover_media_id: int | None = None
    video_media_id: int | None = None
    gallery_media_ids: list[int] = []
    is_featured: bool = False
    status: WorkStatus = WorkStatus.draft
    sort_order: int = 0
    published_at: datetime | None = None

class WorkUpdate(WorkCreate): ...
```

### 4.4 通用包装

```python
class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int

class Paginated[T](BaseModel):        # FastAPI 泛型
    items: list[T]
    meta: PageMeta

class ErrorOut(BaseModel):            # 统一错误体
    detail: str
```

### 4.5 鉴权

```python
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int                    # 秒

class AdminUserOut(BaseModel):
    id: int
    username: str
    last_login_at: datetime | None
```

---

## 5. 约定与注意事项

1. **命名**：接口字段一律 `snake_case`；前端如需驼峰，只在 API 层做映射，不改变生成类型。
2. **时间**：全部 ISO 8601 字符串（如 `2026-09-12T20:00:00+08:00`），前端统一用 `dayjs`/`date-fns` 格式化。
3. **空值**：可空字段明确标注 `| None` / `NULL`，前端生成类型为 `X | null`，避免 `undefined` 与 `null` 混用。
4. **枚举**：前端展示文案（如 `video` → 「短视频」）写成一张常量映射表，不用枚举值直接展示。
5. **聚合字段**：`work_count`、`view_count` 属派生数据，只读，写入接口忽略。
6. **视频派生信息**：`duration_seconds` / `width` / `height` 由后端上传时解析（ffprobe），前端只读展示。

---

## 6. 待你确认的开放项

| # | 问题 | 当前默认方案 |
| --- | --- | --- |
| 1 | 首页「关于我」内容是否需要后台可编辑？你之前未选「站点设置」模块 | 暂**硬编码在前端**；若需可编辑，则新增单行表 `site_profile`（nickname/avatar/about/social_links） |
| 2 | 作品浏览量是否需要统计与展示？ | 仅做详情页 `view_count` 自增，不做访问来源/趋势报表 |
| 3 | 搜索实现方式 | v1 用 `ILIKE '%q%'` 匹配 `title`/`summary`/`content`；数据量增长后再升级 `tsvector` + `pg_trgm` |
| 4 | 视频是否需要自动生成封面缩略图或转码？ | v1 **不做**，封面由你手动上传；不引入 ffmpeg，仅用 ffprobe 读时长/分辨率 |
| 5 | 是否需要 RSS / sitemap.xml（SEO） | v1 不做，后续可加 |
| 6 | 是否需要定时发布（未来时间自动转已发布） | v1 不做，`published_at` 仅作展示字段 |
