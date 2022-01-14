__all__ = [
    "lectern_sources",
    "beet_default",
    "lepsen",
]


from dataclasses import InitVar, dataclass, field
from re import M
from typing import Any, ClassVar, Dict, Iterable, Iterator, List, Optional, Set, Tuple
from importlib.abc import Traversable
from importlib.resources import files

from beet import Context
from beet.library.data_pack import LootTable
from beet.toolchain.helpers import sandbox
from beet.contrib.dundervar import beet_default as dundervar
from beet.contrib.inline_function_tag import beet_default as inline_function_tag
from beet.contrib.yellow_shulker_box import beet_default as yellow_shulker_box
from beet.contrib.hangman import hangman
from beet.contrib.render import render

from lectern import Document
from lectern.contrib.yaml_to_json import handle_yaml

from mecha import Mecha


def _files(directory: Traversable) -> Iterator[Tuple[str, Traversable]]:
    """Iterate over Markdown files in the current package."""

    for resource in directory.iterdir():
        if resource.is_dir():
            yield from _files(resource)
        elif resource.name.endswith(".md"):
            yield resource.name[:-3], resource


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
lectern_sources = {k: v for k, v in _files(files(__name__))}

features = {
    "load": [],
    "main": ["load"],
    "tick_scheduler": ["main"],
    "forceload": ["main"],
    "player_head": [],
}


def add_feature(set: Set[str], feature: str):
    if feature not in set:
        set.add(feature)
        for feature_dep in features[feature]:
            add_feature(set, feature_dep)


def feature_set(config: Optional[Dict[str, Any]]) -> Set[str]:
    feature_set = set()
    for feature in features:
        if config and config.get(feature):
            add_feature(feature_set, feature)
    return feature_set


def lepsen(config: Optional[Dict[str, Any]]):
    """Return a plugin that will add the Lepsen Core library to the current pack."""

    # Read Lepsen feature config.
    features = feature_set(config)

    def plugin(ctx: Context):
        # Load and render the requested documents.
        ctx.require(dundervar)
        ctx.require(inline_function_tag)
        for k in version:
            for t in version[k]:
                ctx.template.env.globals[f"{k}_ver_{t}"] = version[k][t]
        for k in version_check:
            ctx.template.env.globals[f"{k}_version_check"] = version_check[k]
        document = ctx.inject(Document)
        document.loaders.append(handle_yaml)
        for k in features:
            text = lectern_sources[k].read_text()
            for k in version_prefix:
                text = text.replace(f"__{k}_prefix__", version_prefix[k])
            document.add_markdown(text)
        ctx.require(render(data_pack={"functions": ["*"]}))
        mecha = ctx.inject(Mecha)
        mecha.compile(ctx.data, multiline=True)
        if "forceload" in features:
            ctx.require(yellow_shulker_box)

    return plugin


def beet_default(ctx: Context):
    plugin = lepsen(ctx.meta.get("lepsen", {}))
    ctx.require(sandbox(plugin))
