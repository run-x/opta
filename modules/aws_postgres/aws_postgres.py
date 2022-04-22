from typing import TYPE_CHECKING, Optional

from modules.base import ModuleProcessor
from opta.exceptions import UserErrors

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsPostgresProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        super(AwsPostgresProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        create_global_database: bool = self.module.data.get(
            "create_global_database", False
        )
        existing_global_database_id: Optional[str] = self.module.data.get(
            "existing_global_database_id", None
        )
        restore_from_snapshot: Optional[str] = self.module.data.get(
            "restore_from_snapshot"
        )
        database_name: Optional[str] = self.module.data.get("database_name")
        if database_name is not None and existing_global_database_id is not None:
            raise UserErrors(
                "You can not specify a database name when creating a read replica for an existing Aurora "
                "Global cluster. The automatically created db will be the one of the writer db (aka the master, aka "
                "the one who created the cluster)."
            )
        if create_global_database and existing_global_database_id is not None:
            raise UserErrors(
                "If you want to create a new global database, then you can't input the id of a "
                "pre-existing one to use."
            )
        if restore_from_snapshot and existing_global_database_id is not None:
            raise UserErrors(
                "You can't attach to existing global database and restore from snapshot. It's one or the other."
            )
        super(AwsPostgresProcessor, self).process(module_idx)
