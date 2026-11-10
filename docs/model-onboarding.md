# 新机型接入（以 SHC09 为例）

引擎里没有机型专用代码。接入一架新飞机 = 一个 JSON 配置 + 一次验证运行。`configs/DF4.json` 是完整的样例。

## 0. 准备输入

- 上游模型目录放在**本仓库之外**，并保持只读。
- 需要机器描述（SDF/URDF）以及它引用的全部网格。
- 在 [asset-provenance.md](asset-provenance.md) 里记录数据来源与许可状态，再考虑发布任何东西。

## 1. 复制模板

```powershell
Copy-Item configs\template.json configs\SHC09.json
```

## 2. 填写描述级字段

| 键 | 含义 |
|---|---|
| `model_name` | 机型短名；用于根空对象与输出路径，不要含空格 |
| `adapter` | `"sdf"` 单模型 SDF；`"stl"` 显式零件清单 |
| `input_root` | 绝对路径，或相对仓库根的路径 |
| `description` | 相对 `input_root` 的描述文件（STL 适配器填 `null`） |
| `mesh_unit` | **网格**坐标的单位：`"m"`、`"mm"`、`"cm"` |
| `sdf_unit` | **描述文件**位姿数值的单位；SDFormat 为米 |
| `input_root` | 绝对路径，或相对仓库根的路径；默认相对 |
| `input_root_env` | 可选环境变量名；设置后整体覆盖 `input_root`，换机器不必改配置 |
| `output_dir`、`blend_name` | 当前工程位置，形如 `output/SHC09/SHC09.blend`；全阶段共用这一个文件 |
| `work_dir`、`audit_root` | 临时目录（默认 `.work`，运行后删除）与审计仓库根目录（证据写这里） |
| `apply_model_pose` | `false` 保留模型原点（不把仿真飞行高度烘进工程） |
| `uri_roots` | `model://<id>` → `input_root` 下的目录映射 |
| `ignored_includes` | 有意不建模的外部 include，**每个都要写理由** |
| `expected_dimensions_m` | 整机可见尺寸的逐轴 `[min, max]` 校验区间 |
| `coordinate_evidence`、`unit_evidence` | 简短依据，会原样进入报告 |

单位与坐标靠**声明**，绝不推断。如果写不出依据，正确做法是停下来测量，不是猜一个值。

## 3. 给零件分类

- `groups`：功能分组到通配符的映射（`"DUCT": ["duct-*.STL"]`）。没匹配上的文件进入 `UNCLASSIFIED`，不会消失。
- `reference_only`：文件名 → 理由。用于合并件与完全重复件。构建会先**证明**可见零件覆盖其 100% 独特三角面，才允许隐藏。
- `extra_meshes`：磁盘上存在但描述未引用的网格。每项要 `path`、`pose`、`reason`；因无 link 信息，挂在模型根下。

## 4. 填写材质块

`materials.source_blend` 与 `target_blend` 把 Stage 1.5 接到 Stage 1 工程上。`source_color_space` 必须显式并说明理由：`"linear"` 保留原始数值，`"srgb"` 走标准分段解码。

代码强制的规则：

- `overrides` 必须带 `reason`；覆盖项会记为 `config_override`，不会伪装成原始色。
- 一个网格被多个 visual 以不同颜色引用时，用 `object_visuals` 消歧；仍不唯一则报错，不按任意顺序选色。
- 未知脚本材质优先保留外来已有材质，否则回落到有记录的中性展示默认。
- 新确认的 Gazebo 脚本材质加到 `assets/materials/gazebo_standard.json`，不要在材质引擎里写死颜色。

## 5. 运行与验证

```powershell
$B = '<blender.exe>'
& $B --background --factory-startup --python-exit-code 1 --python .\scripts\main.py -- --config configs\SHC09.json
& $B --background --factory-startup --python-exit-code 1 --python .\scripts\materials.py -- --config configs\SHC09.json
& $B -W .\output\SHC09\SHC09.blend --python .\scripts\gui_verify.py           -- --config configs\SHC09.json
& $B -W .\output\SHC09\SHC09.blend --python .\scripts\gui_verify_materials.py -- --config configs\SHC09.json
```

然后**逐张看截图**。文件存在不等于视觉验收通过。

## 6. 报阶段前的检查清单

- [ ] `expected_dimensions_m` 与实际测量一致，且数字有解释。
- [ ] 每个隐藏参考件都有理由，且独特三角面覆盖率 100%。
- [ ] 每个 `extra_meshes` 都说明了描述文件为什么没有定义它。
- [ ] 输入 SHA-256 前后一致（构建自身会断言）。
- [ ] Stage 1.5 对本工程报告了"多少/多少对象保留"（不是照搬 DF4 的 89）。
- [ ] 材质来源分布已知：显式 RGBA / 命名脚本 / 展示默认各多少。
- [ ] 截图是**看过**的，不是只生成过。
- [ ] 报告与证据进**审计仓库**，不进本仓库。

## 7. 涵道风扇机型的参考数字

供对照：DF4 的结果是 25 个 SDF visual + 2 个未引用的补充网格 + 6 个隐藏参考件 = 33 个网格对象；26 个 link 空对象；25 个关节空对象（19 个 fixed，6 个 revolute，其中 5 个有关节子网格）。

不同机型一定不同——**不要把这些数字当预期值抄过去**。
