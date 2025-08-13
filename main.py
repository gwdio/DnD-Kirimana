# main.py
from Services.registry import CommandRegistry
from Services.database import DatabaseManager
from Services.orchestrator import Orchestrator

# Commands
from Commands.add_command import AddCommand
from Commands.echo_command import EchoCommand
from Commands.dice_command import DiceRollerCommand
from Commands.make_command import MakeCommand
from Commands.db_command import DbCommand
from Commands.rest_command import RestCommand
from Commands.refresh_command import RefreshCommand
from Commands.equip_command import EquipCommand
from Commands.unequip_command import UnequipCommand


def build_registry() -> CommandRegistry:
    registry = CommandRegistry()
    database_manager = DatabaseManager()

    # Register commands here
    registry.register(AddCommand())
    registry.register(EchoCommand())
    registry.register(DiceRollerCommand())
    registry.register(MakeCommand(database_manager))
    registry.register(DbCommand(database_manager))
    registry.register(RestCommand(database_manager))
    registry.register(RefreshCommand(database_manager))
    registry.register(EquipCommand(database_manager))
    registry.register(UnequipCommand(database_manager))

    return registry

def main():
    registry = build_registry()
    orchestrator = Orchestrator(registry)
    orchestrator.run()

if __name__ == "__main__":
    main()
