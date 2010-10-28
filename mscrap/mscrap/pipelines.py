# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

#from scrapy.contrib.exporter.jsonlines import JsonLinesItemExporter
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher


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
        if not item['id'] in self.duplicates[spider] and not self._item_exists(item):
            self._item_save(item)
        return item

    def _item_exists(self, item):
        # TODO
        return False

    def _item_save(self, item):
        # TODO
        pass
