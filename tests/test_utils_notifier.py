#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash
    # for whole tests
    python -m unittest tests.test_utils_notifier
    # for specific test
    python -m unittest tests.test_utils_notifier.TestSendSystemNotify.test_message_is_set
"""

# standard library
import unittest
from unittest.mock import patch

# project
from dicogis.utils import notifier

# ############################################################################
# ########## Classes #############
# ################################


class TestSendSystemNotify(unittest.TestCase):
    """Test send_system_notify().

    ``notifier.notification`` is a module-level singleton (not rebuilt per
    call), so every test patches its ``.send`` method to avoid touching a
    real OS notification backend, and explicitly sets/reads its state
    rather than assuming any particular starting point.
    """

    def test_message_is_set(self):
        with patch.object(notifier.notification, "send"):
            notifier.send_system_notify(
                notification_message="Hello there",
                notification_title="A title",
                notification_sound=False,
            )

        self.assertEqual(notifier.notification.message, "Hello there")

    def test_known_bug_title_is_never_applied_to_the_notification(self):
        """Document a pre-existing bug: notification_title is accepted as a
        parameter but notification.title is never assigned from it anywhere
        in send_system_notify -- every notification is shown under
        whatever title the Notify() singleton started with (its notifypy
        default, since dicogis.utils.notifier doesn't pass
        default_notification_title either), regardless of the title
        callers pass in.
        """
        with patch.object(notifier.notification, "send"):
            notifier.send_system_notify(
                notification_message="Hello there",
                notification_title="This should be the title but never is",
                notification_sound=False,
            )

        self.assertNotEqual(
            notifier.notification.title, "This should be the title but never is"
        )

    def test_sound_enabled_sets_audio_path(self):
        with patch.object(notifier.notification, "send"):
            notifier.send_system_notify(
                notification_message="msg",
                notification_title="title",
                notification_sound=True,
            )

        self.assertTrue(notifier.notification.audio)

    def test_sound_disabled_does_not_touch_audio(self):
        with patch.object(notifier.notification, "send"):
            audio_before = notifier.notification.audio
            notifier.send_system_notify(
                notification_message="msg",
                notification_title="title",
                notification_sound=False,
            )

        self.assertEqual(notifier.notification.audio, audio_before)

    def test_send_failure_is_caught_and_logged(self):
        with patch.object(
            notifier.notification, "send", side_effect=RuntimeError("boom")
        ):
            # should not raise despite notification.send() failing
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
