# AeroViz-Blender — Audit Repository

本仓库是 **AeroViz-Blender** 的阶段报告、验收证据与交接记录，**不含源码、不含模型资产**。

- 开发仓库（代码、配置、文档）：<https://github.com/tangqingxi/AeroViz-Blender>
- 审计仓库（本仓库）：<https://github.com/tangqingxi/AeroViz-Blender-Audit>

## 仓库分工

| 仓库 | 内容 |
|---|---|
| AeroViz-Blender | 通用 Blender 自动化代码、适配器、机型配置、材质与后续动画/渲染实现 |
| AeroViz-Blender-Audit（本仓库） | 每个阶段**一份**主报告 + 证据附件、SHA256 清单、验收记录、交接记录、未解决问题 |

两个仓库相互独立：审计报告与实验证据不得混入主仓库；本仓库不得放入可执行源码或原始模型数据。

## 阶段索引

| 阶段 | 内容 | 状态 | 报告 |
|---|---|---|---|
| Stage 1 | 通用模型导入与空间装配恢复 | 已完成（本地验收通过） | [`stages/stage-1/STAGE_1_REPORT.md`](stages/stage-1/STAGE_1_REPORT.md) |
| Stage 1.5 | SDF 材质恢复 | 已完成（本地验收通过） | [`stages/stage-1.5/STAGE_1_5_REPORT.md`](stages/stage-1.5/STAGE_1_5_REPORT.md) |
| Stage 2 | 机械运动骨架与独立运动测试 | **COMPLETE / PASS** | [`STAGE_2_REPORT.md`](stages/stage-2/STAGE_2_REPORT.md) |
| Stage 3 | FLU定义与爆炸/恢复视图 | **COMPLETE / PASS** | [`STAGE_3_REPORT.md`](stages/stage-3/STAGE_3_REPORT.md) |
| Stage 4.0 | 展示镜头与渐进式拆解原型 | **技术PASS / 等待人工效果验收** | [STAGE_4_0_REPORT.md](stages/stage-4.0/STAGE_4_0_REPORT.md) |
| Stage 4.0-R1 | 中性摄影棚、姿态、同步拆解与逆序装配 | **READY FOR USER VISUAL ACCEPTANCE** | [STAGE_4_0_R1_REPORT.md](stages/stage-4.0-r1/STAGE_4_0_R1_REPORT.md) |
| Stage 5 | 多机型适配与工具完善 | 未执行 | — |

当前验证机型只有 DF4。项目定位、路线图与代码结构见开发仓库 README。

## 目录结构

```text
AeroViz-Blender-Audit/
├── README.md                      本文件：导航与阶段状态
├── HANDOFF.md                     下一 Agent 的交接记录
├── stages/
│   ├── stage-1/
│   │   ├── STAGE_1_REPORT.md      阶段主报告（唯一）
│   │   ├── evidence-manifest.json 证据 SHA256 清单
│   │   └── evidence/              截图与测量记录
│   └── stage-1.5/
│       ├── STAGE_1_5_REPORT.md
│       ├── evidence-manifest.json
│       └── evidence/
└── manifests/
    ├── ARTIFACT_MANIFEST.md       全部输入/产物哈希、来源与许可证核查
    └── reverify-2026-11-10.json   交付字节的只读重开复验记录
```

每个阶段只有一份主报告；截图作为报告内的证据附件，不另建零散说明文档。

## 证据校验

证据清单由 `build_manifest.py` 生成，记录了每份证据的相对路径与 SHA256，以及它所对应的开发提交。本地校验：

```bash
python scripts/verify_evidence.py <audit-root> <audit-root>/stages/stage-1/evidence-manifest.json
python scripts/verify_evidence.py <audit-root> <audit-root>/stages/stage-1.5/evidence-manifest.json
```

退出码 0 表示所有列出的文件本地字节与记录一致。该校验只证明本地文件完整性，不证明测试结果或科学结论。

## 当前工程

本地只有一个工程：`output/DF4/DF4.blend`，SHA256 `392af12f14a6fbfb27b201d836b86752c90a97afbc024960fc00f03407726824`。

Stage 1、Stage 1.5、Stage 2 与 Stage 3 的成果都在这一个文件里；后续阶段直接在它上面迭代，不再生成阶段编号的 `.blend`。两份历史报告保留原始文件名与历史哈希，作为过程记录。

## 分工边界

本仓库只放报告、截图与测量记录，不含原始 STL/SDF/`.blend`，也不放可执行源码。模型来源与文件取舍见 [`manifests/ARTIFACT_MANIFEST.md`](manifests/ARTIFACT_MANIFEST.md) §1、§6。

## 协作流程

1. ChatGPT 制定阶段任务。
2. Agent 在本地执行，代码提交主仓库。
3. Agent 将报告与验收证据提交本仓库。
4. 用户提供本仓库链接。
5. ChatGPT 阅读报告并复核；通过后授权下一阶段。

每个阶段只产生一个完整主报告，用户不需要手工整理多个文件。

## 明确声明

- Stage 1.5 结束时工程是静态的；Stage 2 现已加入五个关节的独立动画，尚无爆炸视图或视频。
- 报告中的数据全部来自实际执行与工程文件，未将计划功能写成已实现功能。
- 未创建版本 Tag；本项目自身许可证尚未确定。

Stage 2 窗口、运动测试和保存后回归见阶段主报告；证据清单为 `stages/stage-2/evidence-manifest.json`。当前工程：117对象、33网格、7材质、33材质分配、29动画对象（旧5个JOINT与24个独立爆炸Empty）。

Stage3主报告与截图见 `stages/stage-3/STAGE_3_REPORT.md`，坐标定义为FLU，爆炸距离是展示参数。按用户最新要求截图验收后已退出Blender，不要求用户操作软件。
