#! python3  # noqa: E265


"""
Name:         TabSettings
Purpose:      Tab containing settings widgets in DicoGIS Notebook.

Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from os import environ, getenv
from pathlib import Path
from webbrowser import open_new_tab

# project
from dicogis.__about__ import __uri_homepage__
from dicogis.ui.qt_compat import uic
from dicogis.ui.qt_compat.QtCore import Qt
from dicogis.ui.qt_compat.QtWidgets import QApplication, QStyleFactory, QWidget
from dicogis.utils.str2bool import str2bool
from dicogis.utils.utils import Utilities


# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class TabSettings(QWidget):
    """Tab form for end-user settings.

    Args:
        QWidget: inherited Qt widget
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        """Initializes UI tab for end-user options.

        Args:
            parent: Qt parent widget
        """
        super().__init__(parent)
        uic.loadUi(
            Utilities().resolve_internal_path(
                internal_path=Path("ui/wdg_tab_settings.ui")
            ),
            self,
        )

        self._init_interface_options()
        self._init_export_options()
        self._init_env_vars()

        self.retranslate_ui()

    def _init_interface_options(self) -> None:
        """Populate and wire the interface style combobox."""
        self.cbb_ui_style.addItems(QStyleFactory.keys())
        current_style = getenv("DICOGIS_UI_STYLE") or self.style().objectName()
        style_idx = self.cbb_ui_style.findText(current_style)
        if style_idx < 0:
            style_idx = next(
                (
                    i
                    for i in range(self.cbb_ui_style.count())
                    if self.cbb_ui_style.itemText(i).lower() == current_style.lower()
                ),
                -1,
            )
        if style_idx >= 0:
            self.cbb_ui_style.setCurrentIndex(style_idx)
        self.cbb_ui_style.currentTextChanged.connect(self.apply_ui_style)

    def _init_export_options(self) -> None:
        """Seed the export/general options from environment variables."""
        self.btn_toggle_export.toggled.connect(self._update_toggle_arrows)

        self.cbx_export_size_prettify.setChecked(
            str2bool(getenv("DICOGIS_EXPORT_SIZE_PRETTIFY", "True"))
        )
        self.cbx_export_raw_path.setChecked(
            str2bool(getenv("DICOGIS_EXPORT_RAW_PATH", "False"))
        )
        self.cbx_quick_fail.setChecked(str2bool(getenv("DICOGIS_QUICK_FAIL", "False")))
        self.cbx_end_process_notification_sound.setChecked(
            str2bool(getenv("DICOGIS_ENABLE_NOTIFICATION_SOUND", "True"))
        )
        self.cbx_debug.setChecked(str2bool(getenv("DICOGIS_DEBUG", "False")))
        self.cbx_debug.toggled.connect(self.apply_debug_logging)
        self.cbx_parallel_scan.setChecked(
            str2bool(getenv("DICOGIS_LISTING_PARALLEL_SCAN", "False"))
        )
        env_max_workers = getenv("DICOGIS_LISTING_MAX_WORKERS", "")
        self.sbx_max_workers.setValue(
            int(env_max_workers) if env_max_workers.isdigit() else 0
        )

    def _init_env_vars(self) -> None:
        """List the DicoGIS environment variables and link to their documentation."""
        self.btn_toggle_env_vars.toggled.connect(self._update_toggle_arrows)

        self.btn_doc_env_vars.clicked.connect(
            lambda: open_new_tab(
                f"{__uri_homepage__}usage/settings.html#using-environment-variables"
            )
        )

        dicogis_env_vars = {
            env_var: value
            for env_var, value in environ.items()
            if env_var.startswith("DICOGIS_")
        }
        if nb_dicogis_envvars := len(dicogis_env_vars):
            logger.debug(
                f"{nb_dicogis_envvars} environment variables related to DicoGIS: "
            )
            for var_name, var_value in dicogis_env_vars.items():
                logger.debug(f"{var_name}={var_value}")
                self.wdg_env_vars.add_row(var_name, var_value)

    def _update_toggle_arrows(self) -> None:
        """Point the arrow of each collapsible section button down when expanded.

        Showing/hiding the sections is connected in the .ui file: the arrow type
        isn't a slot, so it can't be.
        """
        for btn_toggle in (self.btn_toggle_export, self.btn_toggle_env_vars):
            btn_toggle.setArrowType(
                Qt.ArrowType.DownArrow
                if btn_toggle.isChecked()
                else Qt.ArrowType.RightArrow
            )

    # -- Live-apply handlers ---------------------------------------------------------

    def apply_ui_style(self, style_name: str) -> None:
        """Apply the selected Qt style immediately to the running application.

        Args:
            style_name: name of a Qt style, as listed by QStyleFactory.keys().
        """
        if app := QApplication.instance():
            app.setStyle(style_name)

    def apply_debug_logging(self, enabled: bool) -> None:
        """Toggle root logger verbosity immediately.

        Args:
            enabled: whether debug (verbose) logging should be enabled.
        """
        level = logging.DEBUG if enabled else logging.INFO
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setLevel(level)

    # -- Accessors used by OptionsManager -------------------------------------------

    def get_proxy_settings(self) -> dict:
        """Return proxy settings as a dict."""
        return {
            "proxy_needed": self.grp_proxy.isChecked(),
            "proxy_type": self.cbx_ntlm.isChecked(),
            "proxy_server": self.lne_proxy_host.text(),
            "proxy_port": self.sbx_proxy_port.value(),
            "proxy_user": self.lne_proxy_user.text(),
        }

    def set_proxy_settings(self, values: dict) -> None:
        """Apply proxy settings from a dict."""
        self.grp_proxy.setChecked(bool(str2bool(values.get("proxy_needed", False))))
        self.cbx_ntlm.setChecked(bool(str2bool(values.get("proxy_type", False))))
        if server := values.get("proxy_server"):
            self.lne_proxy_host.setText(server)
        if port := values.get("proxy_port"):
            self.sbx_proxy_port.setValue(int(port))
        if user := values.get("proxy_user"):
            self.lne_proxy_user.setText(user)

    def get_export_options(self) -> dict:
        """Return export/general options as a dict."""
        return {
            "export_prettify_size": self.cbx_export_size_prettify.isChecked(),
            "export_raw_path": self.cbx_export_raw_path.isChecked(),
            "quick_fail": self.cbx_quick_fail.isChecked(),
            "notification_sound": self.cbx_end_process_notification_sound.isChecked(),
            "debug": self.cbx_debug.isChecked(),
            "listing_parallel_scan": self.cbx_parallel_scan.isChecked(),
            "listing_max_workers": self.sbx_max_workers.value(),
        }

    def set_export_options(self, values: dict) -> None:
        """Apply export/general options from a dict."""
        if "export_prettify_size" in values:
            self.cbx_export_size_prettify.setChecked(
                bool(str2bool(values["export_prettify_size"]))
            )
        if "export_raw_path" in values:
            self.cbx_export_raw_path.setChecked(
                bool(str2bool(values["export_raw_path"]))
            )
        if "quick_fail" in values:
            self.cbx_quick_fail.setChecked(bool(str2bool(values["quick_fail"])))
        if "notification_sound" in values:
            self.cbx_end_process_notification_sound.setChecked(
                bool(str2bool(values["notification_sound"]))
            )
        if "debug" in values:
            self.cbx_debug.setChecked(bool(str2bool(values["debug"])))
        if "listing_parallel_scan" in values:
            self.cbx_parallel_scan.setChecked(
                bool(str2bool(values["listing_parallel_scan"]))
            )
        if "listing_max_workers" in values:
            self.sbx_max_workers.setValue(int(values["listing_max_workers"]))

    def get_listing_scan_kwargs(self) -> dict:
        """Return parallel_scan/max_workers kwargs ready for
        find_geodata_files() (translating the spinbox's 0 = 'Auto' into the
        None that find_geodata_files() expects)."""
        max_workers = self.sbx_max_workers.value()
        return {
            "parallel_scan": self.cbx_parallel_scan.isChecked(),
            "max_workers": max_workers if max_workers > 0 else None,
        }

    def get_ui_options(self) -> dict:
        """Return interface options as a dict."""
        return {"style": self.cbb_ui_style.currentText()}

    def set_ui_options(self, values: dict) -> None:
        """Apply interface options from a dict."""
        if style := values.get("style"):
            idx = self.cbb_ui_style.findText(style)
            if idx >= 0:
                self.cbb_ui_style.setCurrentIndex(idx)

    def retranslate_ui(self) -> None:
        """Update widgets texts for the currently active language."""
        self.grp_interface.setTitle(self.tr("Interface"))
        self.lbl_ui_style.setText(self.tr("Interface style:"))
        self.grp_proxy.setTitle(self.tr("Proxy settings"))
        self.lbl_proxy_host.setText(self.tr("Server: "))
        self.lbl_proxy_port.setText(self.tr("Port: "))
        self.lbl_proxy_user.setText(self.tr("User: "))
        self.lbl_proxy_password.setText(self.tr("Password: "))
        self.btn_toggle_export.setText(self.tr("Export"))
        self.cbx_export_size_prettify.setText(self.tr("Export: prettify files size"))
        self.cbx_export_raw_path.setText(self.tr("Export: raw path"))
        self.cbx_quick_fail.setText(self.tr("Quick fail"))
        self.cbx_end_process_notification_sound.setText(
            self.tr("Play a notification sound when processing has finished.")
        )
        self.cbx_debug.setText(self.tr("Enable verbose (debug) logging"))
        self.cbx_parallel_scan.setText(
            self.tr(
                "Parallelize folder scan (recommended only for network-mounted / "
                "high-latency storage; can be slower on local/fast storage)"
            )
        )
        self.lbl_max_workers.setText(self.tr("Parallel scan: max workers (0 = auto)"))
        self.sbx_max_workers.setSpecialValueText(self.tr("Auto"))
        self.btn_toggle_env_vars.setText(self.tr("Environment variables"))
        self.btn_doc_env_vars.setText(self.tr("See supported variables"))


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    import sys

    from dicogis.ui.qt_compat.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = TabSettings()
    widget.show()
    sys.exit(app.exec())
