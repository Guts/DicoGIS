#! python3  # noqa: E265


"""
    Name:         Check Norris
    Purpose:      A class dedicated to perform system test to ensure another \
        program works fine

    Author:       Julien Moura (@geojulien)
"""

# #############################################################################
# ###### Libraries ########
# #########################

import logging
import socket
from os import environ as env
from urllib.request import (
    ProxyHandler,
    build_opener,
    getproxies,
    install_opener,
    urlopen,
)

# #############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)

# #############################################################################
# ########## Classes ###############
# ##################################


class CheckNorris:
    """Check Norris never fails, always tests."""

    def check_internet_connection(self, remote_server: str = "www.google.com") -> bool:
        """Check if an internet connection is operational.

        Source: http://stackoverflow.com/a/20913928/2556577

        Args:
            remote_server: internet address to try. Defaults to "www.google.com".

        Returns:
            True if connection works
        """
        try:
            # see if we can resolve the host name -- tells us if there is
            # a DNS listening
            host = socket.gethostbyname(remote_server)
            # connect to the host -- tells us if the host is actually
            # reachable
            socket.create_connection((host, 80), 2)
            logger.info("Internet connection OK.")
            return True
        except Exception as err:
            logger.info(f"Internet connection failed. Trace: {err}")
            pass
        # end of method
        return False

    def check_proxy(self, specific: dict = {}):
        """Check if proxy settings are set on the OS.

        Returns:
        -- 1 when direct connection works fine
        -- 2 when direct connection fails and any proxy is set in the OS
        -- 3 and settings when direct connection fails but a proxy is set
        see: https://docs.python.org/2/library/urllib.html#urllib.getproxies
        """
        os_proxies = getproxies()
        if len(os_proxies) == 0 and self.check_internet_connection:
            logger.info("No proxy needed nor set. Direct connection works.")
            return 1
        elif len(os_proxies) == 0 and not self.check_internet_connection:
            logger.error("Proxy not set in the OS. Needs to be specified")
            return 2
        else:
            #
            env["http_proxy"] = os_proxies.get("http")
            env["https_proxy"] = os_proxies.get("https")
            #
            proxy = ProxyHandler(
                {"http": os_proxies.get("http"), "https": os_proxies.get("https")}
            )
            opener = build_opener(proxy)
            install_opener(opener)
            urlopen("http://www.google.com")
            return 3, os_proxies
