# -*- coding: utf8 -*-

import re
from urlparse import urljoin
from functools import partial

from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
from scrapy.spider import BaseSpider

from mscrap.loaders import LegisladorItemLoader


_RE_RESOURCE_ID = re.compile(r'http://webappl.hcdn.gov.ar/diputados/([-\w]+)')

class DiputadosSpider(BaseSpider):
    name = 'diputados'
    allowed_domains = ['webappl.hcdn.gov.ar']
    start_urls = 'http://webappl.hcdn.gov.ar/diputados/listadodiputados.html',

    def parse(self, response):
        hxs = HtmlXPathSelector(response)

        dipus = hxs.select('//div[@id="tablaPpal"]//table//tr/td[2]/a')
        for dipu in dipus:
            apellido, nombre = dipu.select('text()').extract()[0].split(',')
            resource_id = dipu.select('@href').extract()[0]
            resource_url = urljoin(response.url, resource_id)
            item_data = {
                'apellido': apellido,
                'nombre': nombre,
                'resource_id': resource_id,
                'resource_url': resource_url }
            yield Request(resource_url, callback=partial(self.parse_diputado, item_data=item_data))

    def parse_diputado(self, response, item_data):
        hxs = HtmlXPathSelector(response)
        #uname =  urlsplit(response.url).path.split('/')[-1]

        l = LegisladorItemLoader(selector=hxs.select('//div[@id="page"]//div[@class="primera"]'))

        l.add_value('id', item_data['resource_url']) # unique enough :)

        l.add_value('resource_source', u'webappl.hcdn.gov.ar')
        l.add_value('resource_id', item_data['resource_id'])
        l.add_value('resource_url', item_data['resource_url'])

        l.add_value('camara', 'D')
        l.add_value('nombre', item_data['nombre'])
        l.add_value('apellido', item_data['apellido'])

        l.add_xpath('foto_url', './/img[@alt="Foto del legislador"]/@src')
        l.add_xpath('bloque_nombre', './/*[@class="quinto1"][3]/p/text()')
        l.add_xpath('distrito_nombre', './/div[@class="cuarto1"]/p[contains(., "Distrito:")]/text()',
                                       re='Distrito:\xa0 ([a-zA-Z0-9 ]+)')
        l.add_xpath('mandato_inicio', './/div[@class="quinto1"]/p[contains(., "Mandato:")]/text()',
                                      re=r'.*(\d\d/\d\d/\d\d\d\d)\xa0-.*')
        l.add_xpath('mandato_fin', './/div[@class="quinto1"]/p[contains(., "Mandato:")]/text()',
                                   re=r'.*-\xa0(\d\d/\d\d/\d\d\d\d)$')
        l.add_xpath('email', './/div[@class="quinto1"]/p[contains(., "E-Mail:")]/a/text()')
        l.add_xpath('telefono', './/div[@class="cuarto1"]/p[contains(., "Teléfono:")]/text()', re='([-\d]+)')

        yield l.load_item()


SPIDER = DiputadosSpider()
