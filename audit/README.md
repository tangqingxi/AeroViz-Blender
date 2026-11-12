# AeroViz 审计归档

审计资料已整合进当前主仓库，不再作为独立项目维护。DF4是第一个完整验证案例，工作流已完成至Stage4.2，Stage5暂不启动。

- [DF4归档入口](DF4/README.md)
- [Stage4索引与正式渲染](DF4/stages/stage-4/INDEX.md)
- [迁移报告](MIGRATION_REPORT.md)
- [逐文件SHA256对照](migration-file-comparison.json)

原AeroViz-Blender-Audit HEAD：`3876b07298cb19e408f1c4b7a18e029945da5f32`。2026-11-12通过Git Subtree迁入`audit/DF4/`，未使用squash，原提交历史可在主仓库查询。

历史报告记录当时状态，旧“等待验收/未授权”文字不代表当前待办。正式工程在`output/DF4/DF4.blend`，最终900帧PNG与正式MP4在仓库外`DF4_Render/`；本归档中的旧Stage4.0低清MP4仅作历史证据，不是正式成片。

证据验证使用`audit/DF4`作为root。GitHub远端旧Audit仓库依用户最新安排由用户自行删除，自动化不执行该删除。
