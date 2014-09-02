"CVE DOWNLOADER FOR TOPPATCH, NVD/CVE XML VERSION 1.2"
import os
import logging
import logging.config
import requests

from vFense import VFENSE_LOGGING_CONFIG
from vFense.plugins.patching.patching import get_remote_file_size
from vFense.plugins.vuln.cve._constants import CVEDataDir, CVEStrings
from vFense.plugins.vuln._constants import DateValues

logging.config.fileConfig(VFENSE_LOGGING_CONFIG)
logger = logging.getLogger('cve')


def cve_downloader(url, file_path):
    """Http Downloader, that returns the status of the download
        and the size of the file
    Args:
        url (str): the full url path of the xml file.
        file_path (str): The full file patch, to where it is going to be saved.

    Basic Usage:
        >>> from vFense.plugins.vuln.cve.downloader import cve_downloader
        >>> cve_downloader

    Returns:
        Tuple (Boolean, file_size)
        (True, 186)
    """
    req = requests.get(url)
    xml = open(file_path, 'wb')
    if req.ok:
        xml.write(req.content)

    xml.close()

    return(req.ok, os.stat(file_path).st_size)


def log_status(status, size, url_path, nvd_path):
    """Log the status of the downloaded cve file
    Args:
        status (bool): True or False (Verify if the file downloaded)
        size (int): The size of the file that was downloaded.
        url_path (str): The full url of the file that was downloaded.
        nvd_path (str): The full path on disk of the file that was downloaded.

    """
    if status is True and size > 0:
        msg = '%s Downloaded to %s' % (url_path, nvd_path)
        logger.info(msg)
    elif status is False:
        msg = '%s Could not be downloaded' % (url_path)
        logger.warn(msg)
    else:
        msg = '%s Was downloaded to %s, but the size is %d' \
              % (url_path, nvd_path, size)
        logger.error(msg)


def download_xml(url, nvd_file):
    msg = 'downloading %s' % (url)
    print msg
    logger.info(msg)
    xml_status = cve_downloader(url, nvd_file)
    log_status(xml_status[0], xml_status[1], url, nvd_file)


def start_nvd_xml_download():
    """The is the CVE/NVD Downloader
    Basic Usage:
        >>> from vFense.plugins.vuln.cve.downloader import start_nvd_xml_download
        >>> start_nvd_xml_download()
    """
    iter_year = CVEStrings.START_YEAR
    if not os.path.exists(CVEDataDir.XML_DIR):
        os.makedirs(CVEDataDir.XML_DIR, 0755)
    xml_status = (
        cve_downloader(
            CVEStrings.NVD_MODIFIED_URL,
            CVEDataDir.NVD_MODIFIED_FILE
        )
    )
    log_status(
        xml_status[0], xml_status[1],
        CVEStrings.NVD_MODIFIED_URL,
        CVEDataDir.NVD_MODIFIED_FILE
    )

    # If we have not yet downloaded the 2002-now CVE's,
    # please download them now

    while iter_year <= DateValues.CURRENT_YEAR:
        nvd = CVEStrings.NVDCVE_BASE + str(iter_year) + '.xml'
        full_url = CVEStrings.NVD_DOWNLOAD_URL + nvd
        full_nvd = os.path.join(CVEDataDir.XML_DIR, nvd)
        remote_file_size = int(get_remote_file_size(full_url))

        if not os.path.exists(full_nvd):
            download_xml(full_url, full_nvd)

        else:
            local_file_size = os.stat(full_nvd).st_size
            if local_file_size != remote_file_size:
                download_xml(full_url, full_nvd)

            elif local_file_size == remote_file_size:
                msg = "%s already exists at %s" % (nvd, full_nvd)
                print msg
                logger.info(msg)

        if iter_year == DateValues.CURRENT_YEAR:
            msg = 'downloading %s' % (full_url)
            print msg
            logger.info(msg)
            # Always download the latest and the current year
            xml_status = cve_downloader(full_url, full_nvd)
            log_status(xml_status[0], xml_status[1], full_url, full_nvd)

        iter_year = iter_year + 1
