import re

from . import settings
from .log import log
from .constants import KODI_VERSION
from .util import get_kodi_string, set_kodi_string

AUTO = -1
WV_L1 = 1
WV_L2 = 2
WV_L3 = 3
WV_LEVELS = [AUTO, WV_L1, WV_L3]
WV_UUID = 'edef8ba9-79d6-4ace-a3c8-27dcd51d21ed'

HDCP_NONE = 0
HDCP_1 = 10
HDCP_2_2 = 22
HDCP_3_0 = 30
HDCP_LEVELS = [AUTO, HDCP_NONE, HDCP_1, HDCP_2_2, HDCP_3_0]

def is_wv_secure():
    return widevine_level() == WV_L1

def req_wv_level(level):
    return widevine_level() <= level

def req_hdcp_level(level):
    return hdcp_level() >= level

def widevine_level():
    return int(get_kodi_string('wv_level', WV_L3))

def hdcp_level():
    return int(get_kodi_string('hdcp_level', HDCP_NONE))

def set_drm_level():
    wv_level = settings.common_settings.getEnum('wv_level', WV_LEVELS, default=AUTO)
    hdcp_level = settings.common_settings.getEnum('hdcp_level', HDCP_LEVELS, default=AUTO)

    wv_mode = 'manual'
    hdcp_mode = 'manual'

    if wv_level == AUTO:
        wv_mode = 'auto'
        wv_level = None

    if hdcp_level == AUTO:
        hdcp_mode = 'auto'
        hdcp_level = None

    if not wv_level or not hdcp_level:
        if KODI_VERSION > 17:
            try:
                import xbmcdrm
                crypto = xbmcdrm.CryptoSession(WV_UUID, 'AES/CBC/NoPadding', 'HmacSHA256')

                if not wv_level:
                    wv_level = crypto.GetPropertyString('securityLevel')
                    if wv_level:
                        wv_level = int(wv_level.lower().lstrip('l'))

                if not hdcp_level:
                    hdcp_level = crypto.GetPropertyString('hdcpLevel')
                    if hdcp_level:
                        hdcp_level = re.findall('\\d+\\.\\d+', hdcp_level)
                        hdcp_level = int(float(hdcp[0])*10) if hdcp_level else None

            except Exception as e:
                log.debug('Failed to obtain crypto config')
                log.exception(e)

        if not wv_level:
            wv_mode = 'fallback'
            wv_level = WV_L3

        if not hdcp_level:
            hdcp_mode = 'fallback'
            hdcp_level = HDCP_NONE

    set_kodi_string('wv_level', wv_level)
    set_kodi_string('hdcp_level', hdcp_level)

    log.debug('Widevine Level ({}): {}'.format(wv_mode, wv_level))
    log.debug('HDCP Level ({}): {}'.format(hdcp_mode, hdcp_level/10.0))
