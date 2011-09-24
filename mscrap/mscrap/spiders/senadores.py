# -*- coding: utf8 -*-
import re
from functools import partial
from urlparse import urljoin, parse_qs, urlparse

from mscrap.loaders import LegisladorItemLoader
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from scrapy.spider import BaseSpider

from mscrap.items import LegisladorItem

_RE_BLOQUE = re.compile(r'Bloque (.*)')
_RE_MANDATO_PERIODO = re.compile(ur'Período (\d{2}/\d{2}/\d{4}) - (\d{2}/\d{2}/\d{4})')


class SenadoresSpider(BaseSpider):
    name = 'senadores'
    allowed_domains = ['senado.gov.ar']
    start_urls = [
        "http://www.senado.gov.ar/web/senadores/senadores.php?iOrden=0&iSen=ASC&Page=1&iPageSize=500"
    ]

    def parse(self, response):
        hxs = HtmlXPathSelector(response)

        senadores = hxs.select('//table[@bordercolor="#ece8e1"]/tbody/tr[position()>1]')
        for sen in senadores:
            l = LegisladorItemLoader(item=LegisladorItem(), selector=sen)

            apellido, nombre = sen.select('td[2]/text()').re(r'(.*?),(.*)')
            l.add_value('apellido', apellido)
            l.add_value('nombre', nombre)
            l.add_xpath('distrito_nombre', 'text()[1]')
            l.add_xpath('partido_nombre', 'text()[2]')
            l.add_value('camara', 'S')

            l.add_value('resource_source', u"http://www.senado.gov.ar/web/senadores/senadores.php")
            resource_url = urljoin(response.url, sen.select('td[2]/@onclick').re(r"^location\.href = '(.*?)'")[0])
            l.add_value('resource_url', resource_url)
            resource_id = parse_qs(urlparse(resource_url).query)['id_sena'][0]
            l.add_value('resource_id', resource_id)
            l.add_value('id', 'senador:%s' % resource_id)

            yield Request(resource_url, callback=partial(self._parse_senador_bio_page, l=l))

    def _parse_senador_bio_page(self, response, l):
        hxs = HtmlXPathSelector(response)
        _t = hxs.select(r'//td[@class="titulos"]/parent::tr[1]/following-sibling::*/td/table')

        # Bloque
        s = _t.select('.//tr[2]//text()').extract()[0]
        l.add_value('bloque_nombre', _RE_BLOQUE.search(s).group(1))

        # Mandato
        s = _t.select('.//tr[4]//text()').extract()[0]
        mandato_inicio, mandato_fin = _RE_MANDATO_PERIODO.search(s).groups()
        l.add_value('mandato_inicio', mandato_inicio)
        l.add_value('mandato_fin', mandato_fin)

        # Email
        s = _t.select('.//tr[6]//a[@class="textolink"]/text()').extract()[0]
        l.add_value('email', s)

        # Foto
        s = hxs.select('//img[starts-with(@src, "fsena/")]/@src').extract()[0].strip()
        l.add_value('foto_url',
            urljoin(response.url, s))

        yield l.load_item()


SPIDER = SenadoresSpider()
