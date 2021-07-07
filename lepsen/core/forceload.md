# Forceloaded Chunk

`@function __prefix__/forceload/setup`
```mcfunction
#!tag "__prefix__/features"
# Set the compatibility flag for the forceload feature. The flag will not be set
# if an incompatible version of this feature was previously loaded in this world.
data modify storage lepsen:core compat.forceload set value 1
execute
    if data storage lepsen:core features.forceload
    unless data storage lepsen:core features{forceload: 1}
    run data remove storage lepsen:core compat.forceload
execute if data storage lepsen:core compat.forceload
    run data modify storage lepsen:core features.forceload set value 1

# No incompatibilities detected; enable forceload feature.
execute if data storage lepsen:core compat{forceload: 1}
    run function __prefix__/forceload/init
```

`@function __prefix__/forceload/init`
```mcfunction
# Forcibly unload and then reload the chunk.
forceload remove -30000000 8880
forceload add -30000000 8880

# Summon the marker entity if it is not already present.
execute unless entity cb-0-0-0-1
    run summon minecraft:marker -30000000 -2048 8880 {
        UUID: [I;203,0,0,1],
        Tags: [global.ignore, lepsen.forceload_marker],
        CustomName: '{"text": "Lepsen Forceload Marker"}'
    }

# Locate the bottom of the world so we can place the utility blocks.
scoreboard players set #lepsen.forceload_ready lepsen.lvar 0
execute as cb-0-0-0-1 positioned -30000000 -2048 8880
    run function __prefix__/forceload/find_world_bottom

# Summon utility item frame at this position as well.
execute if score #lepsen.forceload_ready lepsen.lvar matches 1
    at cb-0-0-0-1
    run function __prefix__/forceload/item_frame

# Store the Y level of the utility blocks in storage.
data modify storage lepsen:core forceload_y
    set from entity cb-0-0-0-1 Pos[1]
```

`@function __prefix__/forceload/find_world_bottom`
```mcfunction
# Keep entity position in sync with execution position.
teleport @s ~ ~ ~

# If this location supports block placements, place utility blocks.
execute if blocks ~ ~ ~ ~ ~ ~ ~ ~ ~ all
    run function __prefix__/forceload/place_blocks

# If this location does not support block placement, try again 16 blocks higher.
execute unless score #lepsen.forceload_ready lepsen.lvar matches 1
    # Execute function again but 16 blocks higher.
    positioned ~ ~16 ~ run function __prefix__/forceload/find_world_bottom
```

`@function __prefix__/forceload/place_blocks`
```mcfunction
#!set lock = "_" * 128
# Refresh the contents of the utility blocks.
fill ~ ~ ~ ~ ~ ~1 minecraft:stone

# Place shulker boxes with special loot tables.
fill ~ ~ ~ ~ ~ ~1 minecraft:yellow_shulker_box[facing=up]{Lock: __lock__}

# Indicate that forceloading was successful.
scoreboard players set #lepsen.forceload_ready lepsen.lvar 1
```

`@function __prefix__/forceload/item_frame`
```mcfunction
# Summon item frame if it is not already present.
execute unless entity cb-0-0-0-2
    run summon minecraft:glow_item_frame ~ ~ ~ {
        UUID: [I;203,0,0,2],
        Tags: [global.ignore, lepsen.item_frame],
        CustomName: '{"text": "Lepsen Item Frame"}',
        Invisible: 1b,
        Fixed: 1b,
        Facing: 1b
    }
teleport cb-0-0-0-2 ~ ~ ~
```
