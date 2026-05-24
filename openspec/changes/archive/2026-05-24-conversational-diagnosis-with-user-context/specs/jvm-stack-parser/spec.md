# Spec: jvm-stack-parser

## Spec ID

`jvm-stack-parser`

## Change ID

`conversational-diagnosis-with-user-context`

## Overview

JVM 堆栈解析与精简能力。识别重复帧、合并相同包前缀、精简过长堆栈。

---

## ADDED Requirements

### Requirement: 堆栈格式识别

系统 SHALL 识别标准 JVM 堆栈格式。支持的格式包括：
- Oracle/Sun HotSpot
- OpenJDK
- 常见框架（Spring、MyBatis、Dubbo 等）

#### Scenario: 标准 HotSpot 格式
- **WHEN** 输入包含 `at com.demo.OrderService.query(OrderService.java:42)`
- **THEN** 系统正确解析出 class、method、file、line

#### Scenario: Spring 框架格式
- **WHEN** 输入包含 `at org.springframework.web.servlet.DispatcherServlet.doDispatch(DispatcherServlet.java:1055)`
- **THEN** 系统正确解析

### Requirement: 重复帧检测与合并

当堆栈中存在连续重复的帧（如循环内的重复调用）时，系统 SHALL 合并这些帧并标注重复次数。

#### Scenario: 检测循环导致的重复帧
- **WHEN** 堆栈中出现连续 5 次相同的帧
- **THEN** 系统合并为一行：`...（重复 5 次）`

### Requirement: 同包前缀合并

当堆栈中存在相同包前缀的连续帧时，系统 SHALL 合并显示。

#### Scenario: 同包连续帧合并
- **WHEN** 堆栈中连续 3 帧都是 `com.demo.service.` 包下
- **THEN** 系统合并显示：`com.demo.service.*（3 帧）`

### Requirement: 行数限制与截断

当堆栈超过配置的行数限制（默认 50 行）时，系统 SHALL 截断并保留头部和尾部关键帧。

#### Scenario: 长堆栈截断
- **WHEN** 堆栈有 200 行
- **THEN** 系统保留前 20 行和后 20 行，中间截断并标注「...（160 行已省略）」

### Requirement: 异常类型提取

系统 SHALL 从堆栈中提取异常类型（首位 `Caused by` 或顶层异常）。

#### Scenario: 提取异常类型
- **WHEN** 堆栈以 `Caused by: java.lang.NullPointerException` 开头
- **THEN** 系统提取 `NullPointerException` 作为关键信息

### Requirement: 入口点识别

系统 SHALL 识别堆栈的入口点（通常是最外层框架帧，如 Controller、Servlet）。

#### Scenario: 识别入口点
- **WHEN** 堆栈包含 `OrderController.get()`
- **THEN** 系统将该帧标记为入口点

### Requirement: 用户提示精简建议

当堆栈超过阈值（默认 30 行）时，系统 SHALL 提示用户可以粘贴完整堆栈由系统自动精简。

#### Scenario: 提示精简建议
- **WHEN** 用户粘贴超过 30 行的堆栈
- **THEN** 系统显示提示：「检测到较长堆栈，是否需要自动精简？」

---

## API Interface

### `parse_stack(stack: str, options: StackParserOptions) -> ParsedStack`

```python
@dataclass
class StackParserOptions:
    max_lines: int = 50        # 最大显示行数
    merge_repeated: bool = True # 合并重复帧
    merge_package: bool = True  # 合并同包前缀
    show_suggestion: bool = True # 显示精简建议

@dataclass
class ParsedStack:
    total_lines: int           # 原始行数
    display_lines: int         # 显示行数
    exception_type: str | None # 异常类型
    entry_point: str | None    # 入口点
    frames: list[StackFrame]   # 解析后的帧
    truncated: bool            # 是否截断
    truncated_count: int       # 截断行数
```

---

## Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC1 | HotSpot 格式正确解析 | 单元测试 |
| AC2 | 重复帧正确合并 | 单元测试 |
| AC3 | 同包前缀正确合并 | 单元测试 |
| AC4 | 长堆栈正确截断 | 单元测试 |
| AC5 | 异常类型正确提取 | 单元测试 |
| AC6 | 入口点正确识别 | 单元测试 |
| AC7 | 精简建议正确显示 | 前端测试 |
