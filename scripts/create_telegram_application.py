import argparse
import asyncio
from httpx import AsyncClient
from bs4 import BeautifulSoup


def parse_app_details(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    app_id_tag = soup.find('label', text='App api_id:').find_next('span')
    app_id = app_id_tag.strong.text if app_id_tag and app_id_tag.strong else None

    app_hash_tag = soup.find('label', text='App api_hash:').find_next('span')
    app_hash = app_hash_tag.text if app_hash_tag else None

    return {'app_id': app_id, 'app_hash': app_hash}


async def create_telegram_app(hash: str, stel_token: str,
                              app_title="telegram front end",
                              app_shortname="xxxxtgapp",
                              app_url="https://github.com/ConnorSwis/telegram-front-end",
                              app_desc="https://github.com/ConnorSwis/telegram-front-end"):
    url = "https://my.telegram.org/apps/create"
    headers = {
        "Origin": "https://my.telegram.org",
        "Referer": "https://my.telegram.org/apps",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    }
    data = {
        "MIME Type": " application/x-www-form-urlencoded; charset=UTF-8",
        "hash": hash,
        "app_title": app_title,
        "app_shortname": app_shortname,
        "app_url": app_url,
        "app_platform": "desktop",
        "app_desc": app_desc,
    }
    cookies = {
        "stel_token": stel_token
    }
    async with AsyncClient() as client:
        while True:
            resps = await asyncio.gather(
                *[client.post(url=url, headers=headers, data=data, cookies=cookies) for _ in range(1, 100)]
            )
            for i, resp in enumerate(resps):
                print(i, resp.status_code)
                print(i, resp.text)
                if resp.text != "ERROR":
                    app_details = parse_app_details(resp.text)
                    return app_details


def main():
    parser = argparse.ArgumentParser(
        description="Create a Telegram app with provided hash and stel_token.")
    parser.add_argument("hash", help="The hash value for the Telegram app.")
    parser.add_argument(
        "stel_token", help="The stel_token for authentication.")

    args = parser.parse_args()

    # Run the asyncio function with command-line arguments
    asyncio.run(create_telegram_app(
        hash=args.hash,
        stel_token=args.stel_token
    ))


if __name__ == "__main__":
    main()
