# coding: utf-8
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

#from scrapy.contrib.exporter.jsonlines import JsonLinesItemExporter
from scrapy import signals
from scrapy.exceptions import DropItem
from scrapy.xlib.pydispatch import dispatcher
from mscrap.items import LegisladorItem


class MscrapPipeline(object):
    def __init__(self):
        self.duplicates = {}
        dispatcher.connect(self.spider_opened, signals.spider_opened)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_opened(self, spider):
        self.duplicates[spider] = set()

    def spider_closed(self, spider):
        del self.duplicates[spider]

    def process_item(self, item, spider):
        if not self._item_valid(item):
            raise DropItem
        if not item['id'] in self.duplicates[spider] and not self._item_exists(item):
            self._item_save(item)
        return item

    def _item_valid(self, item):
        # ISSUE #1: Data for 'Perroni, Ana María' is unavailable.
        if isinstance(item, LegisladorItem):
            if item['apellido'] == u'Perroni' and item['nombre'] == u'Ana Maria':
                return False
        return True

    def _item_exists(self, item):
        # TODO
        return False

    def _item_save(self, item):
        # TODO
        pass

