#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import json
import os
import random
import re
import sys
import time
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Tuple

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
import base64


GRANT_KEYWORDS = [
    "助成金",
    "補助金",
    "交付決定",
    "採択",
    "Grant",
    "Subsidy",
]

STARTUP_DB_BASE = "https://startup-db.com"
COMPANY_SEARCH_PATHS = [
    "/companies?keyword=",  # preferred guess
    "/search?keyword=",     # legacy/alt
]


@dataclass
class NewsItem:
    company_name: str
    company_url: Optional[str]
    news_title: str
    news_url: Optional[str]
    news_date: Optional[str]
    snippet: Optional[str]
    matched_keywords: List[str]


def create_driver(headless: bool = True, user_agent: Optional[str] = None) -> webdriver.Chrome:
    options = ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1366,900")
    ua = user_agent or (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    options.add_argument(f"--user-agent={ua}")
    # reduce automation flags
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        # more anti-detect tweaks
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": ua})
        return driver
    except WebDriverException as e:
        raise RuntimeError(
            "Failed to start Chrome WebDriver. Ensure Chrome is installed."
        ) from e


def load_cookies(driver: webdriver.Chrome, cookies_path: str) -> None:
    if not cookies_path or not os.path.exists(cookies_path):
        return
    try:
        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        driver.get(STARTUP_DB_BASE)
        human_delay(0.8, 1.2)
        for c in cookies:
            cookie = {k: v for k, v in c.items() if k in {"name", "value", "domain", "path", "expiry", "secure", "httpOnly", "sameSite"}}
            if "domain" not in cookie:
                cookie["domain"] = "startup-db.com"
            if "path" not in cookie:
                cookie["path"] = "/"
            try:
                driver.add_cookie(cookie)
            except Exception:
                continue
        driver.refresh()
        human_delay(0.8, 1.2)
    except Exception:
        pass


def read_company_names(csv_path: str, name_column: str = "企業名") -> List[str]:
    df = pd.read_csv(csv_path)
    if name_column not in df.columns:
        # try common fallbacks
        for candidate in ["企業名", "会社名", "社名", "Company", "会社名（日本語）", "Name"]:
            if candidate in df.columns:
                name_column = candidate
                break
        else:
            raise ValueError(f"Company name column not found. Available columns: {list(df.columns)}")
    names = [str(x).strip() for x in df[name_column].dropna().tolist() if str(x).strip()]
    return names


def human_delay(min_s: float = 1.0, max_s: float = 2.2) -> None:
    time.sleep(random.uniform(min_s, max_s))


def try_click(driver: webdriver.Chrome, by: By, value: str, timeout: int = 8) -> bool:
    try:
        elem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
        elem.click()
        return True
    except Exception:
        return False


def safe_text(elem) -> str:
    try:
        return elem.text.strip()
    except Exception:
        return ""


def find_company_page(driver: webdriver.Chrome, company_name: str, timeout: int = 15) -> Optional[str]:
    try:
        driver.get(STARTUP_DB_BASE)
        human_delay(1.1, 2.0)
        # Prefer concrete selectors from provided HTML
        try:
            search_input = WebDriverWait(driver, 6).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.GlobalSearchForm_field__a99bF"))
            )
        except TimeoutException:
            # Fallback to generic selectors
            selectors = [
                (By.CSS_SELECTOR, "input[type='search']"),
                (By.CSS_SELECTOR, "input[placeholder*='検索']"),
                (By.CSS_SELECTOR, "input[placeholder*='Search']"),
                (By.CSS_SELECTOR, "input[type='text']"),
            ]
            search_input = None
            for by, val in selectors:
                try:
                    search_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((by, val)))
                    if search_input:
                        break
                except TimeoutException:
                    continue
        if search_input is None:
            return None
        search_input.clear()
        search_input.send_keys(company_name)
        human_delay(0.3, 0.7)

        # Click the search button per provided HTML
        clicked = False
        for by, val in [
            (By.CSS_SELECTOR, "button.GlobalSearchForm_searchButton__T6_oK"),
            (By.CSS_SELECTOR, "button[aria-label*='検索']"),
            (By.CSS_SELECTOR, "button[type='submit']"),
        ]:
            try:
                btn = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((by, val)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                human_delay(0.2, 0.4)
                btn.click()
                clicked = True
                break
            except TimeoutException:
                continue
            except Exception:
                continue
        if not clicked:
            # fallback: press Enter
            from selenium.webdriver.common.keys import Keys
            search_input.send_keys(Keys.ENTER)

        # wait for results to appear and settle
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/companies/']"))
            )
        except TimeoutException:
            human_delay(0.8, 1.2)
        # scroll to load more if infinite list
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            human_delay(0.5, 1.0)
        except Exception:
            pass

        html = driver.page_source
        soup = BeautifulSoup(html, "lxml")
        anchors = soup.select("a[href*='/companies/']")
        if not anchors:
            return None
        best_href = None
        for a in anchors:
            href = a.get("href")
            if not href:
                continue
            text = (a.get_text(strip=True) or "")
            title = (a.get("title") or "")
            if company_name in text or company_name in title:
                best_href = href
                break
        if not best_href:
            best_href = anchors[0].get("href")
        if best_href and best_href.startswith("/"):
            return STARTUP_DB_BASE + best_href
        return best_href
    except Exception:
        return None


