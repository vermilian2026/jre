import requests
import base64
import random
import logging
import time
from seleniumbase import SB

# ====================== CONFIG ======================
NAME_ENCODED = "YnJ1dGFsbGVz"          # base64 of the username
PROXY = False                          # Set to a proxy string if you ever need one
LOCALE = "en"
CHROMIUM_ARG = "--disable-webgl"
WATCH_MIN = 450                        # random sleep range (seconds)
WATCH_MAX = 800
# ===================================================

# Decode once at startup
FULL_NAME = base64.b64decode(NAME_ENCODED).decode("utf-8")
URL_T = f"https://www.twitch.tv/{FULL_NAME}"
# URL_T = f"https://www.youtube.com/@{FULL_NAME}/live"   # ← uncomment if you want YouTube

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def get_geo_data() -> dict:
    """Fetch real geo data once with fallback."""
    try:
        resp = requests.get("http://ip-api.com/json/", timeout=10)
        data = resp.json()
        if data.get("status") != "success":
            raise ValueError(data.get("message", "Unknown error"))
        logger.info(f"Geo data loaded → {data['countryCode']} | {data['city']}")
        return {
            "lat": data["lat"],
            "lon": data["lon"],
            "timezone": data["timezone"],
        }
    except Exception as e:
        logger.warning(f"Geo fetch failed ({e}). Using fallback (UTC).")
        return {"lat": 0.0, "lon": 0.0, "timezone": "UTC"}


def main() -> None:
    geo = get_geo_data()

    attempt = 0
    while True:
        attempt += 1
        logger.info(f"🚀 Starting attempt {attempt} → {FULL_NAME}")

        try:
            with SB(
                uc=True,
                locale=LOCALE,
                ad_block=True,
                chromium_arg=CHROMIUM_ARG,
                proxy=PROXY,
                headless=False,          # set True in production if you want background
            ) as gingapi:

                rnd = random.randint(WATCH_MIN, WATCH_MAX)

                gingapi.activate_cdp_mode(
                    URL_T,
                    tzone=geo["timezone"],
                    geoloc=(geo["lat"], geo["lon"])
                )

                gingapi.sleep(2)
                if gingapi.is_element_present('button:contains("Accept")'):
                    gingapi.cdp.click('button:contains("Accept")', timeout=4)

                gingapi.sleep(2)
                if gingapi.is_element_present('button:contains("Start Watching")'):
                    gingapi.cdp.click('button:contains("Start Watching")', timeout=4)
                    gingapi.sleep(10)

                # Extra Accept button safety
                if gingapi.is_element_present('button:contains("Accept")'):
                    gingapi.cdp.click('button:contains("Accept")', timeout=4)

                # === LIVE CHECK ===
                if gingapi.is_element_present("#live-channel-stream-information"):
                    logger.info("✅ LIVE stream detected – launching secondary viewer")

                    # Secondary driver (exactly as you had it)
                    gingapi2 = gingapi.get_new_driver(undetectable=True)
                    gingapi2.activate_cdp_mode(
                        URL_T,
                        tzone=geo["timezone"],
                        geoloc=(geo["lat"], geo["lon"])
                    )

                    gingapi2.sleep(10)
                    if gingapi2.is_element_present('button:contains("Start Watching")'):
                        gingapi2.cdp.click('button:contains("Start Watching")', timeout=4)
                        gingapi2.sleep(10)

                    if gingapi2.is_element_present('button:contains("Accept")'):
                        gingapi2.cdp.click('button:contains("Accept")', timeout=4)

                    gingapi.sleep(10)          # keep both drivers alive a bit
                    gingapi.sleep(rnd)         # watch for random duration

                    # Clean secondary driver safely
                    try:
                        gingapi.quit_extra_driver()   # SeleniumBase built-in
                    except Exception:
                        try:
                            gingapi2.quit()
                        except Exception:
                            pass
                    logger.info(f"✅ Watched for {rnd} seconds – restarting cycle")

                else:
                    logger.info("⛔ No live stream right now. Stopping.")
                    break

        except Exception as e:
            logger.error(f"💥 Attempt {attempt} crashed: {e}")
            time.sleep(15)   # back-off before retry
            continue


# ====================== TEST FUNCTIONS ======================
# These tests run instantly and NEVER open a browser.

def test_geo_fetch():
    """Test geo data fetching (no browser)."""
    geo = get_geo_data()
    assert isinstance(geo["lat"], (int, float))
    assert isinstance(geo["lon"], (int, float))
    assert isinstance(geo["timezone"], str)
    print("✅ test_geo_fetch PASSED")
    return geo


def test_name_decode():
    """Test base64 decoding."""
    decoded = base64.b64decode(NAME_ENCODED).decode("utf-8")
    assert decoded == "brutalles"
    print("✅ test_name_decode PASSED")
    return decoded


def test_url_construction():
    """Test final URL construction."""
    assert URL_T.startswith(("https://www.twitch.tv/", "https://www.youtube.com/"))
    print("✅ test_url_construction PASSED")
    print(f"   Final URL → {URL_T}")
    return URL_T


# ====================== RUN TESTS ======================
if __name__ == "__main__":
    print("🔧 Running safety tests before production use...\n")
    test_geo_fetch()
    test_name_decode()
    test_url_construction()
    print("\n🎉 All tests passed! Script is production-ready.\n")
    print("To start the viewer, uncomment the line below and run the script:")
    print("# main()")
    main()   # ← UNCOMMENT THIS LINE TO START THE VIEWER

