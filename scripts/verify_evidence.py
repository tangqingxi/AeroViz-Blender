"""校验 Audit 清单中列出的证据字节；不修改任何清单或证据。"""
import argparse
import hashlib
import json
from pathlib import Path


def verify(root, manifest):
    root=Path(root).resolve()
    manifest=Path(manifest).resolve()
    data=json.loads(manifest.read_text(encoding="utf8"))
    rows=data.get("evidence")
    if not isinstance(rows,list) or not rows:
        raise ValueError("证据清单必须包含非空 evidence 数组")
    seen=set()
    for row in rows:
        relative=Path(row["path"])
        path=(root/relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(root) or path==manifest:
            raise ValueError(f"无效证据路径：{row['path']}")
        if row["path"] in seen:
            raise ValueError(f"重复证据：{row['path']}")
        seen.add(row["path"])
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=row["sha256"].lower():
            raise ValueError(f"SHA256 不匹配：{row['path']}")
    print("EVIDENCE_PASS",manifest.relative_to(root).as_posix(),len(rows))
    return len(rows)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("manifest")
    args=parser.parse_args()
    verify(args.root,args.manifest)
