import json
import os
import platform
import shutil
from logging import DEBUG, Handler, LogRecord
from typing import TYPE_CHECKING, List

from opta.constants import VERSION
from opta.utils import SensitiveFormatter, ansi_scrub, logger

# from opta.core.terraform import Terraform
if TYPE_CHECKING:
    from opta.layer import Layer


class CrashReporter:
    def __init__(self) -> None:
        self.log_lines: List[str] = []
        self.opta_yaml = ""
        self.opta_parent_yaml = ""
        self.tf_plan_text = ""
        self.metadata = {
            "opta_version": VERSION,
            "platform": platform.system(),
            "os_name": os.name,
            "os_version": platform.version(),
        }

    def set_layer(self, layer: "Layer") -> None:
        self.opta_yaml = layer.original_spec
        if layer.parent is not None:
            self.opta_parent_yaml = layer.parent.original_spec

    def generate_report(self) -> None:
        report_path = ".opta_crash_report"
        if os.path.exists(report_path):
            shutil.rmtree(report_path)
        os.mkdir(report_path)

        log_file = f"{report_path}/opta_logs.txt"
        with open(log_file, "w") as f:
            f.write("\n".join(self.log_lines))

        metadata_file = f"{report_path}/metadata.json"
        with open(metadata_file, "w") as f:
            f.write(json.dumps(self.metadata, indent=2))

        if self.tf_plan_text != "":
            tfplan_file = f"{report_path}/tfplan"
            with open(tfplan_file, "w") as f:
                f.write(SensitiveFormatter.filter(self.tf_plan_text))

        if self.opta_yaml != "":
            opta_file = f"{report_path}/opta.yaml"
            with open(opta_file, "w") as f:
                f.write(SensitiveFormatter.filter(self.opta_yaml))

        if self.opta_parent_yaml != "":
            opta_parent_file = f"{report_path}/opta_parent.yaml"
            with open(opta_parent_file, "w") as f:
                f.write(SensitiveFormatter.filter(self.opta_parent_yaml))

        shutil.make_archive("opta_crash_report", "zip", report_path)
        shutil.rmtree(report_path)


class ListHandler(Handler):  # Inherit from logging.Handler
    def __init__(self, log_list: List[str]):
        # run the regular Handler __init__
        Handler.__init__(self)
        # Our custom argument
        self.log_list = log_list

    def emit(self, record: LogRecord) -> None:
        msg = self.format(record)
        self.log_list.append(ansi_scrub(msg))


CURRENT_CRASH_REPORTER = CrashReporter()
crash_report_handler = ListHandler(CURRENT_CRASH_REPORTER.log_lines)
crash_report_handler.setLevel(DEBUG)
crash_report_handler.setFormatter(SensitiveFormatter())
logger.addHandler(crash_report_handler)
