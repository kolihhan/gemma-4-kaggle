# Gemma · Phase A 盲评｜2026-11-18

[事实] 评分按题 PASS/FAIL，12 小时含沙箱准备、不含最终验证，限投 1 次/日。代码快照 `bfc78ae` 的 .18 对照是 31B、5 分钟、60 次工具、80 轮；构建入口取已评分 ZIP。评分器能在普通超时或未显式 submit 时回收非空 diff。原始 129 个开发题来自 4 个仓库（67/48/13/1）。[赛事](https://www.kaggle.com/competitions/gemma-4-developer-agent) · [规则](https://www.kaggle.com/competitions/gemma-4-developer-agent/rules) · [评分器 §8](HARNESS_README.md#8-patch-extraction--phase-2-verification-verify_task) · [对照构建代码](scripts/build_toolcap60_timeout_recovery.py)

[判断] 官方只说约 120 题、约 50% Public。早期公开分值集合以两位截断、枚举 N=1…78，唯一解为 58。单看 .15/.17/.18 不能唯一反推 N。按 58，9/10/11 题分别显示 .15/.17/.18，15/58 显示 .25；目标要净加 4 题。每题 .01724。11/58 的单模型跨题独立近似 SE=.0515，Wilson 95% 区间 [.109,.309]。同一批题、不同运行的配对标准误未定。有人用相同 ZIP 得 .12 和 .17。[官方题量](https://www.kaggle.com/competitions/gemma-4-developer-agent/data?select=embeddings) · [原始公榜分值与枚举](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/743506) · [重复提交](https://www.researchforgehq.com/blog/kaggle-leaderboard-noise)

| 竞赛与迁移距离 | [事实] 参赛者披露的机制 |
|---|---|
| [Konwinski 冠军](https://www.kaggle.com/competitions/konwinski-prize/writeups/eduardo-rocha-de-andrade-1st-place-solution-write-) · [第二](https://www.kaggle.com/competitions/konwinski-prize/writeups/camaro-public-2nd-place-solution)，近 | 定位、复现、生成、用行为及回归测试选补丁；该赛错误有惩罚 |
| [APR-Comp Functional-C](https://apr-comp.github.io/results.html) · [F1X 方法](https://mechtaev.com/files/aprcomp24.pdf)，近 | 用给定测试和测试等价类筛减修复候选 |
| [Meta Hacker Cup AI 决赛第一](https://pytorch.org/event/ai-powered-competitive-programming-my-hackercup-2024-experience/)，远 | 从零写算法，检索并运行、测试生成的程序 |
| [KDD Cup 2026 Data Agents 决赛第四](https://github.com/kekshibata/kddcup2026-data-agents-4th-place-solution)，远 | 固定阶段转换条件、检查输出、测同代码多次运行 |
| [AIMO2 第二](https://github.com/imagination-research/aimo2)，远 | 按答案一致性提前结束，以剩余时间和题数分配采样 |

[事实] 每场只计一次，执行候选程序/补丁来测试 3/5，用行为测试淘汰同题补丁 2/5，条件性停止生成 2/5，从文字 issue 分层定位代码 1/5。最接近的两场都使用行为测试，其中仅 Konwinski 需要从 issue 构造复现。频数不能量化 Gemma 收益。

| [判断] 单项改动、主观 P(一次 Public≥.25) | 最便宜的证伪测量与成本 |
|---|---|
| **18%　同一行为断言在改前红、改后绿** | 对有具体期望的题原样复跑同一断言，排除导入/依赖错误；不可复现就沿用对照。用题面产生的断言区分 base/no-op 和 gold；约 1–2 人时、CPU，每个适用题最多两次窄检查。 |
| **12%　定位含糊时展开一次调用关系** | 从错误文字/标识符跟到真实实现。等预算比较首次找到生产文件的比例、调用数；约 1–2 人时、CPU。命中位置只验证定位环节。 |
| **9%　首个补丁被反证才试第二根因** | 保留首 diff，另一解释只试一次，以相同断言与邻近回归选择。记录触发、第二候选独有解、错选和超时；约 2–3 人时，每触发题多一轮修复。 |

[判断] 若隐藏两半共用一次 12 小时顺序运行，120 题平均 360 秒/题；全部用满 5 分钟时，共余 120 分钟给启动与其他开销。若按两个 split 分开运行，余量不同。[未核实] 实际调度、隐藏逐题反馈、每类故障占比、可节省的真实时间。可取得的开发 trace 才记录提取后有无补丁、阶段、用时、步数、PASS/FAIL；超时可与非空补丁并存。15 gold 与未经认证的 16 Click 题不排名。三项均无需开发 GPU。
