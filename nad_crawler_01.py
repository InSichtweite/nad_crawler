import scrapy
import re
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from datetime import datetime
from urllib.parse import urlparse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class CrawlingSpider(CrawlSpider):
    name = "crawler01"
    #allowed_domains = ["residence.aec.at"]
    start_urls = ["https://residence.aec.at/lastentry/"]
    # allowed_domains = ["toscrape.com"]
    # start_urls = ["http://books.toscrape.com/"]
    # allowed_domains = ["berliner-zeitung.de"]
    # start_urls = ["https://www.berliner-zeitung.de/"]

    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DEPTH_LIMIT': 10,
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

    def parse_item(self, response):
        current_domain = urlparse(response.url).netloc

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
                "has cookies": has_cookies,
                "has ads": bool(has_ads)
            }

    def check_for_ads(self, response):
        has_ads = []
        for identifier in self.ad_identifiers:
            xpath_query = f"//div[re:test(@class, '{identifier}') or re:test(@id, '{identifier}')]"
            divs = response.xpath(xpath_query, namespaces={"re": "http://exslt.org/regular-expressions"})
            if divs:
                has_ads.extend(divs)
        return has_ads if has_ads else None

if __name__ == "__main__":
    # Generate a unique filename out of domain and date
    parsed_url = urlparse(CrawlingSpider.start_urls[0])
    start_domain = parsed_url.netloc.replace('.', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output_{start_domain}_{timestamp}.json"

    # Create a CrawlerProcess instance with the project settings
    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'json',
        'FEED_URI': output_file,
    })
    process.crawl(CrawlingSpider)
    process.start()

    print(f"Output saved to {output_file}")
