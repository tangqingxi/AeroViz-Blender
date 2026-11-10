# Asset provenance and licence status

> 中文摘要：DF4 模型来自第三方仓库 `mengchaoheng/DF_gazebo`，该仓库**没有任何许可证**
> （GitHub API `license: null`，根目录无 LICENSE/COPYING），因此再分发权不明确。
> 本仓库不包含任何模型资产、`.blend` 工程或渲染截图；本项目自身许可证尚未确定，
> 故不放置 `LICENSE` 文件。

Checked on 2026-11-10 from the local workspace and the public GitHub API.

## 1. DF4 geometry and description

| Item | Value |
|---|---|
| Local input directory | `D:\01_科研\TIE\DF4_SolidWorks\DF4_SolidWorks` (read-only, outside this repo) |
| Description file | `ductedfan4.sdf.jinja`, 46 482 B, SHA-256 `8567be57b6181812bc0f20c8bd065b02f89eeec0f6b3047ca02154786e5b52c4` |
| Meshes | 33 STL files under `meshes/` |
| Input files total | 34 |
| Presumed upstream | <https://github.com/mengchaoheng/DF_gazebo>, branch `ductedfan`, directory `models/ductedfan4` |
| Upstream description file | `models/ductedfan4/ductedfan4.sdf.jinja`, 38 859 B, git blob `62b55d9224222945a396a075fe894ceea34c8801` |
| Local git blob of the same file | `5755d40a7e6dfdbc58bfdcf9ac05639eddcdaf32` |

**The local description file is not byte-identical to the upstream file** (46 482 B vs
38 859 B). The local copy carries simulation-side adaptations, for example an external
`<include>` of `model://gps` and a model-mass comment keeping the total at 1.56 kg with
that sensor link. The upstream commit the local copy was derived from has not been
identified, and the exact delta has not been audited. Treat the local set as a
**modified derivative** of the upstream model, not as upstream.

## 2. Upstream licence

- GitHub repository metadata reports `"license": null`.
- The repository root on branch `ductedfan` contains no `LICENSE`, `COPYING` or
  `NOTICE` file (checked 2026-11-10).
- No licence statement was found in the upstream `README.md` either.

A public repository without a licence grants **no** redistribution right: the default is
"all rights reserved". Whether the third party actually holds the rights, or is itself
redistributing someone else's CAD, cannot be determined from the repository.

## 3. What this repository does and does not contain

| Material | Where it lives | Reason |
|---|---|---|
| 33 STL files, `.sdf.jinja` | local only, never committed | third-party geometry; upstream grants no licence |
| `DF4_Stage1.blend`, `DF4_Stage1_5.blend` (≈ 5.4 MB each) | local only, git-ignored | large, regenerable, and contains the third-party geometry |
| Rendered previews and window screenshots | audit repository | evidence for the stage reports; they depict the geometry |
| Code, configs, docs, this file | main repository | authored for this project; no geometry embedded |

`.gitignore` blocks `*.stl`, `*.sdf`, `*.sdf.jinja`, `*.urdf`, `*.step` and `/output/`
so that the assets cannot be committed by accident.

## 4. What remains to be decided

1. **Project licence for this repository.** Not chosen. No `LICENSE` file is present,
   so "all rights reserved" applies. Pick one (MIT / BSD-3-Clause / Apache-2.0 are the
   usual candidates for tooling like this) and add `LICENSE` plus the copyright line.
2. **Model redistribution.** Upstream carries no licence text, so the geometry itself is
   not redistributed by this project; only reports and screenshots of the rebuilt
   assembly are published. If the geometry or a packaged artefact ever has to leave the
   team, confirm the terms first and record them here.
3. **Stage 2+ assets.** Any new airframe (SHC09 etc.) inherits the same rule: document
   provenance and rights before publishing a single screenshot.

## 5. Third-party material that *is* redistributable here

`assets/materials/gazebo_standard.json` contains a numeric summary of two material
definitions from Gazebo Classic's `gazebo.material` script
(<https://github.com/gazebosim/gazebo-classic>, Apache-2.0). It stores colour values,
not script source, and the source URL is recorded inside the file for attribution.
