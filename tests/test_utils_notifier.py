#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest tests.test_utils_notifier
    # for specific test
    python -m unittest tests.test_utils_notifier.TestSendSystemNotify.test_title_and_message_are_applied
"""

# standard library
import unittest
from pathlib import Path
from unittest.mock import patch

# 3rd party
from notifypy import Notify

# project
from dicogis.utils import notifier


# ############################################################################
# ########## Globals #############
# ################################

BACKEND_AVAILABLE = notifier.build_notification() is not None


# ############################################################################
# ########## Functions ###########
# ################################


def send_and_capture(**kwargs) -> Notify:
    """Call send_system_notify() without touching a real OS notification backend,
    and return the notification it built.

    Args:
        **kwargs: send_system_notify() arguments

    Returns:
        the notify-py notification send_system_notify() sent
    """
    built: list[Notify] = []
    real_build_notification = notifier.build_notification

    def _build_and_keep() -> Notify | None:
        built.append(real_build_notification())
        return built[-1]

    with (
        patch.object(notifier, "build_notification", _build_and_keep),
        patch.object(Notify, "send", return_value=True),
    ):
        notifier.send_system_notify(**kwargs)

    return built[0]


# ############################################################################
# ########## Classes #############
# ################################


@unittest.skipUnless(
    BACKEND_AVAILABLE, "No supported notification backend on this platform."
)
class TestSendSystemNotify(unittest.TestCase):
    """Test send_system_notify() against real notify-py notifications, with
    their send() patched out."""

    def test_application_name_is_dicogis(self):
        """notify-py swallows unknown keyword arguments: a misspelled one left
        notifications under its default "Python Application (notify.py)"."""
        self.assertEqual(notifier.build_notification().application_name, "DicoGIS")

    def test_title_and_message_are_applied(self):
        notification = send_and_capture(
            notification_message="Hello there",
            notification_title="This is the title",
            notification_sound=False,
        )

        self.assertEqual(notification.title, "This is the title")
        self.assertEqual(notification.message, "Hello there")

    def test_sound_enabled_sets_audio_path(self):
        notification = send_and_capture(
            notification_message="msg",
            notification_title="title",
            notification_sound=True,
        )

        self.assertTrue(Path(notification.audio).is_file())

    def test_sound_disabled_after_enabled_is_silent(self):
        """Regression: a module-level notification kept the audio set by a
        previous call, so unticking the sound option had no effect until the
        application was restarted."""
        send_and_capture(notification_message="msg", notification_title="title")
        notification = send_and_capture(
            notification_message="msg",
            notification_title="title",
            notification_sound=False,
        )

        self.assertIsNone(notification.audio)

    def test_send_failure_is_caught_and_logged(self):
        with (
            patch.object(Notify, "send", side_effect=RuntimeError("boom")),
            self.assertLogs(notifier.logger, level="WARNING"),
        ):
            # should not raise despite notification.send() failing
            notifier.send_system_notify(
                notification_message="msg",
                notification_title="title",
                notification_sound=False,
            )

    def test_send_returning_false_is_logged(self):
        """notify-py reports backend failures (missing aplay, D-Bus error...)
        only through send()'s return value, which used to be ignored."""
        with (
            patch.object(Notify, "send", return_value=False),
            self.assertLogs(notifier.logger, level="WARNING") as logs,
        ):
            notifier.send_system_notify(
                notification_message="msg",
                notification_title="title",
                notification_sound=False,
            )

        self.assertIn("notifypyEnableLogging", logs.output[0])


class TestSendSystemNotifyNoBackend(unittest.TestCase):
    """send_system_notify() must degrade to a no-op, not crash, when no
    notification backend is available (e.g. notify-py's UnsupportedPlatform
    on a Windows release it doesn't recognize, such as Windows Server)."""

    def test_build_returns_none_when_notify_py_fails(self):
        with patch.object(notifier, "Notify", side_effect=RuntimeError("nope")):
            self.assertIsNone(notifier.build_notification())

    def test_skips_gracefully_without_backend(self):
        with patch.object(notifier, "build_notification", return_value=None):
            # should not raise despite there being no backend to notify with
            notifier.send_system_notify(
                notification_message="msg",
                notification_title="title",
                notification_sound=False,
            )


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
