import json
import math
import re
import subprocess
import time
from collections import deque
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

BASE = "http://tds26vu3ptapxx6igo6n26kuwfpn2l5omkmagc4hc7g7yn2o3xb25syd.onion"

URLS = {
    "task1": f"{BASE}/37/cat/home/index.html",
    "task2": f"{BASE}/37/cat/outdoors/index.html",
    "task3": f"{BASE}/37/cat/electronics/index.html",
    "task4": f"{BASE}/54/c/sports/index.html",
    "task5": f"{BASE}/54/c/politics/index.html",
    "task6": f"{BASE}/54/c/sports/index.html",
    "task7": f"{BASE}/92/index.html",
    "task8": f"{BASE}/92/explore.html",
    "task9": f"{BASE}/92/index.html",
    "task10": f"{BASE}/11/users/index.html",
    "task11": f"{BASE}/11/b/leaks/index.html",
    "task12": f"{BASE}/11/users/index.html",
}


def clean_num(text: str) -> str:
    return re.sub(r"[^\d.\-]", "", text or "")


def to_int(text: str) -> int:
    s = clean_num(text)
    return int(float(s)) if s else 0


def to_float(text: str) -> float:
    s = clean_num(text)
    return float(s) if s else 0.0


_soup_cache = {}


def fetch_html(url: str, retries: int = 3, max_time: int = 45) -> str:
    for attempt in range(1, retries + 1):
        print(f"FETCH {attempt}/{retries}: {url}", flush=True)
        proc = subprocess.run(
            [
                "curl",
                "-sS",
                "--max-time",
                str(max_time),
                "--socks5-hostname",
                "127.0.0.1:9050",
                url,
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout
        time.sleep(min(3 * attempt, 12))
    raise RuntimeError(f"Failed to fetch: {url}")


def fetch_soup(url: str) -> BeautifulSoup:
    if url in _soup_cache:
        return _soup_cache[url]
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    _soup_cache[url] = soup
    return soup


def resolve_href(current_url: str, soup: BeautifulSoup, href: str) -> str:
    base_tag = soup.find("base", href=True)
    if base_tag:
        base_abs = urljoin(current_url, base_tag["href"])
        return urljoin(base_abs, href)
    return urljoin(current_url, href)


def collect_paginated_pages(start_url: str) -> dict:
    pages = {}
    queue = deque([start_url])
    while queue:
        url = queue.popleft()
        if url in pages:
            continue
        soup = fetch_soup(url)
        pages[url] = soup

        links = soup.select(".pager a[href], .pagination a[href], a[rel='next'][href], a.next[href]")
        for a in links:
            next_url = resolve_href(url, soup, a["href"])
            if next_url not in pages and next_url not in queue:
                queue.append(next_url)

    return pages


# ---------------- ECOMMERCE ----------------
def collect_products(category_url: str) -> dict:
    products = {}
    pages = collect_paginated_pages(category_url)

    for page_url, soup in pages.items():
        cards = soup.select("div.card")
        for card in cards:
            sku_text = card.select_one(".card-sku")
            if not sku_text:
                continue
            m = re.search(r"SKU:\s*([A-Z0-9\-]+)", sku_text.get_text(" ", strip=True))
            if not m:
                continue
            sku = m.group(1)

            price_el = card.select_one(".current-price")
            price = 0.0
            if price_el and price_el.get("data-raw-price"):
                price = to_float(price_el.get("data-raw-price"))
            elif price_el:
                price = to_float(price_el.get_text(" ", strip=True))

            stock_text = card.select_one(".stock-badge")
            stock_status = stock_text.get_text(" ", strip=True) if stock_text else ""

            rating = 0.0
            rating_el = card.select_one(".rating-strip")
            if rating_el and rating_el.get("aria-label"):
                rm = re.search(r"Rated\s+([0-9.]+)", rating_el.get("aria-label"), re.I)
                if rm:
                    rating = to_float(rm.group(1))

            reviews = 0
            if rating_el:
                sib = rating_el.find_next_sibling("span")
                if sib:
                    rv = re.search(r"\((\d+)\)", sib.get_text(" ", strip=True))
                    if rv:
                        reviews = int(rv.group(1))

            link_el = card.select_one("a.p-link[href]")
            product_url = resolve_href(page_url, soup, link_el["href"]) if link_el else ""

            products[sku] = {
                "sku": sku,
                "price": price,
                "stock_status": stock_status,
                "rating": rating,
                "reviews": reviews,
                "product_url": product_url,
            }

    return products


def get_inventory_level(product_url: str) -> int:
    soup = fetch_soup(product_url)
    data_script = soup.find("script", id="__SERVER_DATA")
    if data_script and data_script.string:
        try:
            payload = json.loads(data_script.string.strip())
            return int(payload.get("inventory_level", 0))
        except Exception:
            pass

    stock_badge = soup.select_one(".stock-badge")
    if stock_badge:
        txt = stock_badge.get_text(" ", strip=True).lower()
        if "out of stock" in txt:
            return 0
        m = re.search(r"only\s+(\d+)\s+left", txt)
        if m:
            return int(m.group(1))
        if "in stock" in txt:
            return 1
    return 0


def task1() -> str:
    # Q1: Total inventory value for Home category (price * inventory across products)
    products = collect_products(URLS["task1"])
    total = 0.0
    for p in products.values():
        inv = get_inventory_level(p["product_url"])
        total += p["price"] * inv
    return f"{total:.2f}"


def task2() -> str:
    # Q2: SKU with the highest review count in Outdoors category
    products = collect_products(URLS["task2"])
    best = max(products.values(), key=lambda x: x["reviews"])
    return best["sku"]


def task3() -> str:
    # Q3: Average rating of out-of-stock Electronics items
    products = collect_products(URLS["task3"])
    vals = [p["rating"] for p in products.values() if "out of stock" in p["stock_status"].lower()]
    avg = (sum(vals) / len(vals)) if vals else 0.0
    return f"{avg:.2f}"


# ---------------- NEWS ----------------
def collect_article_links(category_url: str) -> list:
    pages = collect_paginated_pages(category_url)
    links = []
    seen = set()
    for page_url, soup in pages.items():
        for a in soup.select("article.article-card h2 a[href]"):
            u = resolve_href(page_url, soup, a["href"])
            if u not in seen:
                seen.add(u)
                links.append(u)
    return links


def parse_article_views(article_url: str) -> tuple:
    soup = fetch_soup(article_url)
    view_el = soup.find(attrs={"data-internal-views": True})
    views = int(view_el["data-internal-views"]) if view_el else 0
    m = re.search(r"/article/([^/]+)\.html$", article_url)
    article_id = m.group(1) if m else article_url
    return article_id, views


def task4() -> str:
    # Q4: Sum of internal views for all Sports articles
    total = 0
    for link in collect_article_links(URLS["task4"]):
        _, views = parse_article_views(link)
        total += views
    return str(total)


def task5() -> str:
    # Q5: Rounded average internal views for Politics articles
    views = []
    for link in collect_article_links(URLS["task5"]):
        _, v = parse_article_views(link)
        views.append(v)
    avg = (sum(views) / len(views)) if views else 0.0
    return str(int(math.floor(avg + 0.5)))


def task6() -> str:
    # Q6: Sports article id with maximum internal views
    best_id, best_views = "", -1
    for link in collect_article_links(URLS["task6"]):
        aid, views = parse_article_views(link)
        if views > best_views:
            best_id, best_views = aid, views
    return best_id


# ---------------- SOCIAL ----------------
def crawl_social(seed_urls: list) -> dict:
    allowed = re.compile(
        r"/92/(index\.html|feed_page_\d+\.html|explore(?:_page_\d+)?\.html|u/[^/]+/index\.html)$"
    )
    parsed_base = urlparse(BASE)

    pages = {}
    queue = deque(seed_urls)
    while queue:
        url = queue.popleft()
        if url in pages:
            continue

        try:
            soup = fetch_soup(url)
        except Exception:
            continue
        pages[url] = soup

        for a in soup.select("a[href]"):
            next_url = resolve_href(url, soup, a["href"])
            p = urlparse(next_url)
            if p.netloc != parsed_base.netloc:
                continue
            if allowed.search(p.path):
                if next_url not in pages and next_url not in queue:
                    queue.append(next_url)

    return pages


def extract_posts_and_users(social_pages: dict) -> tuple:
    posts = {}
    users = {}

    for url, soup in social_pages.items():
        # Posts
        for card in soup.select("article.post-card[data-post-id]"):
            post_id = card.get("data-post-id", "").strip()
            if not post_id:
                continue

            text = ""
            text_el = card.select_one(".post-text")
            if text_el:
                text = text_el.get_text(" ", strip=True)
            tags = set(re.findall(r"#\w+", text.lower()))

            likes = 0
            likes_block = card.find("div", attrs={"aria-label": re.compile(r"likes", re.I)})
            if likes_block:
                likes_span = likes_block.find("span")
                likes = to_int(likes_span.get_text(" ", strip=True) if likes_span else likes_block.get_text(" ", strip=True))

            if post_id not in posts or likes > posts[post_id]["likes"]:
                posts[post_id] = {"likes": likes, "hashtags": tags}
            else:
                posts[post_id]["hashtags"].update(tags)

        # User profile pages
        if "/92/u/" in url:
            ph = soup.select_one(".profile-header")
            if not ph:
                continue

            handle_el = ph.select_one(".handle")
            if not handle_el:
                continue
            handle = handle_el.get_text(" ", strip=True).lstrip("@").strip()

            ph_text = ph.get_text(" ", strip=True)
            loc = ""
            lm = re.search(r"📍\s*([^🗓]+?)\s*(?:🗓|$)", ph_text)
            if lm:
                loc = lm.group(1).strip()

            fm = re.search(r"([\d,]+)\s*Followers", ph_text, re.I)
            followers = to_int(fm.group(1)) if fm else 0

            users[handle] = {"location": loc, "followers": followers}

    return posts, users


def task7(posts_users_cache: dict = None) -> str:
    # Q7: User handle in Catherinefurt with the highest follower count
    cache = posts_users_cache or {}
    users = cache.get("users", {})
    candidates = [(h, u["followers"]) for h, u in users.items() if u["location"] == "Catherinefurt"]
    if not candidates:
        return ""
    return max(candidates, key=lambda x: x[1])[0]


def task8(posts_users_cache: dict = None) -> str:
    # Q8: Total likes on posts containing #coding
    cache = posts_users_cache or {}
    posts = cache.get("posts", {})
    total = sum(p["likes"] for p in posts.values() if "#coding" in p["hashtags"])
    return str(total)


def task9(posts_users_cache: dict = None) -> str:
    # Q9: Number of user profiles whose location is Traciefort
    cache = posts_users_cache or {}
    users = cache.get("users", {})
    count = sum(1 for u in users.values() if u["location"] == "Traciefort")
    return str(count)


# ---------------- FORUM ----------------
def collect_forum_user_links(users_index_url: str) -> tuple:
    pages = collect_paginated_pages(users_index_url)
    links = []
    rep_by_user = {}
    seen = set()

    for page_url, soup in pages.items():
        for tr in soup.select("table tbody tr"):
            a = tr.select_one("td a[href]")
            tds = tr.select("td")
            if not a or len(tds) < 2:
                continue
            user_url = resolve_href(page_url, soup, a["href"])
            uname = a.get_text(" ", strip=True)
            rep_by_user[uname] = to_int(tds[1].get_text(" ", strip=True))
            if user_url not in seen:
                seen.add(user_url)
                links.append(user_url)

    return links, rep_by_user


def parse_forum_user_profile(user_url: str) -> dict:
    soup = fetch_soup(user_url)
    panel = soup.select_one(".panel")
    text = panel.get_text(" ", strip=True) if panel else soup.get_text(" ", strip=True)

    jm = re.search(r"Joined:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text, re.I)
    joined = jm.group(1) if jm else ""

    rm = re.search(r"Reputation:\s*([\d,]+)", text, re.I)
    rep = to_int(rm.group(1)) if rm else 0

    vendor = bool(re.search(r"\bVendor\b", text, re.I))
    return {"joined": joined, "rep": rep, "vendor": vendor}


def task10_forum_cache(cache: dict) -> str:
    # Q10: Sum of reputation for users who joined in 2025-09
    total = 0
    for profile in cache.values():
        if profile["joined"].startswith("2025-09"):
            total += profile["rep"]
    return str(total)


def task12_forum_cache(cache: dict) -> str:
    # Q12: Total reputation of users marked as Vendor
    total = sum(p["rep"] for p in cache.values() if p["vendor"])
    return str(total)


def task11() -> str:
    # Q11: Thread id with the highest view count in leaks board
    pages = collect_paginated_pages(URLS["task11"])
    best_id, best_views = "", -1

    for page_url, soup in pages.items():
        for tr in soup.select("table.thread-list tbody tr"):
            a = tr.select_one("td a[href]")
            v = tr.select_one("span[data-views]")
            if not a or not v:
                continue
            href = a.get("href", "")
            m = re.search(r"t/(\d+)\.html", href)
            thread_id = m.group(1) if m else href
            views = to_int(v.get("data-views"))
            if views > best_views:
                best_id, best_views = thread_id, views

    return best_id


def main():
    # Precompute social crawl once for tasks 7/8/9
    social_pages = crawl_social([URLS["task7"], URLS["task8"]])
    posts, users = extract_posts_and_users(social_pages)
    social_cache = {"posts": posts, "users": users}

    # Precompute forum users once for tasks 10/12
    user_links, rep_index = collect_forum_user_links(URLS["task10"])
    forum_cache = {}
    for user_url in user_links:
        try:
            profile = parse_forum_user_profile(user_url)
        except Exception:
            continue
        # Fallback rep from index if profile parsing fails
        if profile["rep"] == 0:
            m = re.search(r"/u/([^/.]+)\.html", user_url)
            if m:
                uname = m.group(1)
                profile["rep"] = rep_index.get(uname, 0)
        forum_cache[user_url] = profile

    answers = {
        "task1": task1(),
        "task2": task2(),
        "task3": task3(),
        "task4": task4(),
        "task5": task5(),
        "task6": task6(),
        "task7": task7(social_cache),
        "task8": task8(social_cache),
        "task9": task9(social_cache),
        "task10": task10_forum_cache(forum_cache),
        "task11": task11(),
        "task12": task12_forum_cache(forum_cache),
    }

    print(json.dumps(answers, indent=2))


if __name__ == "__main__":
    main()
