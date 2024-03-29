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
notification = Notify(
    default_application_name=__title__,
    default_notification_icon=dicogis_utils.resolve_internal_path(
        internal_path=__icon_path__
    ),
)


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
