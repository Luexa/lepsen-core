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


def _files(directory: Traversable) -> Iterator[Tuple[str, Traversable]]:
    """Iterate over Markdown files in the current package."""

    for resource in directory.iterdir():
        if resource.is_dir():
            yield from _files(resource)
        elif resource.name.endswith(".md"):
            yield resource.name[:-3], resource


# Dict mapping feature name to resource handle.
lectern_sources = {k: v for k, v in _files(files(__name__))}

# Prefix used for multi-version compatibility.
prefix = "lepsen:core/_private/v0.1.0"

# Version check used to avoid repetition.
version_check = (
    "if score lepsen_core.major load.status matches 0 "
    + "if score lepsen_core.minor load.status matches 1 "
    + "if score lepsen_core.patch load.status matches 0"
)

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
        ctx.template.env.globals["version_check"] = version_check
        document = ctx.inject(Document)
        document.loaders.append(handle_yaml)
        for text in [lectern_sources[k].read_text() for k in features]:
            text = text.replace("__prefix__", prefix)
            document.add_markdown(text)
        ctx.require(hangman("*"))
        ctx.require(render(data_pack={"functions": ["*"]}))
        if "forceload" in features:
            ctx.require(yellow_shulker_box)


    return plugin


def beet_default(ctx: Context):
    plugin = lepsen(ctx.meta.get("lepsen", {}))
    ctx.require(sandbox(plugin))
