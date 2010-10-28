# Scrapy settings for mscrap project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
# Or you can copy and paste them from where they're defined in Scrapy:
#
#     scrapy/conf/default_settings.py
#

import os

_HERE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.join(_HERE_DIR, '..')

LOG_LEVEL = 'WARNING'

BOT_NAME = 'mscrap'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['mscrap.spiders']
NEWSPIDER_MODULE = 'mscrap.spiders'
#DEFAULT_ITEM_CLASS = 'mscrap.items.LegisladorItem'
USER_AGENT = '%s/%s' % (BOT_NAME, BOT_VERSION)
ITEM_PIPELINES = [
    'mscrap.pipelines.MscrapPipeline'
]

FEED_EXPORTERS = {
    'typedjsonlines': 'mscrap.exporters.TypedJsonLinesItemExporter'
}
FEED_FORMAT = 'typedjsonlines'
FEED_URI = 'file://'+ os.path.join(_ROOT_DIR, 'mscrap-%(name)s-%(time)s.jsonlines')


