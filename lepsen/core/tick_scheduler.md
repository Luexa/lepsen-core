# Tick Scheduler

`@function __prefix__/tick/setup`
```mcfunction
#!tag "__prefix__/features"
# Set the compatibility flag for the tick scheduler feature. The flag will not be
# set if an incompatible version of this feature was previously loaded in this world.
data modify storage lepsen:core compat.tick_scheduler set value 1
execute
    if data storage lepsen:core features.tick_scheduler
    unless data storage lepsen:core features{tick_scheduler: 1}
    run data remove storage lepsen:core compat.tick_scheduler
execute if data storage lepsen:core compat.tick_scheduler
    run data modify storage lepsen:core features.tick_scheduler set value 1

# No incompatibilities detected; enable tick scheduler feature.
execute if data storage lepsen:core compat{tick_scheduler: 1}
    run function __prefix__/tick/init
```

`@function __prefix__/tick/init`
```mcfunction
# Initialize `current_tick` tracking score and schedule the tick function.
# Every tick, the score will be incremented by 1 until it wraps around to 0
# upon reaching a value of 16. This allows packs to schedule themselves to
# execute every 16 ticks without unpredictably resetting upon reload.
scoreboard players set #16 lepsen.lvar 16
execute unless score lepsen.current_tick lepsen.pvar matches 0..15
    run scoreboard players set lepsen.current_tick lepsen.pvar 0
schedule function __prefix__/tick/tick 1t
```

`@function __prefix__/tick/tick`
```mcfunction
# Schedule this function to execute every tick.
schedule function __prefix__/tick/tick 1t

# Increment the current tick score and wrap around if it reaches 16.
scoreboard players add lepsen.current_tick lepsen.pvar 1
scoreboard players operation lepsen.current_tick lepsen.pvar %= #16 lepsen.lvar
```
