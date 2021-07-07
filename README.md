# Lepsen Core

Data pack utility library packaged as a [Beet](https://github.com/mcbeet/beet) plugin.

## Example Beet Configuration

Note that any directly required feature must be manually specified for it to be included in the generated data pack.
Implicit dependencies of a required feature will be loaded automatically, however, so users of the tick scheduler or forceloaded chunk need not enable the `main` feature.

```yaml
pipeline:
  - lepsen.core
meta:
  lepsen:
    main: true
    forceload: true
    tick_scheduler: true
    player_head: true
data_pack:
  name: Example
  load: ["src/*"]
```

## Data Pack Initialization

This pack uses [Lantern Load](https://github.com/LanternMC/load), but the recommended way to check for correct pack initialization is through *compatibility flags*.
The benefit of this approach is that a new major version may not break usage of a feature, making this a more flexible way of checking for successful dependency loading.

An example of minimal initialization of this pack is as follows (including the correct way to check for compatibility flags).

`@function_tag(merge) load:load`

```json
{
    "values": [
        {"id": "#lepsen:core/load", "required": false},
        "example:load"
    ]
}
```

`@function example:load`

```mcfunction
execute
    if score #lepsen_core.compat load.status matches 1
    if data storage lepsen:core compat{
        objectives: 1,
        forceload: 1
    }
    run function example:init
```

`@function example:init`

```mcfunction
# Indicate that the plack was successfully loaded.
scoreboard players set example_pack load.status 1

# Pack initialization logic.
# ...
```

## License

Lepsen Core is made freely available under the terms of the [0BSD License](LICENSE).
Third-party contributions shall be licensed under the same terms unless explicitly stated otherwise.
