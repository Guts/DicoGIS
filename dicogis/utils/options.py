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

    def load_settings(self, parent):
        """load settings from last execution"""
        # basics
        parent.def_lang = self.config.get("basics", "def_codelang")
        parent.tab_files.listing_initial_folder_path = Path(
            self.config.get("basics", "def_rep")
        )
        parent.nb.select(self.config.get("basics", "def_tab"))
        # filters
        parent.tab_files.opt_shp.set(self.config.get("filters", "opt_shp"))
        parent.tab_files.opt_tab.set(self.config.get("filters", "opt_tab"))
        parent.tab_files.opt_kml.set(self.config.get("filters", "opt_kml"))
        parent.tab_files.opt_gml.set(self.config.get("filters", "opt_gml"))
        parent.tab_files.opt_geoj.set(self.config.get("filters", "opt_geoj"))
        parent.tab_files.opt_gxt.set(self.config.get("filters", "opt_gxt"))
        parent.tab_files.opt_rast.set(self.config.get("filters", "opt_rast"))
        parent.tab_files.opt_egdb.set(self.config.get("filters", "opt_egdb"))
        parent.tab_files.opt_spadb.set(self.config.get("filters", "opt_spadb"))
        parent.tab_files.opt_dxf.set(self.config.get("filters", "opt_dxf"))

        # database settings
        last_used_pg_service = self.config.get("database", "last_used_pg_service")
        if last_used_pg_service in parent.tab_sgbd.ddl_pg_services["values"]:
            parent.tab_sgbd.ddl_pg_services.set(
                self.config.get("database", "last_used_pg_service")
            )
        parent.tab_sgbd.opt_pg_views.set(self.config.get("database", "opt_views"))

        # proxy settings
        parent.tab_options.opt_proxy.set(self.config.get("proxy", "proxy_needed"))
        parent.tab_options.opt_ntlm.set(self.config.get("proxy", "proxy_type"))
        parent.tab_options.prox_server.set(self.config.get("proxy", "proxy_server"))
        parent.tab_options.prox_port.set(self.config.get("proxy", "proxy_port"))
        parent.tab_options.prox_user.set(self.config.get("proxy", "proxy_user"))

        # log
        logging.info("Last options loaded")

    def save_settings(self, parent):
        """save last options in order to make the next excution more easy"""

        # add sections
        if self.first_use:
            self.config.add_section("config")
            self.config.add_section("basics")
            self.config.add_section("filters")
            self.config.add_section("database")
            self.config.add_section("proxy")

        # config
        self.config.set("config", "DicoGIS_version", parent.package_about.__version__)
        self.config.set("config", "OS", platform.platform())

        # basics
        self.config.set("basics", "def_codelang", parent.ddl_lang.get())
        if parent.tab_files.target_path.get():
            self.config.set("basics", "def_rep", parent.tab_files.target_path.get())
        else:
            self.config.set(
                "basics",
                "def_rep",
                str(parent.tab_files.listing_initial_folder_path.resolve()),
            )
        self.config.set("basics", "def_tab", str(parent.nb.index(parent.nb.select())))
        self.config.set(
            "basics",
            "export_prettify_size",
            str(parent.tab_options.opt_export_size_prettify),
        )
        self.config.set(
            "basics",
            "export_raw_path",
            str(parent.tab_options.opt_export_raw_path),
        )
        self.config.set(
            "basics",
            "quick_fail",
            str(parent.tab_options.opt_quick_fail),
        )
        self.config.set(
            "basics",
            "notification_sound",
            str(parent.tab_options.opt_end_process_notification_sound),
        )

        # filters
        self.config.set("filters", "opt_shp", str(parent.tab_files.opt_shp.get()))
        self.config.set("filters", "opt_tab", str(parent.tab_files.opt_tab.get()))
        self.config.set("filters", "opt_kml", str(parent.tab_files.opt_kml.get()))
        self.config.set("filters", "opt_gml", str(parent.tab_files.opt_gml.get()))
        self.config.set("filters", "opt_geoj", str(parent.tab_files.opt_geoj.get()))
        self.config.set("filters", "opt_gxt", str(parent.tab_files.opt_gxt.get()))
        self.config.set("filters", "opt_rast", str(parent.tab_files.opt_rast.get()))
        self.config.set("filters", "opt_egdb", str(parent.tab_files.opt_egdb.get()))
        self.config.set("filters", "opt_spadb", str(parent.tab_files.opt_spadb.get()))
        self.config.set("filters", "opt_dxf", str(parent.tab_files.opt_dxf.get()))

        # database settings
        self.config.set(
            "database", "last_used_pg_service", parent.tab_sgbd.ddl_pg_services.get()
        )
        self.config.set(
            "database", "opt_views", str(parent.tab_sgbd.opt_pg_views.get())
        )

        # proxy settings
        self.config.set(
            "proxy", "proxy_needed", str(parent.tab_options.opt_proxy.get())
        )
        self.config.set("proxy", "proxy_type", str(parent.tab_options.opt_ntlm.get()))
        self.config.set("proxy", "proxy_server", parent.tab_options.prox_server.get())
        self.config.set("proxy", "proxy_port", str(parent.tab_options.prox_port.get()))
        self.config.set("proxy", "proxy_user", parent.tab_options.prox_user.get())

        # Writing the configuration file
        with open(file=self.confile, mode="w", encoding="UTF-8") as configfile:
            try:
                self.config.write(configfile)
                logging.info(f"Options saved to {self.confile}")
                return True
            except Exception as err:
                logging.error(f"Options couldn't be saved because of: {err}")
                return False
