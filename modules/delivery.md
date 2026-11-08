# GitHub交付适配
输入：具体代码变化、相关运行结果、非作者意见；消费者是下一次可复现研究和最终提交。

先从适配表读取本包OpenAI原版yeet、gh-address-comments或gh-fix-ci的当前切片，使用Git/gh或连接器执行。本场已明确授权私有提交、推送、PR与审后合并，范围内无需重新询问；原文示例涉及全量stage时改为本次明确文件。原版yeet只负责到PR，审查和采用仍由编排器处理。

流程：确认实际仓库与变更→提交相关文件→推送分支→找现有开放PR或创建→非作者审实际diff与相关行为→处理会影响使用的问题→必要检查通过后按既有授权合并。大改需更新审查；小文案变更不重跑整套研究。记录PR链接、普通Git版本和采用理由即可，不额外生成哈希清单或审查证书。提交不等于模型更强。

有反馈时适配gh-address-comments：读取所有相关review，按影响处理；用户已授权自主修复时不用再逐条询问。保留未解决分歧和实际验证。禁止把其提权参数搬到不支持提权的当前环境。CI真正阻塞交付时参考官方gh-fix-ci的失败日志定位流程；若是外部CI只给可用证据，别盲改模型。不要为了显示绿色凭空加一堆测试。

可用原生命令：git status/diff/add/commit/push；gh repo create --private；gh pr list/create/checks/view/merge；用body文件传PR说明。未知API响应先读PR真实状态。GraphQL故障可用GitHub REST读取/执行同一已授权操作，先查是否已经完成。需要回滚时用普通revert并说明行为变化，不覆盖用户未提交工作。

正式比赛提交由execution另外决定，绑定实际Notebook版本或提交文件，保留最好版本；PR合并不会自动触发它。

上游参考（2026-11-04已读取）：
- https://github.com/openai/skills/blob/main/skills/.curated/yeet/SKILL.md
- https://github.com/openai/skills/blob/main/skills/.curated/gh-fix-ci/SKILL.md