def open_news_tab(driver: webdriver.Chrome) -> bool:
    # Try tabs containing NEWS/ニュース
    tab_candidates = driver.find_elements(By.XPATH, "//a[contains(., 'NEWS') or contains(., 'ニュース')]")
    for tab in tab_candidates:
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", tab)
            human_delay(0.2, 0.4)
            tab.click()
            human_delay(0.8, 1.4)
            return True
        except Exception:
            continue

    # Sometimes tabs are buttons/divs
    tab_candidates = driver.find_elements(By.XPATH, "//*[self::button or self::div][contains(., 'NEWS') or contains(., 'ニュース')]")
    for tab in tab_candidates:
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", tab)
            human_delay(0.2, 0.4)
            tab.click()
            human_delay(0.8, 1.4)
            return True
        except Exception:
            continue

    return False


def extract_news_items(driver: webdriver.Chrome, company_name: str, company_url: Optional[str]) -> List[NewsItem]:
    items: List[NewsItem] = []

    # Parse current page with BeautifulSoup
    html = driver.page_source
    soup = BeautifulSoup(html, "lxml")

    # Heuristic: find news list containers and links
    link_candidates = []
    # common patterns: anchor text containing news keywords or href including news/press
    for a in soup.select("a"):
        href = a.get("href")
        text = a.get_text(strip=True)
        if not href:
            continue
        href_l = href.lower()
        if ("news" in href_l) or ("press" in href_l) or ("prtimes" in href_l) or ("ニュース" in text) or ("NEWS" in text):
            link_candidates.append((a, href, text))

    for a, href, text in link_candidates:
        parent = a.find_parent(["li", "article", "div"]) or soup
        date_text = None
        snippet = None
        # attempt to find nearby date/snippet
        date_elem = parent.find(["time"]) or parent.find(class_=lambda c: c and ("date" in c or "time" in c))
        if date_elem:
            date_text = date_elem.get_text(strip=True)
        desc_elem = parent.find(class_=lambda c: c and ("summary" in c or "desc" in c or "text" in c))
        if desc_elem:
            snippet = desc_elem.get_text(strip=True)

        full_text = " ".join(filter(None, [text, snippet]))
        matched = [kw for kw in GRANT_KEYWORDS if kw in full_text]
        if matched:
            abs_href = href
            if abs_href and abs_href.startswith("/"):
                abs_href = STARTUP_DB_BASE + abs_href
            items.append(
                NewsItem(
                    company_name=company_name,
                    company_url=company_url,
                    news_title=text,
                    news_url=abs_href,
                    news_date=date_text,
                    snippet=snippet,
                    matched_keywords=matched,
                )
            )

    return items


