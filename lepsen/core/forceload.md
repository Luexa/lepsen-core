# Lepsen - Forceload Module

## Version Resolution

<details>

`@function_tag(merge) lepsen:core/_private/main/1/features`
```yaml
values:
  - "#lepsen:core/_private/feature/1/forceload"
```

`@function_tag(merge) lepsen:core/_private/feature/1/forceload`
```yaml
values:
  - "#lepsen:core/_private/forceload/feature.1/enumerate"
  - "#lepsen:core/_private/forceload/feature.1/resolve"
```

`@function __forceload_prefix__/forceload/enumerate`
```mcfunction
#!tag "lepsen:core/_private/forceload/feature.1/enumerate"
#!if forceload_ver_major > 0
  # Avoid logic error where, for example, enumerating v0.1.1 and v1.0.0 causes the
  # code to believe the currently loaded version is v1.1.1 instead of v1.0.0.
  #!set forceload_ver_major_prev = forceload_ver_major - 1
  execute if score #lepsen_core.forceload.major load.status matches ..__forceload_ver_major_prev__
    run scoreboard players reset #lepsen_core.forceload.minor load.status
  execute if score #lepsen_core.forceload.major load.status matches ..__forceload_ver_major_prev__
    run scoreboard players reset #lepsen_core.forceload.patch load.status
#!endif

#!if forceload_ver_minor > 0
  # Avoid logic error where, for example, enumerating v0.1.1 and v0.2.0 causes the
  # code to believe the currently loaded version is v0.2.1 instead of v0.2.0.
  #!set forceload_ver_minor_prev = forceload_ver_minor - 1
  execute if score #lepsen_core.forceload.major load.status matches __forceload_ver_major__
    if score #lepsen_core.forceload.minor load.status matches ..__forceload_ver_minor_prev__
    run scoreboard players reset #lepsen_core.forceload.patch load.status
#!endif

# With the logic errors accounted for, initialize the version scores using the
# naive method that would otherwise break due to said logic errors.
execute unless score #lepsen_core.forceload.major load.status matches __forceload_ver_major__..
  run scoreboard players set #lepsen_core.forceload.major load.status __forceload_ver_major__
execute if score #lepsen_core.forceload.major load.status matches __forceload_ver_major__
  unless score #lepsen_core.forceload.minor load.status matches __forceload_ver_minor__..
  run scoreboard players set #lepsen_core.forceload.minor load.status __forceload_ver_minor__
execute if score #lepsen_core.forceload.major load.status matches __forceload_ver_major__
  if score #lepsen_core.forceload.minor load.status matches __forceload_ver_minor__
  unless score #lepsen_core.forceload.patch load.status matches __forceload_ver_patch__..
  run scoreboard players set #lepsen_core.forceload.patch load.status __forceload_ver_patch__
```

`@function __forceload_prefix__/resolve`
```mcfunction
#!tag "lepsen:core/_private/forceload/feature.1/resolve"
schedule clear __forceload_prefix__/tick
execute __forceload_version_check__
  run function __forceload_prefix__/try_init
```

`@function __forceload_prefix__/try_init`
```mcfunction
# We don't want these to pollute the scoreboard as they are implementation details.
# The official expectation is to utilize the `compat` storage object for Lepsen modules.
scoreboard players reset #lepsen_core.forceload.major load.status
scoreboard players reset #lepsen_core.forceload.minor load.status
scoreboard players reset #lepsen_core.forceload.patch load.status

# Store the previously loaded version of the forceload module in a fake player.
execute store result score #lepsen_core.forceload load.status
  run data get storage lepsen:core features.tick_forceload

# If the previously loaded version of the forceload module is incompatible, fail initialization.
execute if score #lepsen_core.forceload load.status matches 2..
  run function __forceload_prefix__/fail_init

# If the module was either never loaded before, or is of a compatible version,
# continue with the initialization process.
execute if score #lepsen_core.forceload load.status matches ..1
  run function __forceload_prefix__/init

# Clean up temporary fake player now that initialization is complete.
scoreboard players reset #lepsen_core.forceload load.status
```

</details>

## Module Initialization

<details>

`@function __forceload_prefix__/forceload/init`
```mcfunction
# Set compatibility and feature flags for the forceload module.
data modify storage lepsen:core compat.forceload set value 1
data modify storage lepsen:core features.forceload set value 1

# Forcibly unload and then reload the chunk.
forceload remove -30000000 8880
forceload add -30000000 8880

# Summon the marker entity if it is not already present.
execute unless entity cb-0-0-0-1
    run summon minecraft:marker -30000000 -2048 8880 {
        UUID: [I;203,0,0,1],
        Tags: [lepsen.forceload_marker],
        CustomName: '{"text": "Lepsen Forceload Marker"}'
    }

# Locate the bottom of the world so we can place the utility blocks.
scoreboard players set #lepsen.forceload_ready lepsen.lvar 0
execute as cb-0-0-0-1 positioned -30000000 -2048 8880
    run function __forceload_prefix__/forceload/find_world_bottom

# Summon utility item frame at this position as well.
execute if score #lepsen.forceload_ready lepsen.lvar matches 1
    at cb-0-0-0-1
    run function __forceload_prefix__/forceload/item_frame

# Store the Y level of the utility blocks in storage.
data modify storage lepsen:core forceload_y
    set from entity cb-0-0-0-1 Pos[1]
```

`@function __forceload_prefix__/forceload/find_world_bottom`
```mcfunction
# Keep entity position in sync with execution position.
teleport @s ~ ~ ~

# If this location supports block placements, place utility blocks.
execute if blocks ~ ~ ~ ~ ~ ~ ~ ~ ~ all
    run function __forceload_prefix__/forceload/place_blocks

# If this location does not support block placement, try again 16 blocks higher.
execute unless score #lepsen.forceload_ready lepsen.lvar matches 1
    # Execute function again but 16 blocks higher.
    positioned ~ ~16 ~ run function __forceload_prefix__/forceload/find_world_bottom
```

`@function __forceload_prefix__/forceload/place_blocks`
```mcfunction
#!set lock = "_" * 128
# Refresh the contents of the utility blocks.
fill ~ ~ ~ ~ ~ ~1 minecraft:stone

# Place shulker boxes with special loot tables.
fill ~ ~ ~ ~ ~ ~1 minecraft:yellow_shulker_box[facing=up]{Lock: __lock__}

# Indicate that forceloading was successful.
scoreboard players set #lepsen.forceload_ready lepsen.lvar 1
```

`@function __forceload_prefix__/forceload/item_frame`
```mcfunction
# Summon item frame if it is not already present.
execute unless entity cb-0-0-0-2
    run summon minecraft:glow_item_frame ~ ~ ~ {
        UUID: [I;203,0,0,2],
        Tags: [lepsen.item_frame],
        CustomName: '{"text": "Lepsen Item Frame"}',
        Invisible: 1b,
        Fixed: 1b,
        Facing: 1b
    }
teleport cb-0-0-0-2 ~ ~ ~
```

</details>
