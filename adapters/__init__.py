"""Format adapters: the only place where a model description format is parsed.

An adapter is a module with one required function::

    read(config: dict, input_root: Path) -> dict

It returns the neutral scene description consumed by ``scripts/scene_builder.py``::

    {
      "parts":   [{"file": str, "link": str|None, "scale": [sx, sy, sz],
                   "matrix": 4x4 | None, "pose": [6] | None, "reason": str}],
      "links":   {name: {"matrix": 4x4, "inertial_pose": str}},
      "joints":  [{"name", "type", "child", "parent", "axis", "axis_frame",
                   "lower", "upper", "matrix", "axis_model"}],
      "includes": [...], "ignored_joints": [...], "model_pose": 4x4,
    }

Adding an aircraft format must not require touching the scene builder: register
the new module in ``ADAPTERS`` below and select it from a model config with
``"adapter": "<key>"``.  Adapters stay aircraft-agnostic; everything specific to
one airframe belongs in ``configs/<MODEL>.json``.
"""

# Adapter key -> importable module name.  Keep this the single registry so that
# selecting a format is a configuration change, not a code change.
ADAPTERS = {
    "sdf": "adapters.import_sdf",
    "stl": "adapters.import_stl",
}


def resolve(key):
    """Return the importable module path for an adapter key."""
    try:
        return ADAPTERS[key]
    except KeyError:
        raise ValueError(
            f"尚未注册该格式适配器：{key!r}；已注册：{sorted(ADAPTERS)}"
        ) from None
