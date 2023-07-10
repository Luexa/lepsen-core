__all__ = [
    "lepsen_core",
    "LepsenCoreOptions",
]


from beet import Context, PackageablePath, configurable
from beet.contrib.lantern_load import base_data_pack as lantern_load

from pydantic import BaseModel

from .markdown_iterator import markdown_iterator


class LepsenCoreOptions(BaseModel):
    pass


@configurable(name="lepsen", validator=LepsenCoreOptions)
def lepsen_core(ctx: Context, opts: LepsenCoreOptions):
    pass
