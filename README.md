# DnDSystem (WIP)

A lightweight, keyboard-first CLI to run homebrew encounters fast. It stores game data on disk, loads objects on demand, and gives you quick commands for building characters, equipping gear, rolling dice, and resolving attacks.

## What it does

* **Data & persistence**

  * JSON-backed store with identity map and dirty-write commits
  * Players/Enemies/Weapons/Accessories/Outfits in `Data/` folders
  * `db` shell to list/show/reload/delete items
* **Character management**

  * `make` commands to create players, enemies, and items
  * `equip` / `unequip` with auto-applied stat mods
  * `refresh`/`rest` helpers to recalc/restore stats
* **Combat helpers**

  * `attack` implements your accuracy/evasion and damage scaling formulas (standard & counter)
  * `damage <target> <amount>` applies raw damage and notes if the target should be dead
  * `heal` method on `Player` (integer, clamped to max HP)
* **Utilities**

  * `dice` for quick rolls
  * `help` to list all avaliable commands
  * `commit`/`reload` to persist or re-read disk state

## Quick start

```bash
python main.py

# examples inside the CLI:
help          # lists all commands
make player   # creates a player object
make enemy    # creates an enemy object
equip         # equips an item to a player or enemy
attack        # simulates damage encounter, damage optional
damage alice  # deals damage to entity (alice)
db            # browse data
exit          # quit program
```

## Project layout

```
Commands/    # CLI commands
GameObjects/ # Player, Enemy, Weapon, Accessory, Outfit
Services/    # database, orchestration, and command registry
Types/       # stats, prompts, results, gameobjects, and commands
Data/        # saved JSON objects
```

## Status & roadmap (in progress)

* ✅ Core CRUD, equip, dice, attack (incl. counters), damage, heal
* 🔜 Faster table play: status summaries, groups/batch ops, snapshots/undo
* 🔜 Systems: turn order, mana & effect tracking, resistances/temps, logs

Feedback and PRs welcome while this is still evolving.
