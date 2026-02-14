# SteamDB & PSN Matcher

A tool for searching Steam and PlayStation Network store data, matching games across both platforms, and viewing PS4/PS5 patch and firmware information.

---

## Requirements

- Python 3.9 or newer (must be added to PATH)
- Google Chrome installed
- ChromeDriver matching your Chrome version

### Python packages

```
pip install streamlit selenium undetected-chromedriver webdriver-manager cloudscraper beautifulsoup4 requests urllib3
```

---

## Running the tool

```
python -m streamlit run streamlit_app.py
```

---

## What it does

**Game Search**
Search for a game by name. The tool queries SteamDB for Steam results and the PlayStation Store for PSN listings. It then attempts to match them and show price, platform, release date, and game type side by side.

**Technology Search**
Search SteamDB by engine or SDK name to find games using that technology. Results are categorized into engines, graphics APIs, SDKs, middleware, and other.

**Batch Search**
Upload a plain text file with one game name per line to process multiple games in sequence.

**Prospero Patches (PS5)**
Pulls patch history for PS5 titles from prosperopatches.com. Shows all available update versions, required firmware for each, file size, and creation date. Useful for checking what firmware a specific game update requires before installing it.

**Orbis Patches (PS4)**
Same as above but for PS4 titles using orbispatches.com. Search by game name or directly by Title ID (format: CUSA12345).

---

## Cloudflare bypass and cf_clearance

SteamDB uses Cloudflare protection. Without a valid bypass, searches will be blocked.

**How to get the cookie:**

1. Open Chrome and go to https://steamdb.info
2. Complete the Cloudflare challenge
3. Open developer tools (F12)
4. Go to the Network tab, reload the page, click any request to steamdb.info
5. Copy the full User-Agent string from the request headers
6. Go to Application > Cookies > steamdb.info and copy the value of cf_clearance

Paste both into the sidebar under "SteamDB Cookie + User Agent" and click Apply.

**Important:**
The cf_clearance cookie and your User-Agent string are tied to your IP address by Cloudflare. They must be used together and from the same IP. Using a proxy, VPN, or a different User-Agent while the cookie is active will not work and will result in blocks. Do not rotate User-Agents or switch IPs while a session is active.

The cookie typically lasts one to two hours. When searches start failing, get a fresh cookie and User-Agent from your browser again.

It is strongly recommended to use the cf_clearance cookie method for all features to work at the same time. Without it, SteamDB searches are likely to fail or return incomplete results.

---

## Limitations

**Technology and SDK information**
The tool pulls engine, SDK, and tech stack data entirely from SteamDB. If SteamDB does not have data for a game, the result will be partial or empty. This is a known limitation of SteamDB's coverage. When a game is not in their database, SteamDB typically returns something like:

> SteamDB does not own [game name]. Gift the game to our bot to improve our data.

In that case there is nothing the tool can do. The information simply is not available.

**Games not found**
Some games that are not multiplatform or not on Steam at all may not appear in SteamDB results. PSN-exclusive titles are one example. The PSN search may still find them, but the Steam side will come up empty.

**Search volume**
It is not recommended to run more than 5 to 10 results per query on SteamDB. High query volumes can trigger bot detection, which causes Cloudflare to invalidate your cf_clearance token early. Keep individual searches focused and avoid batch processing large lists at high speed.

---

## PSN Store regions

You can change the PSN store region in the sidebar. Supported regions:

- fi-fi
- en-us
- en-gb
- de-de
- fr-fr
- ja-jp

Changing the region affects what prices and availability are shown in PSN results.

---

## Hosting

You can run this tool locally on your own machine using the command above. You can also host it on a server with a domain to keep it available around the clock. It works as a local tool you launch when needed or as a persistent hosted service, depending on your setup.

---

## Mobile and alternative environments

The UI has been built with touch support in mind and should work on mobile browsers when hosted. Running it on Android via Termux has not been tested. A rooted device is likely required for Selenium to function. Streamlit's behavior in that environment is unknown.

An Android application wrapper for this tool is theoretically possible.

---

## Known issues

The UI needs work. Layout, styling, and responsiveness are functional but rough in places. Contributions to improve the front end are welcome.

---

## Contributing

Pull requests and suggestions are welcome. If you want to request a feature or report a bug, open an issue or submit a pull request.

---

## TODO

- Fetch patch and build version information from SteamDB's RSS feed
- Pull game metadata from SteamDB and PSN
- Retrieve depot information including game install sizes
- Parse update history to extract MPD and M3U8 stream links

Long shot but worth noting: if someone with the right knowledge wants to package this as an ELF payload for PS5, the ps5-payload-sdk by john-tornblom could potentially make this tool run natively on PS5.
https://github.com/john-tornblom/ps5-payload-sdk

---

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

You are free to use, modify, and distribute this software. If you distribute a modified version, you must also release the source code under the same license.

Full license text: https://www.gnu.org/licenses/gpl-3.0.txt

---

## Third-party notices

This tool depends on the following open source libraries. Their licenses are listed below.

**undetected-chromedriver**
License: GNU General Public License v3.0
https://github.com/ultrafunkamsterdam/undetected-chromedriver

**Selenium**
License: Apache License 2.0
https://github.com/SeleniumHQ/selenium

**Streamlit**
License: Apache License 2.0
https://github.com/streamlit/streamlit

**requests**
License: Apache License 2.0
https://github.com/psf/requests

**webdriver-manager**
License: Apache License 2.0
https://github.com/SergeyPirogov/webdriver_manager

**cloudscraper**
License: MIT License
https://github.com/VeNoMouS/cloudscraper

**Beautiful Soup 4**
License: MIT License
https://www.crummy.com/software/BeautifulSoup

**urllib3**
License: MIT License
https://github.com/urllib3/urllib3

---

This project makes use of data from SteamDB (https://steamdb.info) and the PlayStation Store. Neither of these services is affiliated with or endorses this tool. All trademarks belong to their respective owners.

---

## Disclaimer

This tool uses publicly available data from SteamDB and the PlayStation Store. It does not mirror, redistribute, or host any game files. All data accessed is reachable by anyone through standard web browsing.
