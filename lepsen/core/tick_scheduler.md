# Lepsen - Scheduler Module

## Version Resolution

<details>

`@function_tag(merge) lepsen:core/_private/main/1/features`
```yaml
values:
  - "#lepsen:core/_private/feature/1/scheduler"
```

`@function_tag(merge) lepsen:core/_private/feature/1/scheduler`
```yaml
values:
  - "#lepsen:core/_private/scheduler/feature.1/enumerate"
  - "#lepsen:core/_private/scheduler/feature.1/resolve"
```

`@function __scheduler_prefix__/enumerate`
```mcfunction
#!tag "lepsen:core/_private/scheduler/feature.1/enumerate"
#!if scheduler_ver_major > 0
  # Avoid logic error where, for example, enumerating v0.1.1 and v1.0.0 causes the
  # code to believe the currently loaded version is v1.1.1 instead of v1.0.0.
  #!set scheduler_ver_major_prev = scheduler_ver_major - 1
  execute if score #lepsen_core.scheduler.major load.status matches ..__scheduler_ver_major_prev__
    run scoreboard players reset #lepsen_core.scheduler.minor load.status
  execute if score #lepsen_core.scheduler.major load.status matches ..__scheduler_ver_major_prev__
    run scoreboard players reset #lepsen_core.scheduler.patch load.status
#!endif

#!if scheduler_ver_minor > 0
  # Avoid logic error where, for example, enumerating v0.1.1 and v0.2.0 causes the
  # code to believe the currently loaded version is v0.2.1 instead of v0.2.0.
  #!set scheduler_ver_minor_prev = scheduler_ver_minor - 1
  execute if score #lepsen_core.scheduler.major load.status matches __scheduler_ver_major__
    if score #lepsen_core.scheduler.minor load.status matches ..__scheduler_ver_minor_prev__
    run scoreboard players reset #lepsen_core.scheduler.patch load.status
#!endif

# With the logic errors accounted for, initialize the version scores using the
# naive method that would otherwise break due to said logic errors.
execute unless score #lepsen_core.scheduler.major load.status matches __scheduler_ver_major__..
  run scoreboard players set #lepsen_core.scheduler.major load.status __scheduler_ver_major__
execute if score #lepsen_core.scheduler.major load.status matches __scheduler_ver_major__
  unless score #lepsen_core.scheduler.minor load.status matches __scheduler_ver_minor__..
  run scoreboard players set #lepsen_core.scheduler.minor load.status __scheduler_ver_minor__
execute if score #lepsen_core.scheduler.major load.status matches __scheduler_ver_major__
  if score #lepsen_core.scheduler.minor load.status matches __scheduler_ver_minor__
  unless score #lepsen_core.scheduler.patch load.status matches __scheduler_ver_patch__..
  run scoreboard players set #lepsen_core.scheduler.patch load.status __scheduler_ver_patch__
```

`@function __scheduler_prefix__/resolve`
```mcfunction
#!tag "lepsen:core/_private/scheduler/feature.1/resolve"
schedule clear __scheduler_prefix__/tick
execute __scheduler_version_check__
  run function __scheduler_prefix__/try_init
```

`@function __scheduler_prefix__/try_init`
```mcfunction
# We don't want these to pollute the scoreboard as they are implementation details.
# The official expectation is to utilize the `compat` storage object for Lepsen modules.
scoreboard players reset #lepsen_core.scheduler.major load.status
scoreboard players reset #lepsen_core.scheduler.minor load.status
scoreboard players reset #lepsen_core.scheduler.patch load.status

# Store the previously loaded version of the scheduler module in a fake player.
execute store result score #lepsen_core.scheduler load.status
  run data get storage lepsen:core features.tick_scheduler

# If the previously loaded version of the scheduler module is incompatible, fail initialization.
execute if score #lepsen_core.scheduler load.status matches 2..
  run function __scheduler_prefix__/fail_init

# If the module was either never loaded before, or is of a compatible version,
# continue with the initialization process.
execute if score #lepsen_core.scheduler load.status matches ..1
  run function __scheduler_prefix__/init

# Clean up temporary fake player now that initialization is complete.
scoreboard players reset #lepsen_core.scheduler load.status
```

</details>

## Module Initialization

<details>

`@function __scheduler_prefix__/init`
```mcfunction
# Set compatibility and feature flags for the tick scheduler.
data modify storage lepsen:core compat.tick_scheduler set value 1
data modify storage lepsen:core features.tick_scheduler set value 1

# Initialize `current_tick` tracking score and schedule the tick function.
# Every tick, the score will be incremented by 1 until it wraps around to 0
# upon reaching a value of 16. This allows packs to schedule themselves to
# execute every 16 ticks without unpredictably resetting upon reload.
scoreboard players set #16 lepsen.lvar 16
execute unless score lepsen.current_tick lepsen.pvar matches 0..15
  run scoreboard players set lepsen.current_tick lepsen.pvar 0
schedule function __scheduler_prefix__/tick 1t
```

`@function __scheduler_prefix__/tick`
```mcfunction
# Schedule this function to execute every tick.
schedule function __scheduler_prefix__/tick 1t

# Increment the current tick score and wrap around if it reaches 16.
scoreboard players add lepsen.current_tick lepsen.pvar 1
scoreboard players operation lepsen.current_tick lepsen.pvar %= #16 lepsen.lvar
```

</details>
