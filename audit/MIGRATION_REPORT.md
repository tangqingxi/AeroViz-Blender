# Final Repository Consolidation — 迁移报告

迁移日期：2026-11-12（Asia/Shanghai）。原AeroViz-Blender-Audit现为主仓库的一部分，目标`audit/DF4/`。用户最新安排：GitHub远端旧Audit仓库由用户自行删除，本轮不执行远端删除。

## 基线与历史

- 原主仓库HEAD：`1e04052ace5decd448f7053e582c77e7cd7131b5`。
- 原Audit HEAD：`3876b07298cb19e408f1c4b7a18e029945da5f32`。
- Subtree合并提交：`7e711e962765c6fb88cb5c9f68920a4ae7fd2e01`。
- 采用`git subtree add --prefix=audit/DF4 audit-source main`，未使用`--squash`。原主仓库和Audit HEAD均为当前历史祖先，没有改写历史或force push。
- Audit远端仅main，无tags、其他公开refs、LFS文件、releases、issues、PRs或wiki。原仓库Public。

本地父目录已由用户改为`D:\01_科研\TIE\DF4_Blender`；模型目录改名为`DF4_gazebo`。配置按实际路径修正，原始模型只读；正式素材仍在父目录的`DF4_Render`，未移动或删除。

## 备份

迁移前已fetch并确认两个仓库clean且与远端一致。完整mirror和bundle位于主仓库忽略目录`.work/audit-migration/`；`git bundle verify`与`git fsck --full`通过。由于远端删除改由用户处理，备份保留在本地，不上传Git。

## 文件与证据

原Audit实际173个文件、84,044,806字节（约80.15MiB），均经Subtree迁入，没有额外未跟踪或忽略的独有文件。逐文件路径、原字节数、原SHA256和迁移后SHA256见[migration-file-comparison.json](migration-file-comparison.json)。

156个文件保持字节一致；17个文件有明确记录的链接/入口/清单更新。普通历史报告仅替换旧仓库自身链接；README/HANDOFF更新为归档入口。机器JSON中的仓库引用替换也列入逐文件对照；阶段结论、测量结果及历史绝对路径不作当前化改写。

旧仓库自身URL映射到主仓库`blob/main/audit/DF4/`或`tree/main/audit/DF4/`，外部上游链接不变。随后按真实文件字节刷新原清单的SHA256与已有bytes字段，不删除条目、不降低验证标准。未改动PNG、LOG、MP4等二进制历史证据。

实际发现10份阶段清单及1份全仓快照，共11份；其中包含Stage4.1/4.2独立记录。迁移前全部PASS，迁移后继续使用原`verify_evidence.py`、以`audit/DF4`为root验证。Markdown内部文件/目录链接另行全量检查，旧Audit URL扫描排除Git数据库及完整历史备份。

## 当前工作流

Stage1、1.5、2、3完成；Stage4.0-R3完成并验收；Stage4.1 Cycles画质定标通过；Stage4.2正式900帧PNG与MP4完成。DF4可视化工作流完成，Stage5暂不启动，不将历史未授权状态当作当前任务。

正式工程SHA256保持`cfafc7c7245654409a378a7c16267251a3307863dfcfb6c288ac53c1674295a0`。迁移前对仓库外素材974文件和模型34文件记录路径/字节/SHA256，结束时完整复核。模型、Blend、900张正式PNG和正式MP4不上传。

## 完成检查

迁移内容将正常fast-forward推送；从GitHub重新clone主仓库，逐文件核对173文件并重跑全部证据清单和Markdown链接检查。核对通过后才删除本地独立Audit目录，并移除临时audit-source remote，主仓库只保留origin。

最终执行结果记录在[migration-validation.json](migration-validation.json)与[migration-completion.json](migration-completion.json)。主仓库最终提交由本文件所在Git HEAD及交付消息标识，避免文件自引用其提交哈希。

GitHub远端旧Audit仓库未由自动化删除；用户自行在旧仓库Settings → General → Danger Zone → Delete this repository完成删除。现有CLI登录账号为tangqingxi，未改变账号或扩大令牌权限。
