#! python3  # noqa: E265


"""
Name:         Options Manager
Purpose:      Load & save settings of a parent module

Author:       Julien Moura (@geojulien)
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import configparser
import logging
import platform
from os import path
from pathlib import Path

from dicogis.utils.str2bool import str2bool

# #############################################################################
# ############ Classes #############
# ##################################


class OptionsManager:
    def __init__(self, confile: str = r"..\..\options.ini"):
        """
        Main window constructor
        Creates 1 frame and 2 labelled subframes
        """
        self.confile = path.realpath(confile)
        # first use or not
        if not path.isfile(self.confile):
            logging.info("No options.ini file found. First use: welcome!")
            self.first_use = 1
        else:
            logging.info("Options.ini file found. ")
            self.first_use = 0

        # using safe parser
        self.config = configparser.ConfigParser()
        self.config.read(confile)

    def load_settings(self, parent) -> None:
        """load settings from last execution"""
        # basics
        parent.set_selected_language(self.config.get("basics", "def_codelang"))
        parent.tab_files.listing_initial_folder_path = Path(
            self.config.get("basics", "def_rep")
        )
        parent.set_active_tab_index(int(self.config.get("basics", "def_tab")))
        parent.tab_options.set_export_options(
            {
                "export_prettify_size": self.config.get(
                    "basics", "export_prettify_size"
                ),
                "export_raw_path": self.config.get("basics", "export_raw_path"),
                "quick_fail": self.config.get("basics", "quick_fail"),
                "notification_sound": self.config.get("basics", "notification_sound"),
                "debug": self.config.get("basics", "debug", fallback="False"),
            }
        )

        # interface settings
        parent.tab_options.set_ui_options(
            {"style": self.config.get("ui", "style", fallback="")}
        )

        # filters
        parent.tab_files.set_filters_state(dict(self.config.items("filters")))

        # database settings
        last_used_pg_service = self.config.get("database", "last_used_pg_service")
        parent.tab_sgbd.set_selected_pg_service(last_used_pg_service)
        parent.tab_sgbd.set_views_enabled(
            bool(str2bool(self.config.get("database", "opt_views")))
        )

        # proxy settings
        parent.tab_options.set_proxy_settings(dict(self.config.items("proxy")))

        # log
        logging.info("Last options loaded")

    def save_settings(self, parent) -> bool:
        """save last options in order to make the next excution more easy"""

        # add sections
        if self.first_use:
            self.config.add_section("config")
            self.config.add_section("basics")
            self.config.add_section("filters")
            self.config.add_section("database")
            self.config.add_section("proxy")

        # backward compatibility: older options.ini files predate the "ui" section
        if not self.config.has_section("ui"):
            self.config.add_section("ui")

        # config
        self.config.set("config", "DicoGIS_version", parent.package_about.__version__)
        self.config.set("config", "OS", platform.platform())

        # basics
        self.config.set("basics", "def_codelang", parent.get_selected_language())
        target_path = parent.tab_files.get_target_path()
        if target_path:
            self.config.set("basics", "def_rep", target_path)
        else:
            self.config.set(
                "basics",
                "def_rep",
                str(parent.tab_files.listing_initial_folder_path.resolve()),
            )
        self.config.set("basics", "def_tab", str(parent.get_active_tab_index()))

        export_options = parent.tab_options.get_export_options()
        self.config.set(
            "basics",
            "export_prettify_size",
            str(export_options["export_prettify_size"]),
        )
        self.config.set(
            "basics", "export_raw_path", str(export_options["export_raw_path"])
        )
        self.config.set("basics", "quick_fail", str(export_options["quick_fail"]))
        self.config.set(
            "basics",
            "notification_sound",
            str(export_options["notification_sound"]),
        )
        self.config.set("basics", "debug", str(export_options["debug"]))

        # interface settings
        ui_options = parent.tab_options.get_ui_options()
        self.config.set("ui", "style", ui_options["style"])

        # filters
        for key, value in parent.tab_files.get_filters_state().items():
            self.config.set("filters", key, str(int(value)))

        # database settings
        self.config.set(
            "database",
            "last_used_pg_service",
            parent.tab_sgbd.get_selected_pg_service(),
        )
        self.config.set(
            "database", "opt_views", str(parent.tab_sgbd.get_views_enabled())
        )

        # proxy settings
        proxy_settings = parent.tab_options.get_proxy_settings()
        self.config.set("proxy", "proxy_needed", str(proxy_settings["proxy_needed"]))
        self.config.set("proxy", "proxy_type", str(proxy_settings["proxy_type"]))
        self.config.set("proxy", "proxy_server", proxy_settings["proxy_server"])
        self.config.set("proxy", "proxy_port", str(proxy_settings["proxy_port"]))
        self.config.set("proxy", "proxy_user", proxy_settings["proxy_user"])

        # Writing the configuration file
        with open(file=self.confile, mode="w", encoding="UTF-8") as configfile:
            try:
                self.config.write(configfile)
                logging.info(f"Options saved to {self.confile}")
                return True
            except Exception as err:
                logging.error(f"Options couldn't be saved because of: {err}")
                return False
