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

# common notification information
dicogis_utils = Utilities()
try:
    notification = Notify(
        default_application_name=__title__,
        default_notification_icon=dicogis_utils.resolve_internal_path(
            internal_path=__icon_path__
        ),
    )
except Exception as err:
    # e.g. notify-py raises UnsupportedPlatform on Windows releases it doesn't
    # recognize (Windows Server editions): degrade to a no-op rather than
    # taking down every import of this module.
    logger.warning(
        f"System notifications are unavailable on this platform. Trace: {err}"
    )
    notification = None


# ##############################################################################
# ############ Functions ##########
# #################################
def send_system_notify(
    notification_message: str, notification_title: str, notification_sound: bool = True
):
    """Send a notification to the system.

    Args:
        notification_message (str): notification message
        notification_title (str): notification title
    """
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

    try:
        notification.send()
    except Exception as err:
        logger.warning(f"Sending a system notification failed. Trace: {err}")
        logger.info(f"Notification was: {notification_title=}: {notification_message=}")
