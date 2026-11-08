# 轻量工作记录

已有项目runner与记录足够时直接用它。否则一个workspace.json记录目标、当前最好版本、实验结果、远端作业、预算、学习与下一动作；一个主代理写入，专家通过主代理交结果。此脚本不运行模型，不判科学结论，也不生成校验证书。

```powershell
python scripts/workspace.py --file project/workspace.json init --goal "本场的实际结果目标" --competition slug
python scripts/workspace.py --file project/workspace.json next --action action.json
python scripts/workspace.py --file project/workspace.json start --id run-1
# 宿主现在实际执行command并读取结果
python scripts/workspace.py --file project/workspace.json record --result result.json
python scripts/workspace.py --file project/workspace.json status
# 按需读取原完整视图
python scripts/workspace.py --file project/workspace.json status --full
```

CLI `status` 默认精简续接视图：当前 `next_action` 完整保留，goal、champion、budget、learning 等当前字段原样输出。remote_jobs 保留非终态、未知状态和可恢复的 no_write；completed/failed/cancelled 仅在当前 next_action.remote_id 引用时显示。当前引用的 failed 不因显示过滤而丢失。

最近实验只显示 id、action_id、recorded_at、outcome、decision、evidence，不带旧 next_action/action/proposed_next 等可执行快照；legacy_pending 旧操作块不默认回显。`status --full` 返回原完整 status 视图（仍是最近五条实验及全部 remote_jobs/legacy_pending），供具体问题查证。此调整只影响 CLI status 展示；Workspace.status() 完整 in-process API、原 JSON/schema 及 init/next/start/record 行为不变。

action.json：
```json
{"id":"run-1","kind":"cpu","cwd":"E:/project","command":["python","evaluate.py"],"expected_results":["results.json"]}
```
也可用instruction说明具体宿主动作。kind是cpu/remote/monitor。远端动作另给稳定remote_id（例如项目-notebook版本用途）；start先记uncertain，再实际调用一次工具。收到后record.remote保存真实provider_id、version、state和observation。未知/已受理作业先查同一对象，不因为换动作名而重复发送。CPU仍可执行。

result.json：
```json
{"id":"exp-1","action_id":"run-1","hypothesis":"这项变化能解决哪个错误群","control":"baseline-v1","outcome":"实际观察到的净变化与回归","evidence":["results.json"],"next_action":{"id":"inspect-loss","kind":"cpu","instruction":"读取失败样本并区分生成覆盖和选择损失"}}
```

需要采用时由宿主判断后显式record.adopt：candidate、basis（quality/cost/equivalence）、measurement、evidence。仅说明tests pass不会更换champion；即使填写了字段，也不意味着工具证明了方法有效。record.budget记录剩余额度/在途/这次完整成本，record.learning记录用户真实练习进展。遥远结果的字段远比重复写状态文件有用。

迁移旧项目：
```powershell
python scripts/workspace.py --file project/workspace.json migrate-legacy --db old.sqlite3 --competition slug --goal "继续已有目标"
```
只读导入旧未完成任务、provider回执和未知责任。先查远端真实状态，不能把导入记录当新任务重发。公开包不附带旧调度器；迁移仅只读导入用户仍持有的旧DB。不要为了迁移正在运行的项目改变执行入口，先收完已受理任务。

安装：从源码运行python scripts/install_skill.py。直接复制运行模块，旧安装保存在技能发现目录以外的skill-backups中，便于找回本地笔记；不比较或生成文件哈希。INSTALLATION.json只列版本、来源和安装文件。

异步结果都应带action_id。显式迟到结果的next_action/adopt会保留为proposed_next/proposed_adopt；当前计划和champion不自动变化。无action_id只用于主代理主动记录，不能省略它来导入迟到结果。remote_jobs保留原启动action，可在切换任务后找回命令和目标。
