import scrapy
import re
from scrapy.crawler import CrawlerProcess
from datetime import datetime
from urllib.parse import urlparse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class CrawlingSpider(CrawlSpider):
    name = "crawler01"

    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'LOG_LEVEL': 'INFO',
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
    }

    rules = (
        Rule(LinkExtractor(), callback="parse_item", follow=True),
    )

    ad_identifiers = [
        r'\bad\b', r'\bads\b', r'\badvertisement\b', r'\bsponsored\b', r'\bpromoted\b', r'\bgooglesyndication\b',
        r'\badservice\b', r'\badchoice\b'
    ]

    blocklist = [
        "google.com", "amazon.com", "wikipedia.com"
    ]

    def __init__(self, start_url=None, depth_limit=3, *args, **kwargs):
        super(CrawlingSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.custom_settings['DEPTH_LIMIT'] = int(depth_limit)

    def parse_item(self, response):
        current_domain = urlparse(response.url).netloc
        current_depth = response.meta.get('depth', 0)

        # Check if the domain is in the blocklist
        if any(blocked_domain in current_domain for blocked_domain in self.blocklist):
            self.log(f"Skipping blocked domain: {current_domain}")
            return

        # check for cookies
        has_cookies = 'Set-Cookie' in response.headers

        # check for ads
        has_ads = self.check_for_ads(response)

        # Yield URLs with no cookies and no ads
        if not has_cookies and not has_ads:
            yield {
                "url": response.url,
                "title": response.css('title::text').get(),
                "depth": current_depth,
                "has cookies": has_cookies,
                "has ads": bool(has_ads)
            }
        # Follow links if within depth limit
        if current_depth < self.depth_limit:
            for link in LinkExtractor().extract_links(response):
                yield scrapy.Request(link.url, callback=self.parse_item, meta={'depth': current_depth + 1})

    def check_for_ads(self, response):
        has_ads = []
        for identifier in self.ad_identifiers:
            xpath_query = f"//div[re:test(@class, '{identifier}') or re:test(@id, '{identifier}')]"
            divs = response.xpath(xpath_query, namespaces={"re": "http://exslt.org/regular-expressions"})
            if divs:
                has_ads.extend(divs)
        return has_ads if has_ads else None

if __name__ == "__main__":
    from scrapy.crawler import CrawlerProcess
    import sys

    start_url = sys.argv[1]
    depth_limit = sys.argv[2]

    # Create a CrawlerProcess instance with the project settings
    process = CrawlerProcess()
    process.crawl(CrawlingSpider, start_url=start_url, depth_limit=depth_limit)
    process.start()
