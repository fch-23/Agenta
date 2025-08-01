# 会议纪要生成指令
## 核心要求​
生成的会议纪要需100% 覆盖所有会议要点，不得遗漏任何具体事例、数据、观点或细节；内容需保留原始表述的核心信息，避免过度概括，确保每个要点都能在纪要中找到对应呈现。​

## 操作步骤​
1. 框架锚定：先通读所有会议要点，识别内容的核心主题、模块或逻辑脉络要点中可能有框架内容，如果没有则自行总结，以此作为 “二、内容要点” 的拆分依据。​
2. 精准分类：将每个会议要点逐一对应到框架中，每个要点必须明确归入一个具体子项（如 “二、内容要点” 的 “要点一”“要点二” 等子项），分类时需遵循 “原文逻辑优先” 原则，不强行合并或拆分。​
3. 框架填充：在 “二、内容要点” 中，按拆分的框架分点叙述，每个子项（如 “要点一”）下需列出所有相关的会议要点，直接引用要点中的具体事例、数据或表述，不替换为概括性语言。​
4. 查漏补全：完成分类后，对照会议要点清单逐一核查，确认无遗漏。若存在未归入框架的要点：​
    若此类要点超过 3 个或内容篇幅占比超 10%，需新增对应子项（如 “要点四”）并明确主题；​
    若此类要点少于 3 个且篇幅较短，统一补充到 “五、其他” 中。


## 会议要点（必须使用这些内容生成，无需额外询问）：
{key_points}

## 会议基本信息（用于模板开头部分的信息）
{meeting_info}
{title}

## 模板（必须使用这个模板生成，无需额外询问，如果提供的要点中不包含模板所需要的信息，则省略模板中的那一部分）：

# {title}
**时间**：[YYYY-MM-DD HH:MM]  
**主讲人**：[姓名/角色]  
**参会人**：[姓名列表或部门]  
**记录人**：[姓名]  

## 一、分享概览  
- **核心内容**：[概括录音的主要内容]
- **关键结论**：[核心观点]  

## 二、内容要点[根据实际内容分点叙述]
### 要点一

### 要点二  

### 要点三


## 三、讨论与互动[如果没有讨论与互动部分可以省略]
- **高频问题**：[列出讨论中提到的问题与回答，如果没有可省略]
- **反馈情况**：[列出对本次讲座的反馈如果没有可以省略]

## 四、后续行动 [指对讲座设计内容的实际应用，如果没有可以省略]
- **学习资源**：[列出相关学习资源包括书籍、公众号、文章等，如果没有可省略]
- **实践计划**：[列出学习讲座内容所需要完成的具体步骤，如果没有可省略]

## 五、其他[其他内容，可能有寄语等]