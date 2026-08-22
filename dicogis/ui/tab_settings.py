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
from webbrowser import open_new_tab

# 3rd party
from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

# project
from dicogis.__about__ import __uri_homepage__
from dicogis.ui.collapsible_frame import ToggledFrame
from dicogis.ui.scrollable_table import ScrollableTable
from dicogis.utils.str2bool import str2bool
from dicogis.utils.texts import TextsManager

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
        localized_strings: dict | None = None,
        init_widgets: bool = True,
    ):
        """Initializes UI tab for end-user options.

        Args:
            parent: Qt parent widget
            localized_strings: translated strings. Defaults to None.
            init_widgets: option to create widgets during init or not. Defaults to True.
        """
        super().__init__(parent)

        # handle empty localized strings
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

        if init_widgets:
            self.create_widgets()

    def create_widgets(self) -> None:
        """Create and layout the widgets for the frame."""
        layout = QVBoxLayout(self)

        # -- NETWORK OPTIONS -----------------------------------------------------------
        self.FrOptProxy = QGroupBox(
            self.localized_strings.get("Proxy", "Proxy settings"), self
        )
        self.FrOptProxy.setCheckable(True)
        self.FrOptProxy.setChecked(False)
        self.FrOptProxy.toggled.connect(self.FrOptProxy.setEnabled)
        self.FrOptProxy.setEnabled(False)

        proxy_layout = QFormLayout()
        self.opt_ntlm = QCheckBox("NTLM", self.FrOptProxy)
        self.prox_ent_host = QLineEdit(self.FrOptProxy)
        self.prox_ent_host.setText("proxy.server.com")
        self.prox_ent_port = QSpinBox(self.FrOptProxy)
        self.prox_ent_port.setRange(1, 65535)
        self.prox_ent_port.setValue(80)
        self.prox_ent_user = QLineEdit(self.FrOptProxy)
        self.prox_ent_user.setText("proxy_user")
        self.prox_ent_password = QLineEdit(self.FrOptProxy)
        self.prox_ent_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.prox_lb_host = QLabel(
            self.localized_strings.get("gui_prox_server", "Host:"), self.FrOptProxy
        )
        self.prox_lb_port = QLabel(
            self.localized_strings.get("gui_port", "Port:"), self.FrOptProxy
        )
        self.prox_lb_user = QLabel(
            self.localized_strings.get("gui_user", "User name:"), self.FrOptProxy
        )
        self.prox_lb_password = QLabel(
            self.localized_strings.get("gui_mdp", "User password:"), self.FrOptProxy
        )

        proxy_layout.addRow(self.prox_lb_host, self.prox_ent_host)
        proxy_layout.addRow(self.prox_lb_port, self.prox_ent_port)
        proxy_layout.addRow(self.opt_ntlm)
        proxy_layout.addRow(self.prox_lb_user, self.prox_ent_user)
        proxy_layout.addRow(self.prox_lb_password, self.prox_ent_password)
        self.FrOptProxy.setLayout(proxy_layout)

        # -- EXPORT / GENERAL OPTIONS ---------------------------------------------------
        self.FrOptExport = ToggledFrame(
            self,
            in_text=self.localized_strings.get("Export", "Export"),
            start_opened=False,
        )
        export_layout = QVBoxLayout()

        self.opt_export_size_prettify = QCheckBox(
            self.localized_strings.get(
                "gui_options_export_size_prettify", "Export: prettify files size"
            ),
            self.FrOptExport.sub_frame,
        )
        self.opt_export_size_prettify.setChecked(
            str2bool(getenv("DICOGIS_EXPORT_SIZE_PRETTIFY", "True"))
        )
        export_layout.addWidget(self.opt_export_size_prettify)

        self.opt_export_raw_path = QCheckBox(
            self.localized_strings.get(
                "gui_options_export_raw_path", "Export: raw path"
            ),
            self.FrOptExport.sub_frame,
        )
        self.opt_export_raw_path.setChecked(
            str2bool(getenv("DICOGIS_EXPORT_RAW_PATH", "False"))
        )
        export_layout.addWidget(self.opt_export_raw_path)

        self.opt_quick_fail = QCheckBox(
            self.localized_strings.get("gui_options_quick_fail", "Quick fail"),
            self.FrOptExport.sub_frame,
        )
        self.opt_quick_fail.setChecked(str2bool(getenv("DICOGIS_QUICK_FAIL", "False")))
        export_layout.addWidget(self.opt_quick_fail)

        self.opt_end_process_notification_sound = QCheckBox(
            self.localized_strings.get(
                "gui_options_notification_sound",
                "Play a notification sound when processing has finished.",
            ),
            self.FrOptExport.sub_frame,
        )
        self.opt_end_process_notification_sound.setChecked(
            str2bool(getenv("DICOGIS_ENABLE_NOTIFICATION_SOUND", "True"))
        )
        export_layout.addWidget(self.opt_end_process_notification_sound)
        self.FrOptExport.sub_frame.setLayout(export_layout)

        # -- Environment variables --
        self.FrOptEnv = ToggledFrame(
            self,
            in_text=self.localized_strings.get(
                "environment_variables", "Environment variables"
            ),
            start_opened=False,
        )
        env_layout = QVBoxLayout()

        btn_doc_env_vars = QPushButton(
            self.localized_strings.get(
                "gui_options_supported_env_vars", "See supported variables"
            ),
            self.FrOptEnv.sub_frame,
        )
        btn_doc_env_vars.clicked.connect(
            lambda: open_new_tab(
                f"{__uri_homepage__}usage/settings.html#using-environment-variables"
            )
        )

        self.tab_env_vars = ScrollableTable(self.FrOptEnv.sub_frame)
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
                self.tab_env_vars.add_row(var_name, var_value)

        env_layout.addWidget(btn_doc_env_vars)
        env_layout.addWidget(self.tab_env_vars)
        self.FrOptEnv.sub_frame.setLayout(env_layout)

        # positionning frames
        layout.addWidget(self.FrOptProxy)
        layout.addWidget(self.FrOptExport)
        layout.addWidget(self.FrOptEnv)
        layout.addStretch(1)

    # -- Accessors used by OptionsManager -------------------------------------------

    def get_proxy_settings(self) -> dict:
        """Return proxy settings as a dict."""
        return {
            "proxy_needed": self.FrOptProxy.isChecked(),
            "proxy_type": self.opt_ntlm.isChecked(),
            "proxy_server": self.prox_ent_host.text(),
            "proxy_port": self.prox_ent_port.value(),
            "proxy_user": self.prox_ent_user.text(),
        }

    def set_proxy_settings(self, values: dict) -> None:
        """Apply proxy settings from a dict."""
        self.FrOptProxy.setChecked(bool(str2bool(values.get("proxy_needed", False))))
        self.opt_ntlm.setChecked(bool(str2bool(values.get("proxy_type", False))))
        if server := values.get("proxy_server"):
            self.prox_ent_host.setText(server)
        if port := values.get("proxy_port"):
            self.prox_ent_port.setValue(int(port))
        if user := values.get("proxy_user"):
            self.prox_ent_user.setText(user)

    def get_export_options(self) -> dict:
        """Return export/general options as a dict."""
        return {
            "export_prettify_size": self.opt_export_size_prettify.isChecked(),
            "export_raw_path": self.opt_export_raw_path.isChecked(),
            "quick_fail": self.opt_quick_fail.isChecked(),
            "notification_sound": self.opt_end_process_notification_sound.isChecked(),
        }

    def set_export_options(self, values: dict) -> None:
        """Apply export/general options from a dict."""
        if "export_prettify_size" in values:
            self.opt_export_size_prettify.setChecked(
                bool(str2bool(values["export_prettify_size"]))
            )
        if "export_raw_path" in values:
            self.opt_export_raw_path.setChecked(
                bool(str2bool(values["export_raw_path"]))
            )
        if "quick_fail" in values:
            self.opt_quick_fail.setChecked(bool(str2bool(values["quick_fail"])))
        if "notification_sound" in values:
            self.opt_end_process_notification_sound.setChecked(
                bool(str2bool(values["notification_sound"]))
            )

    def retranslate_ui(self, localized_strings: dict) -> None:
        """Update widgets texts with the given localized strings.

        Args:
            localized_strings: translated strings.
        """
        self.localized_strings = localized_strings
        self.FrOptProxy.setTitle(localized_strings.get("Proxy", "Proxy settings"))
        self.prox_lb_host.setText(localized_strings.get("gui_prox_server", "Host:"))
        self.prox_lb_port.setText(localized_strings.get("gui_port", "Port:"))
        self.prox_lb_user.setText(localized_strings.get("gui_user", "User name:"))
        self.prox_lb_password.setText(
            localized_strings.get("gui_mdp", "User password:")
        )
        self.FrOptExport.btn_toggle.setText(
            localized_strings.get("Export", "Export")
        )
        self.FrOptEnv.btn_toggle.setText(
            localized_strings.get(
                "environment_variables", "Environment variables"
            )
        )


# #############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """To test"""
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = TabSettings()
    widget.show()
    sys.exit(app.exec())
