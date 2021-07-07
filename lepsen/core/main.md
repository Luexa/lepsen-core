# Main Library

## Pack Initialization

<details>

`@function_tag(merge) load:load`
```yaml
values:
  - "#lepsen:core/load"
```

`@function_tag(merge) lepsen:core/load`
```yaml
values:
  - id: "#lepsen:core/_private/dependencies"
    required: false
  - "#lepsen:core/_private/enumerate"
  - "#lepsen:core/_private/resolve"
```

`@function __prefix__/enumerate`
```mcfunction
#!tag "lepsen:core/_private/enumerate"
execute
    unless score lepsen_core.major load.status matches 0..
    run scoreboard players set lepsen_core.major load.status 0
execute
    if score lepsen_core.major load.status matches 0
    unless score lepsen_core.minor load.status matches 1..
    run scoreboard players set lepsen_core.minor load.status 1
execute
    if score lepsen_core.major load.status matches 0
    if score lepsen_core.minor load.status matches 1
    unless score lepsen_core.patch load.status matches 0..
    run scoreboard players set lepsen_core.patch load.status 0
```

`@function __prefix__/resolve`
```mcfunction
#!tag "lepsen:core/_private/resolve"
schedule clear __prefix__/tick/tick
execute __version_check__
    run function __prefix__/init
```

`@function __prefix__/try_init`
```mcfunction
# If a breaking change was made to how Lepsen scoreboard objectives work in a
# version of Lepsen previously loaded in this world, fail initialization.
execute
    if data storage lepsen:core features.objectives
    unless data storage lepsen:core features{objectives: 1}
    run function __prefix__/fail_init

# Otherwise, continue with the initialization process.
execute __version_check__
    run function __prefix__/init
```

`@function __prefix__/fail_init`
```mcfunction
# Reset fake players so other packs do not think this pack is loaded.
scoreboard players reset lepsen_core.major load.status
scoreboard players reset lepsen_core.minor load.status
scoreboard players reset lepsen_core.patch load.status
data remove storage lepsen:core compat
```

`@function __prefix__/init`
```mcfunction
# Global data that will persist between reloads.
scoreboard objectives add lepsen.pvar dummy

# Global data that will survive until the next reload.
scoreboard objectives add lepsen.lvar dummy
scoreboard players reset * lepsen.lvar

# Define "compatibility flags" in storage, which can be used by dependent packs
# to remain compatible with newer major versions of this data pack so long as
# the compatibility flag for the features being used remains the same.
scoreboard players set #lepsen_core.compat load.status 1

# Set the compatibility flag for the objectives feature (eligibility checked in
# `try_init` as objectives are expected to work).
data modify storage lepsen:core compat set value {objectives: 1}
data modify storage lepsen:core features.objectives set value 1

# Initialize any features provided by this distribution of Lepsen.
function #__prefix__/features
```

</details>
