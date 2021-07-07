# Lantern Load

`@function_tag(merge) minecraft:load`
```yaml
values:
  - "#load:_private/load"
```

`@function_tag(merge) load:_private/load`
```yaml
values:
  - "#load:_private/init"
  - id: "#load:pre_load"
    required: false
  - id: "#load:load"
    required: false
  - id: "#load:post_load"
    required: false
```

`@function_tag(merge) load:_private/init`
```yaml
values:
  - load:_private/init
```

`@function load:_private/init`
```mcfunction
# Reset scoreboards so packs can set values accurate for current load.
scoreboard objectives add load.status dummy
scoreboard players reset * load.status
```
