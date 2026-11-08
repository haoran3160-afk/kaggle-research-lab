# 公开成熟来源与窄适配

默认不再依赖本机自研或来源未核实的skill。优先使用下列公开原版，已把需要的技能目录及随附资料放在upstream/；只按当前问题加载，不启动整个框架。它们在下次调用本skill时即可使用，不需全局安装同名技能或改其他项目。

2026-11-04 GitHub API观察：openai/skills 28,509 stars、1,982 forks，最近push10-28；obra/superpowers 312,147/27,767，11-03；K-Dense-AI/scientific-agent-skills 56,053/4,927，11-02。数字是仓库级关注/复用线索，并非单个技能安装量、效果或Kaggle获胜验证。原版技能及具体兼容性已阅读。许可证与来源见upstream/SOURCES.md。

| 切片 | 本包中的原版入口 | 调用边界与输出 |
|---|---|---|
| 提交/推送/PR | [OpenAI yeet](../upstream/openai/yeet/SKILL.md) | 用户已授权发布时，用现有diff、模板和结果创建/更新PR；不覆盖用户无关改动，不照搬git add -A；新draft需在审查后ready，既有ready不降回draft |
| PR反馈 | [OpenAI gh-address-comments](../upstream/openai/gh-address-comments/SKILL.md) | 读取反馈，按已授权范围处理，输出实际修复和未解分歧；无需用户重复逐条选；当前环境不能提权则不用其提权示例 |
| CI故障 | [OpenAI gh-fix-ci](../upstream/openai/gh-fix-ci/SKILL.md) | 仅真实GitHub Actions失败时取日志定位；已授权修复内继续，范围变化才升级；CI成功不代表模型更强 |
| 运行故障 | [Superpowers systematic-debugging](../upstream/superpowers/systematic-debugging/SKILL.md) | 复现→定位→最小修复→实际入口复验；单次低分不自动视作软件bug，不附加整套TDD/防御框架 |
| 代码独审 | [Superpowers requesting-code-review](../upstream/superpowers/requesting-code-review/SKILL.md) | 用其同目录code-reviewer模板，给要求、实际diff和原始结果；独立subagent输出实质问题，不继承作者结论；普通Git范围足够，不另造证明文件 |
| 机制探索 | [K-Dense scientific-brainstorming](../upstream/scientific/scientific-brainstorming/SKILL.md) | 用独立生成→竞争解释→反方→区分实验切片；不启用加权打分CLI、全套注册文件或与本赛无关的临床流程；本场已授权研究由主代理按证据选择下一实验 |
| 科学批判 | [K-Dense scientific-critical-thinking](../upstream/scientific/scientific-critical-thinking/SKILL.md) | 查替代解释、选择偏差、泛化与因果归因；不给作者BEST背书；不启用付费图示或无关医学GRADE流程 |

上游引用和辅助脚本的相对路径以该上游SKILL.md所在目录解析，不以比赛工作目录解析。上游Bash示例应按当前PowerShell/系统转换，不能照抄无法运行的命令。

每次调用明确：当前问题、现有输入、允许动作、所需产物和返回模块。上游原文保留；以上是本比赛的适用范围映射，用户当前指令和工具权限优先。原版的人工设计会审/重复询问不覆盖已授予的自治范围，也不扩大付费或公开权限。

## 其他能力的真实来源

- Kaggle运行优先官方[Kaggle/kaggle-cli](https://github.com/Kaggle/kaggle-cli)，API观察7,644stars/1,446forks；这是工具，不包装成高星skill。先用现有官方入口/SDK，按help与官方文档操作；不要从别的比赛复制虚假的支持命令。
- 学习与情报使用宿主已有搜索/GitHub/视频工具、大学与作者原始材料。当前未核到同时满足本任务自主范围和质量的通用学习skill，薄编排层继续负责先修与练习，不伪称来源成熟。DrCatHicks/learning-opportunities有2,536stars，但逐问等待用户，故只适合用户主动学习，不接后台主循环。
- 不默认接本机create-learning-path、agentic-kaggle-skill、git-workflow-and-versioning等来源/定制情况未独立核实的技能；不删除用户已有安装。模型方法从原作者开源实现与比赛实测选择，不从“框架高星”推断性能。
- anthropics/skills虽有187,266stars，未发现比上述更匹配本轮闭环的必要切片，暂不增加。高星也要经过任务匹配。
