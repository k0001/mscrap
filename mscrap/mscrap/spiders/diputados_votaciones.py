# -*- coding: utf8 -*-

import re
from urlparse import urljoin
from functools import partial

from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
from scrapy.spider import BaseSpider

from mscrap.loaders import ActaVotacionItemLoader
from mscrap.utils import un, fix_space, first_or_value


_RE_RESOURCE_ID = re.compile(r'http://webappl.hcdn.gov.ar/diputados/([-\w]+)')
_RE_SESION = re.compile(r"""
        (?P<reunion_fecha>\d+[-/]\d+[-/]\d+)
        .*?
        (?P<reunion_num>\d+)\ reunion
        .*?
        (?P<sesion_num>\d+)\ sesion\ (?P<sesion_tipo>(?:
                                                       |ordinaria
                                                       |extraordinaria)
                                                  \ ?(?:de\ tablas?
                                                       |especial
                                                       |de\ prorroga
                                                       |en\ minoria
                                                       |de\ prorroga\ de\ tablas
                                                       |de\ prorroga\ especial))$""", re.X)
_RE_PERIODO = re.compile(r"periodo (?P<periodo_num>\d+) - ano (?P<year_inicio>\d+) - (?P<year_fin>\d+)")


class DiputadosVotacionesSpider(BaseSpider):
    name = 'diputados_votaciones'
    allowed_domains = ['www1.hcdn.gov.ar']
    start_urls = [
        'http://www1.hcdn.gov.ar/dependencias/dselectronicos/actas/2010/actas2010.htm',
        'http://www1.hcdn.gov.ar/dependencias/dselectronicos/actas/2009/actas2009.htm',
        'http://www1.hcdn.gov.ar/dependencias/dselectronicos/actas/2008/actas2008.htm',
        'http://www1.hcdn.gov.ar/dependencias/dselectronicos/actas/2007/actas2007.htm',

        # Not tested:
        #'http://www1.hcdn.gov.ar/dependencias/dselectronicos/actas/2006/actas2006.htm',
        #'http://www1.hcdn.gov.ar/dependencias/dselectronicos/actas/2005/actas2005.htm',
        #'http://www1.hcdn.gov.ar/dependencias/dselectronicos/actas/2004/actas2004.htm',
        #'http://www1.hcdn.gov.ar/dependencias/dselectronicos/actas/2003/actas2003.htm',
        #'http://www1.hcdn.gov.ar/dependencias/dselectronicos/actas/2002/actas2002.htm',
        #'http://www1.hcdn.gov.ar/dependencias/dselectronicos/actas/2001/actas2001.htm',

        # 2000 and older PDFs are just image scans
    ]


    def parse(self, response):
        year = int(re.search(r'/(\d{4})/', response.url).group(1))

        hxs = HtmlXPathSelector(response)
        for url in hxs.select('/html/body/p//a[contains(., "-")]/@href').extract():
            yield Request(urljoin(response.url, url), callback=partial(self.parse_sesion, year=year))

    def parse_sesion(self, response, year):
        hxs = HtmlXPathSelector(response)
        data = {}

        s = fix_space(un(u' '.join(hxs.select('/html/body/p[2]/b//text()').extract())), True)
        s = re.sub(r'reunion (\d+)', r'\1 reunion', s)
        m = _RE_SESION.match(s)
        if not m:
            print repr(s)
        data.update(m.groupdict())


        s = fix_space(un(' '.join(hxs.select('/html/body/table/tr/td//b/text()').extract()), True))
        m = _RE_PERIODO.search(s)
        data.update(m.groupdict())

        for tr in hxs.select('/html/body//tr[contains(., "Bajar")]'):
            l = ActaVotacionItemLoader(selector=tr)


            # NOTE: I have no reason for indenting this like I do.
            #       But writing scrappers can get boring sometimes, you know.
            foo = un(u' '.join(tr.select('.//*[preceding-sibling::a[contains(., "Bajar")]]/ancestor::td//text()').extract()))
            if     'nominal' in foo: l.add_value('tipo', 'nominal')
            elif  'numerica' in foo: l.add_value('tipo', 'numerica')
            else                   : raise ValueError(u'Not "nominal" nor "numerica" in "%s"' % foo)
            # -^v^-^v^-^v^-^v^-^v^-^v^-^v^-^v^-^v^-^v^-^v^-^v^-^v^-^v^-^v^-^v^-^v^-^v^-^v^-^v^-^v^
            if     'negativ' in foo: l.add_value('resultado', 'negativa')
            elif 'afirmativ' in foo: l.add_value('resultado', 'afirmativa')
            else                   : raise ValueError(u'Not "afirmativa" nor "negativa" in "%s"' % foo)


            acta_pdf_url = urljoin(response.url, tr.select('.//a[contains(., "Bajar")]/@href').extract()[0])

            l.add_value('camara', 'D')
            l.add_value('reunion_fecha', data['reunion_fecha'])
            l.add_value('reunion_numero', data['reunion_num'])
            l.add_value('sesion_numero', data['sesion_num'])
            l.add_value('sesion_tipo', data['sesion_tipo'])
            l.add_value('year_inicio', data['year_inicio'])
            l.add_value('year_fin', data['year_fin'])
            l.add_xpath('acta_descripcion', 'td[2]/p/font/span/text()')
            l.add_value('acta_pdf_url', acta_pdf_url)
            l.add_value('id', acta_pdf_url)
            l.add_value('resource_url', acta_pdf_url)
            l.add_value('resource_id', acta_pdf_url)
            l.add_value('resource_source', u"http://www1.hcdn.gov.ar/dependencias/dselectronicos/actasvotaciones.html")

            yield l.load_item()


SPIDER = DiputadosVotacionesSpider()
