"""Fetch one public page and extract readable information."""
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup


def validate_url(url):
    parsed = urlparse(str(url).strip())
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        raise ValueError("Enter a complete public webpage URL beginning with https://.")
    if parsed.scheme != "https":
        raise ValueError("For safety, use an HTTPS webpage.")
    return parsed.geturl()


def parse_html(html, source_url):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else "Untitled page"
    headings = [node.get_text(" ", strip=True) for node in soup.find_all(["h1", "h2", "h3"]) if node.get_text(strip=True)][:30]
    links = []
    for anchor in soup.find_all("a", href=True):
        label = anchor.get_text(" ", strip=True)
        if label:
            links.append({"title": label[:150], "url": urljoin(source_url, anchor["href"])})
        if len(links) >= 30:
            break
    paragraphs = [node.get_text(" ", strip=True) for node in soup.find_all("p") if node.get_text(strip=True)][:12]
    return {"title": title, "headings": headings, "links": links, "paragraphs": paragraphs}


def fetch_page(url):
    url = validate_url(url)
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "MediCare-College-Demo/1.0 (educational project)"})
        response.raise_for_status()
    except requests.Timeout as error:
        raise ValueError("The webpage took too long to respond. Please try again later.") from error
    except requests.RequestException as error:
        raise ValueError("Could not retrieve this webpage. Check the address and your connection.") from error
    return {"source": response.url, **parse_html(response.text, response.url)}
