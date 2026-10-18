#! python3  # noqa: E265


# ##############################################################################
# ########## Libraries #############
# ##################################


# standard library
import logging

# 3rd party
from notifypy import Notify

# package
from dicogis.__about__ import __icon_path__, __notification_sound_path__, __title__
from dicogis.utils.utils import Utilities


# ##############################################################################
# ############ Globals ############
# #################################


# LOG
logger = logging.getLogger(__name__)

dicogis_utils = Utilities()


# ##############################################################################
# ############ Functions ##########
# #################################


def build_notification() -> Notify | None:
    """Build a notify-py notification with DicoGIS defaults (name, icon).

    A new one per notification, rather than a module-level one: options such as
    the sound would otherwise carry over from one notification to the next.

    Returns:
        notification, or None if no notification backend is available
    """
    try:
        return Notify(
            default_notification_application_name=__title__,
            default_notification_icon=dicogis_utils.resolve_internal_path(
                internal_path=__icon_path__
            ),
        )
    except Exception as err:
        # e.g. notify-py raises UnsupportedPlatform on Windows releases it doesn't
        # recognize (Windows Server editions): degrade to a no-op rather than
        # crashing at the end of a run.
        logger.warning(
            f"System notifications are unavailable on this platform. Trace: {err}"
        )
        return None


def send_system_notify(
    notification_message: str, notification_title: str, notification_sound: bool = True
) -> None:
    """Send a notification to the system.

    Args:
        notification_message: notification message
        notification_title: notification title
        notification_sound: play the DicoGIS notification sound. Defaults to True.
    """
    notification = build_notification()
    if notification is None:
        logger.info(
            "Notification skipped (unavailable on this platform): "
            f"{notification_title=}: {notification_message=}"
        )
        return

    notification.title = notification_title
    notification.message = notification_message
    if notification_sound:
        notification.audio = str(
            dicogis_utils.resolve_internal_path(
                internal_path=__notification_sound_path__
            ).resolve()
        )

    logger.debug(
        f"Sending notification: {notification_title=}: {notification_message=}, "
        f"audio={notification.audio}"
    )
    try:
        # notify-py catches the backend errors itself (in its own thread, with its
        # logging disabled): a failure mostly shows up as a False return value
        sent = notification.send()
    except Exception as err:
        logger.warning(f"Sending a system notification failed. Trace: {err}")
        return
    if not sent:
        logger.warning(
            "Sending a system notification failed. To get the reason, run again "
            "with the notifypyEnableLogging environment variable set (e.g. to 1): "
            "notify-py then prints its own trace to the console."
        )
