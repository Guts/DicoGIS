#! python3

"""
Tests for the TabPublish widget (uData publication tab).

Usage from the repo root folder:
    pytest tests/ui/test_tab_publish.py
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# package
from dicogis.publishing.report import PublishReport
from dicogis.ui.wdg_tab_publish import TabPublish


# #############################################################################
# ########## Tests ##################
# ##################################


def test_tab_publish_accessors_round_trip(qtbot, tmp_path):
    widget = TabPublish()
    qtbot.addWidget(widget)

    widget.set_input_folder(str(tmp_path))
    widget.lne_udata_api_url_base.setText("https://udata-test.example/api/")
    widget.lne_udata_api_version.setText("2")
    widget.lne_udata_api_key.setText("fake-api-key")
    widget.lne_udata_organization_id.setText("some-org-id")

    assert widget.get_input_folder() == str(tmp_path)
    assert widget.get_udata_api_url_base() == "https://udata-test.example/api/"
    assert widget.get_udata_api_version() == "2"
    assert widget.get_udata_api_key() == "fake-api-key"
    assert widget.get_udata_organization_id() == "some-org-id"


def test_tab_publish_organization_id_empty_is_none(qtbot):
    widget = TabPublish()
    qtbot.addWidget(widget)

    widget.lne_udata_organization_id.setText("")
    assert widget.get_udata_organization_id() is None


def test_tab_publish_options_do_not_include_api_key(qtbot, tmp_path):
    widget = TabPublish()
    qtbot.addWidget(widget)

    widget.set_input_folder(str(tmp_path))
    widget.lne_udata_api_key.setText("super-secret-key")

    options = widget.get_publish_options()
    assert "udata_api_key" not in options
    assert "super-secret-key" not in options.values()


def test_tab_publish_set_publish_options(qtbot, tmp_path):
    widget = TabPublish()
    qtbot.addWidget(widget)

    widget.set_publish_options(
        {
            "input_folder": str(tmp_path),
            "udata_api_url_base": "https://udata-test.example/api/",
            "udata_api_version": "2",
            "udata_organization_id": "some-org-id",
        }
    )

    assert widget.get_input_folder() == str(tmp_path)
    assert widget.get_udata_api_url_base() == "https://udata-test.example/api/"
    assert widget.get_udata_api_version() == "2"
    assert widget.get_udata_organization_id() == "some-org-id"


def test_tab_publish_target_drives_the_page(qtbot):
    widget = TabPublish()
    qtbot.addWidget(widget)

    widget.set_publish_target("geonetwork")
    assert widget.get_publish_target() == "geonetwork"
    assert widget.stk_publish_target.currentWidget() is widget.wdg_page_geonetwork

    widget.cbb_publish_target.setCurrentIndex(
        widget.cbb_publish_target.findData("udata")
    )
    assert widget.stk_publish_target.currentWidget() is widget.wdg_page_udata


def test_tab_publish_unknown_target_is_ignored(qtbot):
    widget = TabPublish()
    qtbot.addWidget(widget)
    widget.set_publish_target("geonetwork")

    widget.set_publish_target("ckan")

    assert widget.get_publish_target() == "geonetwork"


def test_tab_publish_defaults_from_the_environment(qtbot, monkeypatch):
    monkeypatch.setenv("DICOGIS_PUBLISH_TARGET", "geonetwork")
    monkeypatch.setenv("DICOGIS_GEONETWORK_URL_BASE", "https://gn.example/geonetwork")
    monkeypatch.setenv("DICOGIS_GEONETWORK_PORTAL", "inspire")
    monkeypatch.setenv("DICOGIS_GEONETWORK_USERNAME", "editor")
    monkeypatch.setenv("DICOGIS_GEONETWORK_PASSWORD", "s3cret")
    monkeypatch.setenv("DICOGIS_GEONETWORK_GROUP", "2")
    monkeypatch.setenv("DICOGIS_GEONETWORK_CATEGORIES", "1, 3,")
    monkeypatch.setenv("DICOGIS_GEONETWORK_UPDATE_MODE", "complete")
    monkeypatch.setenv("DICOGIS_GEONETWORK_PUBLISH_TO_ALL", "true")
    monkeypatch.setenv("DICOGIS_GEONETWORK_REJECT_IF_INVALID", "true")

    widget = TabPublish()
    qtbot.addWidget(widget)

    assert widget.get_publish_target() == "geonetwork"
    assert widget.get_geonetwork_url_base() == "https://gn.example/geonetwork"
    assert widget.get_geonetwork_portal() == "inspire"
    assert widget.get_geonetwork_username() == "editor"
    assert widget.get_geonetwork_password() == "s3cret"
    assert widget.get_geonetwork_group() == "2"
    assert widget.get_geonetwork_categories() == ["1", "3"]
    assert widget.get_geonetwork_update_mode() == "complete"
    assert widget.cbx_geonetwork_publish_to_all.isChecked()
    assert widget.cbx_geonetwork_reject_if_invalid.isChecked()


def test_tab_publish_options_do_not_include_the_password(qtbot):
    widget = TabPublish()
    qtbot.addWidget(widget)
    widget.lne_geonetwork_password.setText("super-secret-password")

    options = widget.get_publish_options()

    assert "super-secret-password" not in options.values()
    assert not [key for key in options if "password" in key]


def test_tab_publish_authcfg_only_within_qgis(qtbot, monkeypatch):
    widget = TabPublish()
    qtbot.addWidget(widget)
    widget.lne_geonetwork_authcfg.setText("abc1234")

    assert widget.lne_geonetwork_authcfg.isHidden()
    assert widget.get_geonetwork_authcfg() is None

    monkeypatch.setattr(
        "dicogis.ui.wdg_tab_publish.qgis_application_is_running", lambda: True
    )
    in_qgis_widget = TabPublish()
    qtbot.addWidget(in_qgis_widget)
    in_qgis_widget.lne_geonetwork_authcfg.setText("abc1234")

    assert not in_qgis_widget.lne_geonetwork_authcfg.isHidden()
    assert in_qgis_widget.get_geonetwork_authcfg() == "abc1234"


def test_tab_publish_report_details(qtbot):
    widget = TabPublish()
    qtbot.addWidget(widget)

    widget.show_report(
        PublishReport(
            published=1,
            up_to_date=2,
            errors=["boom"],
            added_fields={"a.xml": ["abstract", "keywords"]},
        )
    )

    table = widget.wdg_publish_errors.tbw_content
    assert "2" in widget.lbl_publish_summary.text()
    assert table.rowCount() == 2
    assert table.item(0, 0).text() == "a.xml"
    assert "abstract, keywords" in table.item(0, 1).text()
    assert table.item(1, 1).text() == "boom"


def test_tab_publish_show_report_and_clear_report(qtbot):
    widget = TabPublish()
    qtbot.addWidget(widget)

    report = PublishReport(published=1, ignored=1, failed=1, errors=["boom"])
    widget.show_report(report)

    assert widget.lbl_publish_summary.text()
    assert widget.wdg_publish_errors.tbw_content.rowCount() == 1

    widget.clear_report()

    assert widget.lbl_publish_summary.text() == ""
    assert widget.wdg_publish_errors.tbw_content.rowCount() == 0
