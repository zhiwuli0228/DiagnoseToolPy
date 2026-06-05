# DiagnoseToolPy 性能优化设计文档

## 一、压测结果摘要

| 指标 | 实测值 | 阈值 | 状态 |
|------|--------|------|------|
| 错误率 | 0% | <5% | ✅ 通过 |
| 平均响应时间 | 881ms | <3000ms | ✅ 通过 |
| P95响应时间 | 1495ms | <6000ms | ✅ 通过 |
| 吞吐量 | 5.47 req/s | >10 req/s | ❌ 未达标 |

## 二、问题分析

### 2.1 吞吐量瓶颈分析

当前吞吐量 `5.47 req/s` 未达到预期 `10 req/s`，主要原因：

1. **首屏加载慢** - React应用未做代码分割，所有路由组件打包在一起
2. **重复资源请求** - 每次页面切换都会重新请求相同的API
3. **无缓存机制** - 案例数据每次都从文件系统重新加载
4. **后端无缓存** - BM25索引每次查询都重新构建

### 2.2 各页面性能分析

| 页面 | 平均响应 | P95 | 优化优先级 |
|------|----------|-----|------------|
| Dashboard | 1034ms | 1495ms | 中 |
| Analysis | 819ms | 934ms | 低 |
| Cases | 811ms | 860ms | 高 |
| Settings | 862ms | 967ms | 中 |

**Cases页面优化优先级最高**，因为案例浏览是高频操作。

## 三、优化方案

### 3.1 前端优化

#### 方案A: React Router 懒加载 (实现难度: 低)

**目标**: 将路由组件拆分为独立chunk，实现按需加载

**实现方式**:
```typescript
// App.tsx
const AnalysisTasksPage = lazy(() => import('./pages/AnalysisTasksPage'));
const CasebasePage = lazy(() => import('./pages/CasebasePage'));
const AIDiagnosisPage = lazy(() => import('./pages/AIDiagnosisPage'));

// 使用 <Suspense> 包装
<Suspense fallback={<Spin />}>
  <Routes>...</Routes>
</Suspense>
```

**预期效果**: 首次加载时间减少 30-50%

#### 方案B: API响应缓存 (实现难度: 中)

**目标**: 减少重复API请求

**实现方式**:
- 使用 React Query / SWR 进行数据缓存
- 案例列表缓存 5 分钟
- 案例详情缓存 10 分钟

```typescript
// 使用 useSWR
const { data } = useSWR('/api/cases', fetcher, {
  revalidateOnFocus: false,
  dedupingInterval: 60000, // 1分钟内不重复请求
});
```

#### 方案C: 前端资源压缩 (实现难度: 低)

**目标**: 减少资源传输体积

**实现方式**:
- 启用 Vite build.minify = 'terser'
- 开启 gzip/brotli 压缩
- 图片资源压缩

**配置**:
```typescript
// vite.config.ts
build: {
  minify: 'terser',
  rollupOptions: {
    compress: {
      gzip: true,
      brotli: true,
    }
  }
}
```

### 3.2 后端优化

#### 方案D: 案例数据缓存 (实现难度: 中)

**目标**: 避免重复从文件系统加载案例

**实现方式**:
```python
# case_service.py
from functools import lru_cache
from typing import Optional

@lru_cache(maxsize=128)
def get_case_index() -> List[CaseSummary]:
    """缓存案例索引，5分钟过期"""
    # 原有加载逻辑
    pass

# 定时刷新缓存
def invalidate_case_cache():
    get_case_index.cache_clear()
```

#### 方案E: BM25索引预加载 (实现难度: 中)

**目标**: 避免每次查询重新构建BM25索引

**实现方式**:
```python
# bm25_search.py
class BM25Cache:
    _instance = None
    _index = None
    _last_build = 0
    BUILD_INTERVAL = 300  # 5分钟

    @classmethod
    def get_index(cls):
        now = time.time()
        if cls._index is None or (now - cls._last_build) > cls.BUILD_INTERVAL:
            cls._index = build_bm25_index()
            cls._last_build = now
        return cls._index
```

#### 方案F: API响应压缩 (实现难度: 低)

**目标**: 减少网络传输量

**实现方式**:
```python
# main.py
from fastapi.middleware.gzip import GZIPMiddleware

app.add_middleware(GZIPMiddleware, minimum_size=1000)
```

## 四、优化优先级与实施计划

| 优先级 | 方案 | 工作量 | 预期收益 | 风险 |
|--------|------|--------|----------|------|
| P0 | 方案F: GZIP压缩 | 0.5天 | 吞吐量 +20% | 低 |
| P0 | 方案A: 路由懒加载 | 1天 | 首屏 -40% | 低 |
| P1 | 方案E: BM25缓存 | 1天 | 案例搜索 -60% | 低 |
| P1 | 方案D: 案例缓存 | 1天 | 案例列表 -50% | 低 |
| P2 | 方案B: API缓存 | 1天 | 重复访问 -70% | 中 |
| P2 | 方案C: 资源压缩 | 0.5天 | 加载 -15% | 低 |

## 五、推荐实施方案

建议分两阶段实施：

### 第一阶段 (P0紧急优化，1.5天)

1. 启用GZIP压缩 (方案F)
2. 实现路由懒加载 (方案A)

### 第二阶段 (P1性能提升，2天)

1. 实现BM25索引缓存 (方案E)
2. 实现案例数据缓存 (方案D)

### 第三阶段 (P2体验优化，1.5天)

1. 实现API客户端缓存 (方案B)
2. 资源压缩优化 (方案C)

## 六、验收标准

优化完成后，重新压测应达到：

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| 吞吐量 | 5.47 req/s | >10 req/s |
| 首屏加载 | ~1000ms | <600ms |
| 案例列表 | 811ms | <400ms |
| 错误率 | 0% | 0% |

## 七、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 缓存导致数据不一致 | 中 | 设置合理过期时间，提供手动刷新 |
| 懒加载增加HTTP请求数 | 低 | 合理拆分，控制chunk数量 |
| 压缩增加CPU负载 | 低 | 仅对大响应启用压缩 |