def process_company(driver: webdriver.Chrome, company_name: str, per_company_timeout: int = 25) -> Tuple[str, Optional[str], List[NewsItem]]:
    company_url = find_company_page(driver, company_name)
    if not company_url:
        return company_name, None, []

    driver.get(company_url)
    human_delay(0.9, 1.5)

    opened = open_news_tab(driver)
    if not opened:
        # Try direct /news subpath
        try:
            if not company_url.endswith("/news"):
                news_url = company_url.rstrip("/") + "/news"
                driver.get(news_url)
                human_delay(0.8, 1.2)
        except Exception:
            pass

    items = extract_news_items(driver, company_name, company_url)
    return company_name, company_url, items


def save_results_json(path: str, data: List[NewsItem]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(x) for x in data], f, ensure_ascii=False, indent=2)


def save_results_csv(path: str, data: List[NewsItem]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fieldnames = [
        "company_name",
        "company_url",
        "news_title",
        "news_url",
        "news_date",
        "snippet",
        "matched_keywords",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in data:
            row = asdict(item)
            row["matched_keywords"] = ",".join(item.matched_keywords)
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Startup DB News for grant-related items per company in CSV.")
    parser.add_argument("--input", default="univ_ventures.csv", help="Input CSV path containing company names (default: univ_ventures.csv)")
    parser.add_argument("--name-column", default="企業名", help="Column name containing company names (default: 企業名)")
    parser.add_argument("--output-json", default="startupdb_grants_results.json", help="Output JSON path")
    parser.add_argument("--output-csv", default="startupdb_grants_results.csv", help="Output CSV path")
    parser.add_argument("--start", type=int, default=0, help="Start index in the company list")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of companies to process (0 means all)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--no-headless", dest="headless", action="store_false")
    parser.set_defaults(headless=True)
    parser.add_argument("--delay-min", type=float, default=0.8, help="Min human delay between actions")
    parser.add_argument("--delay-max", type=float, default=1.8, help="Max human delay between actions")
    parser.add_argument("--retry", type=int, default=1, help="Retries per company on failures")
    parser.add_argument("--cookies", type=str, default="", help="Path to JSON cookies exported from a logged-in browser session for startup-db.com")
    parser.add_argument("--user-agent", type=str, default="", help="Custom User-Agent string")

    args = parser.parse_args()

    global human_delay

    def _human_delay(min_s: float = 1.0, max_s: float = 2.2) -> None:
        time.sleep(random.uniform(args.delay_min, args.delay_max))

    human_delay = _human_delay  # type: ignore

    names = read_company_names(args.input, args.name_column)
    if args.start:
        names = names[args.start:]
    if args.limit and args.limit > 0:
        names = names[: args.limit]

    driver = create_driver(headless=args.headless, user_agent=args.user_agent or None)
    if args.cookies:
        load_cookies(driver, args.cookies)

    all_items: List[NewsItem] = []
    try:
        for idx, name in enumerate(names, 1):
            attempt = 0
            last_items: List[NewsItem] = []
            last_url: Optional[str] = None
            while attempt <= args.retry:
                try:
                    company_name, company_url, items = process_company(driver, name)
                    last_items = items
                    last_url = company_url
                    break
                except Exception:
                    attempt += 1
                    time.sleep(1.0 + attempt * 0.7)
            all_items.extend(last_items)
            print(f"[{idx}/{len(names)}] {name} -> {len(last_items)} grant-related news | {last_url or '-'}")
            human_delay()
    finally:
        driver.quit()

    save_results_json(args.output_json, all_items)
    save_results_csv(args.output_csv, all_items)

    print(f"Saved {len(all_items)} items to {args.output_json} and {args.output_csv}")


if __name__ == "__main__":
    main()
