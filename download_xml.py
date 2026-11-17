"""Download the GreenButton XML report.

The scripted Playwright flow is tried first. If it breaks (for example the
portal changed its markup), an LLM-guided Browser Use flow takes over.
"""
from __future__ import annotations

import logging
from io import BytesIO

from playwright.async_api import async_playwright

from agent_flow import run_agent_flow
from config import Settings
from schemas import DownloadParameters

log = logging.getLogger(__name__)


async def _download_xml_files_deterministic(params: DownloadParameters) -> BytesIO:
    """The original, selector-based flow."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        download = None
        try:
            page = await browser.new_page()
            await page.goto("https://alectrautilitiesgbportal.savagedata.com")
            await page.wait_for_load_state("networkidle")

            account_name = page.locator("""xpath=//*[@id="account-name"]""")
            await account_name.wait_for()
            await account_name.click()
            await account_name.fill(params.account_name)

            account_number = page.locator("""xpath=//*[@id="idAccountNumber"]""")
            await account_number.wait_for()
            await account_number.click()
            await account_number.fill(params.account_number)

            await page.keyboard.press("Tab")
            await page.keyboard.type(params.account_phone)

            try:
                value = await account_name.input_value()
                if value != params.account_name:
                    raise ValueError("Account name input failed")
            except Exception as e:
                log.warning("Error locating or filling account name: %s; retrying", e)
                await account_name.fill(params.account_name)

            submit_button = page.locator("""xpath=//*[@class="btn btn-primary btn-block"]""")
            await submit_button.wait_for()
            await submit_button.click()

            download_page_button = page.locator("""xpath=//*[@href="DownloadMyData"]""")
            await download_page_button.wait_for()
            await download_page_button.click()

            start_date_picker = page.locator("""xpath=//*[@id="start"]""")
            await start_date_picker.wait_for()
            await start_date_picker.fill(params.start_date.strftime("%m-%d-%Y"))

            end_date_picker = page.locator("""xpath=//*[@id="end"]""")
            await end_date_picker.wait_for()
            await end_date_picker.fill(params.end_date.strftime("%m-%d-%Y"))

            await page.keyboard.press("Tab")
            await page.keyboard.press("Space")

            download_button = page.locator("""xpath=//*[@class="btn"]""")
            await download_button.wait_for()

            async with page.expect_download() as download_info:
                await download_button.click()
            download = await download_info.value

            filepath = await download.path()
            with open(filepath, "rb") as f:
                return BytesIO(f.read())
        finally:
            if download is not None:
                await download.delete()
            await browser.close()


async def download_xml_files(params: DownloadParameters, settings: Settings) -> BytesIO:
    """Return the downloaded XML, using the LLM fallback if the scripted flow fails."""
    try:
        return await _download_xml_files_deterministic(params)
    except Exception as exc:
        log.warning("Scripted download failed (%s: %s)", type(exc).__name__, exc)
        if not settings.llm_enabled:
            raise
        log.info("Falling back to the LLM-guided browser flow")
        return await run_agent_flow(params, settings)
