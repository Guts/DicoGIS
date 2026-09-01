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
from dicogis.cli.cmd_publish import PublishReport
from dicogis.ui.wdg_tab_publish import TabPublish


# #############################################################################
# ########## Tests ##################
# ##################################


def test_tab_publish_accessors_round_trip(qtbot, tmp_path):
    widget = TabPublish()
    qtbot.addWidget(widget)

    widget.set_input_folder(str(tmp_path))
    widget.ent_udata_api_url_base.setText("https://udata-test.example/api/")
    widget.ent_udata_api_version.setText("2")
    widget.ent_udata_api_key.setText("fake-api-key")
    widget.ent_udata_organization_id.setText("some-org-id")

    assert widget.get_input_folder() == str(tmp_path)
    assert widget.get_udata_api_url_base() == "https://udata-test.example/api/"
    assert widget.get_udata_api_version() == "2"
    assert widget.get_udata_api_key() == "fake-api-key"
    assert widget.get_udata_organization_id() == "some-org-id"


def test_tab_publish_organization_id_empty_is_none(qtbot):
    widget = TabPublish()
    qtbot.addWidget(widget)

    widget.ent_udata_organization_id.setText("")
    assert widget.get_udata_organization_id() is None


def test_tab_publish_options_do_not_include_api_key(qtbot, tmp_path):
    widget = TabPublish()
    qtbot.addWidget(widget)

    widget.set_input_folder(str(tmp_path))
    widget.ent_udata_api_key.setText("super-secret-key")

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


def test_tab_publish_show_report_and_clear_report(qtbot):
    widget = TabPublish()
    qtbot.addWidget(widget)

    report = PublishReport(published=1, ignored=1, failed=1, errors=["boom"])
    widget.show_report(report)

    assert widget.lbl_publish_summary.text()
    assert widget.tab_publish_errors.table.rowCount() == 1

    widget.clear_report()

    assert widget.lbl_publish_summary.text() == ""
    assert widget.tab_publish_errors.table.rowCount() == 0
