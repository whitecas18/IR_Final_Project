import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import re
from crawler.items import CrawlerItem


class WikiSpider(CrawlSpider):
    """
      This a class that is use to scarp wikipedia links
      """
    name = 'wiki'
    allowed_domains = ['en.wikipedia.org']
    start_urls = ['http://en.wikipedia.org/']

    rules = (
        Rule(LinkExtractor(allow=r'Items/'), callback='parse_item', follow=True),
        Rule(LinkExtractor(allow='(/wiki/)((?!:).)*$'),
             callback='parse_item', follow=True)
    )

    def parse_item(self, response):
        """

               This parse a wikipedia page
               :return: request
               :scrapes: Title Summary URL

               """

        title = response.css('title::text').get()
        div = response.xpath("//*[@id='bodyContent']")
        passages = div.xpath('.//p')

        for p in passages:

            x = p.get()
            contains_b = re.search(r'<b>.*</b>', x)
            if contains_b:
                summary = x
                summary = re.sub('<[^<]+?>', '', summary)

        yield CrawlerItem(title=title, url=response.url, summary=summary)
