from playwright.async_api import async_playwright
from schemas import DownloadParameters
from io import BytesIO


async def download_xml_files(params: DownloadParameters) -> BytesIO:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
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
            # check if it was filled correctly
            value = await account_name.input_value()
            if value != params.account_name:
                raise ValueError("Account name input failed")
        except Exception as e:
            print(f"Error locating or filling account name: {e}")
            print("Retrying to fill account name...")
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

        # Start waiting for the download
        async with page.expect_download() as download_info:
            # Perform the action that initiates download
            await download_button.click()
        download = await download_info.value

        filepath = await download.path()
        with open(filepath, 'rb') as f:
            xml_file = BytesIO(f.read())

        await download.delete()
        await browser.close()

        return xml_file