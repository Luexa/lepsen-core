__all__ = [
    "lepsen",
]


from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from collections.abc import Iterable, Iterator, MutableSet, Mapping
from functools import partial
from importlib.abc import Traversable
from importlib.resources import files

from beet import Context, Plugin
from beet.toolchain.helpers import sandbox
from beet.contrib.dundervar import beet_default as dundervar
from beet.contrib.inline_function_tag import beet_default as inline_function_tag
from beet.contrib.yellow_shulker_box import beet_default as yellow_shulker_box
from beet.contrib.lantern_load import base_data_pack as lantern_load
from beet.contrib.render import render

from lectern import Document
from lectern.contrib.yaml_to_json import handle_yaml

from mecha import Mecha

from .markdown_iterator import markdown_iterator


def _version_check(feature: str, version: dict[str, int]) -> str:
    """Create a version check subcommand chain based on a feature name and version dict."""

    if feature == "main":
        objective_prefix = "lepsen_core"
    else:
        objective_prefix = f"#lepsen_core.{feature}"
    return (
        f"if score {objective_prefix}.major load.status matches {version['major']} "
        + f"if score {objective_prefix}.minor load.status matches {version['minor']} "
        + f"if score {objective_prefix}.patch load.status matches {version['patch']}"
    )


# Version definition for each applicable module.
version = {
    "main": {
        "major": 0,
        "minor": 2,
        "patch": 0,
    },
    "scheduler": {
        "major": 0,
        "minor": 2,
        "patch": 0,
    },
    "forceload": {
        "major": 0,
        "minor": 2,
        "patch": 0,
    },
}

# Stringified representations of each module's version.
version_string = {
    k: f"v{version[k]['major']}.{version[k]['minor']}.{version[k]['patch']}"
    for k in version
}

# Execute condition for each module's version.
version_check = {k: _version_check(k, version[k]) for k in version}

# Data file prefix for each module and module version.
version_prefix = {
    k: f"lepsen:core/_private/{k}/{version_string[k]}" for k in version_string
}

# Dict mapping feature name to resource handle.
lectern_sources = {k: v for k, v in markdown_iterator(files(__package__))}


def apply_document(ctx: Context, file: Traversable):
    """Apply the contents of a Lectern document bundled with Lepsen Core."""

    text = file.read_text()
    for k in version_prefix:
        text = text.replace(f"__{k}_prefix__", version_prefix[k])
    document = ctx.inject(Document)
    document.add_markdown(text)


@dataclass(unsafe_hash=True)
class Feature(Plugin):
    """A feature to be applied as part of Lepsen Core."""

    name: str
    deps: list[str] = field(hash=False, compare=False)
    configurable: bool = field(hash=False, compare=False)
    action: Plugin = field(repr=False)

    def __init__(
        self,
        name: str,
        deps: Optional[list[str]] = None
        *,
        action: Optional[Plugin] = None,
        configurable: bool = False,
    ):
        self.name = name
        self.deps = [] if deps is None else deps
        self.configurable = configurable
        if action is None:
            if self.name not in lectern_sources:
                raise KeyError(f"No file {name}.md found for feature {name}")
            action = partial(apply_document, file=lectern_sources[name])
        self.action = action

    def __call__(self, ctx: Context):
        self.action(ctx)


feature_db = {
    feature.name: feature
    for feature in [
        Feature("load", action=lantern_load),
        Feature("yellow_shulker_box", action=yellow_shulker_box, configurable=False),
        Feature("main", ["load"]),
        Feature("tick_scheduler", ["main"]),
        Feature("forceload", ["main", "yellow_shulker_box"]),
        Feature("player_head"),
    ]
}


def add_feature(set: MutableSet[str], list: List[Feature], feature: Feature):
    if feature.name not in set:
        set.add(feature.name)
        for feature_dep in feature.deps:
            add_feature(set, list, feature_db[feature_dep])
        list.append(feature)


def feature_set(features: Iterable[str]) -> List[Feature]:
    feature_set = set()
    feature_list = list()
    for feature_name in features:
        if (feature := feature_db.get(feature_name)) and feature.configurable:
            add_feature(feature_set, feature_list, feature)
    return feature_list


def config_to_iter(config: dict[str, Any]) -> Iterator[str]:
    for k in config:
        if k in feature_db and config[k]:
            yield k


def lepsen(ctx: Context, features: List[Feature]):
    """Add the Lepsen core library to the current pack."""

    ctx.require(dundervar)
    ctx.require(inline_function_tag)
    for k in version:
        for t in version[k]:
            ctx.template.env.globals[f"{k}_ver_{t}"] = version[k][t]
    for k in version_check:
        ctx.template.env.globals[f"{k}_version_check"] = version_check[k]
    document = ctx.inject(Document)
    document.loaders.append(handle_yaml)
    ctx.require(*features)
    ctx.require(render(data_pack={"functions": ["*"]}))
    mecha = ctx.inject(Mecha)
    mecha.compile(ctx.data, multiline=True)
