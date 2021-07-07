# Player Head Loot Table

`@loot_table lepsen:core/player_head`
```yaml
type: minecraft:generic
pools:
  - rolls: 1
    entries:
      - type: minecraft:item
        name: minecraft:player_head
        functions:
          - function: minecraft:fill_player_head
            entity: this
```
