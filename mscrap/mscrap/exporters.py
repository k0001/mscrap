# -*- coding: utf8 -*-

from scrapy.contrib.exporter import JsonLinesItemExporter


class TypedJsonLinesItemExporter(JsonLinesItemExporter):
    """
    Like JsonLinesItemExporter but each line adds the item type.

    Example:
        ['LegisladorItem', {...LegisladorItem data...}]
    """

    def export_item(self, item):
        itemtype = item.__class__.__name__
        itemdict = dict(self._get_serialized_fields(item))
        self.file.write(self.encoder.encode([itemtype, itemdict]) + '\n')

