import base64
import logging

from billiard.exceptions import TimeLimitExceeded
from django.core.files.base import ContentFile
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from helix.celery import app as celery_app
# from helix.settings import QueuePriority

logger = logging.getLogger(__name__)
PDF_TASK_TIMEOUT = 60 * 3  # seconds
SELENIUM_TIMEOUT = 60  # seconds


def __get_pdf_from_html(path, timeout=SELENIUM_TIMEOUT, print_options={}):
    """

    Parameters:
        path (str): The URL or local file path of the HTML page to convert to PDF.
        timeout (int, optional): The maximum time in seconds to wait for the HTML page to load. Default is the value of
        SELENIUM_TIMEOUT.
        print_options (dict, optional): Additional options to customize the PDF generation. Default is an empty
        dictionary.

    Returns:
        bytes: The PDF document as bytes.

    """
    browser_options = webdriver.ChromeOptions()
    browser_options.add_argument('no-sandbox')
    browser_options.add_argument('headless')
    browser_options.add_argument('disable-gpu')
    browser_options.add_argument('disable-dev-shm-usage')

    browser = webdriver.Chrome(options=browser_options)

    browser.get(path)

    try:
        WebDriverWait(browser, timeout).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    except TimeoutException:
        logger.error(f'Chromium timed out for {path}. Saving as is...', exc_info=True)
    except TimeLimitExceeded:
        logger.error(f'Selenium timed out for {path}. Saving as is...', exc_info=True)

    final_print_options = {
        'landscape': False,
        'displayHeaderFooter': False,
        'printBackground': True,
        'preferCSSPageSize': True,
    }
    final_print_options.update(print_options)

    result = browser.execute_cdp_cmd("Page.printToPDF", final_print_options)
    browser.quit()
    return base64.b64decode(result['data'])


@celery_app.task(time_limit=PDF_TASK_TIMEOUT)
def generate_pdf(pk):
    """

    Generate a PDF for a given source preview.

    Parameters:
    - pk (int): The primary key of the source preview.

    Returns:
    None

    Example usage:
    generate_pdf(1)

    """
    from apps.contrib.models import SourcePreview

    source_preview = SourcePreview.objects.get(pk=pk)
    url = source_preview.url
    path = f'{source_preview.token}.pdf'
    logger.warn(f'Starting pdf generation for url: {url} and preview id: {source_preview.id}.')

    source_preview.status = SourcePreview.PREVIEW_STATUS.IN_PROGRESS
    source_preview.save()

    try:
        pdf_content = __get_pdf_from_html(url)
        source_preview.pdf.save(path, ContentFile(pdf_content))
        source_preview.status = SourcePreview.PREVIEW_STATUS.COMPLETED
        source_preview.save()
        logger.warn(f'Completed pdf generation for url: {url} and preview id: {source_preview.id}.')
    except Exception as e:  # noqa
        logger.error('An exception occurred', exc_info=True)
        source_preview.status = SourcePreview.PREVIEW_STATUS.FAILED
        source_preview.save()
        raise e
