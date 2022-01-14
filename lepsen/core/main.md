# Lepsen - Objectives Module

## Version Resolution

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

`@function __main_prefix__/enumerate`
```mcfunction
#!tag "lepsen:core/_private/enumerate"
#!if main_ver_major > 0
  # Avoid logic error where, for example, enumerating v0.1.1 and v1.0.0 causes the
  # code to believe the currently loaded version is v1.1.1 instead of v1.0.0.
  #!set main_ver_major_prev = main_ver_major - 1
  execute if score lepsen_core.major load.status matches ..__main_ver_major_prev__
    run scoreboard players reset lepsen_core.minor load.status
  execute if score lepsen_core.major load.status matches ..__main_ver_major_prev__
    run scoreboard players reset lepsen_core.patch load.status
#!endif

#!if main_ver_minor > 0
  # Avoid logic error where, for example, enumerating v0.1.1 and v0.2.0 causes the
  # code to believe the currently loaded version is v0.2.1 instead of v0.2.0.
  #!set main_ver_minor_prev = main_ver_minor - 1
  execute if score lepsen_core.major load.status matches __main_ver_major__
    if score lepsen_core.minor load.status matches ..__main_ver_minor_prev__
    run scoreboard players reset lepsen_core.patch load.status
#!endif

# With the logic errors accounted for, initialize the version scores using the
# naive method that would otherwise break due to said logic errors.
execute unless score lepsen_core.major load.status matches __main_ver_major__..
  run scoreboard players set lepsen_core.major load.status __main_ver_major__
execute if score lepsen_core.major load.status matches __main_ver_major__
  unless score lepsen_core.minor load.status matches __main_ver_minor__..
  run scoreboard players set lepsen_core.minor load.status __main_ver_minor__
execute if score lepsen_core.major load.status matches __main_ver_major__
  if score lepsen_core.minor load.status matches __main_ver_minor__
  unless score lepsen_core.patch load.status matches __main_ver_patch__..
  run scoreboard players set lepsen_core.patch load.status __main_ver_patch__
```

`@function __main_prefix__/resolve`
```mcfunction
#!tag "lepsen:core/_private/resolve"
execute __main_version_check__
  run function __main_prefix__/try_init
```

`@function __main_prefix__/try_init`
```mcfunction
# Clear older version's scheduled tick just in case it is left over.
schedule clear lepsen:core/_private/v0.1.0/tick/tick

# Store the previously loaded version of the objectives module in a fake player.
execute store result score #lepsen_core.objectives load.status
  run data get storage lepsen:core features.objectives

# If the previously loaded version of the objectives module is incompatible,
# fail initializataion by resetting the fake players and compat storage.
execute if score #lepsen_core.objectives load.status matches 2..
  run function __main_prefix__/fail_init

# If the module was either never loaded before, or is of a compatible version,
# continue with the initialization process.
execute if score #lepsen_core.objectives load.status matches ..1
  run function __main_prefix__/init

# Clean up temporary fake player now that initialization is complete.
scoreboard players reset #lepsen_core.objectives load.status
```

`@function __main_prefix__/fail_init`
```mcfunction
# Reset fake players so other packs do not think this pack is loaded.
scoreboard players reset lepsen_core.major load.status
scoreboard players reset lepsen_core.minor load.status
scoreboard players reset lepsen_core.patch load.status

# Remove compat storage in case it was left over from a previous session.
data remove storage lepsen:core compat
```

</details>

## Module Initialization

<details>

`@function __main_prefix__/init`
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

# Initialize any feature modules compatible with core module version 1.
function #lepsen:core/_private/main/1/features

# Load modules from v0.1.0 that would otherwise not load even though they are
# perfectly compatible. If they are not present then this will do nothing.
execute unless data storage lepsen:core compat.tick_scheduler
  run function lepsen:core/_private/v0.1.0/tick/setup
execute unless data storage lepsen:core compat.forceload
  run function lepsen:core/_private/v0.1.0/forceload/setup
```

</details>
