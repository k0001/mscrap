# -*- coding: utf8 -*-

import re
import unicodedata
import urllib

from BeautifulSoup import BeautifulSoup

from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.loader import XPathItemLoader, ItemLoader
from scrapy.http import Request, FormRequest

from mscrap.loaders import ProyectoItemLoader, FirmaProyectoItemLoader, TramiteProyectoItemLoader, \
                           DictamenProyectoItemLoader

from mscrap.utils import pad_list, first_or_value, normalize_firmante_special, normalize_camara

_RE_EXPEDIENTE = re.compile(r'(\d{1,4})-([A-Za-z]+)-(\d{1,4})')
_RE_REPRODUCCION = re.compile(r'\([^\)\(]*?REPRODUCCI[OÓ]N.*?\)', re.U)
_RE_DICTAMEN_OD = re.compile(r'orden *del *dia.*?(\d+.+?\d+)') # <- just trying to be lax
_RE_TIPO_PROYECTO = re.compile(r'proyecto de (\w+)', re.U)
_RE_MENSAJE_CODIGO = re.compile(r'mensaje .*?(\d+/\d+)')



class DiputadosProyectosSpider(BaseSpider):
    name = 'diputados_proyectos'
    allowed_domains = ["www1.hcdn.gov.ar"]

    def start_requests(self):
        # parece que quieren que tenga una cookie de sesion.
        yield Request("http://www1.hcdn.gov.ar/proyectos_search/qryfrmg_combo.asp", callback=lambda r: None)
        yield FormRequest("http://www1.hcdn.gov.ar/proyectos_search/proyectosd.asp?giro_giradoA=&odanno=&" \
                          "pageorig=1&fromForm=1&whichpage=1&fecha_inicio=01/01/2005&fecha_fin=31/12/2011",
                          formdata={'dia_fin': '31',
                                    'mes_fin': '12',
                                    'anio_fin': '2020',
                                    'mes_inicio': '01',
                                    'dia_inicio': '01',
                                    'anio_inicio': '2005',
                                    'chkcomisiones': 'on',
                                    'chkdictamenes': 'on',
                                    'chkfirmantes': 'on',
                                    'chktramite': 'on',
                                    'ordenar': '3',
                                    'pagesize': '200',
                                    'selcomision': '0',
                                    'selsearchOptions': 'and'},
                            callback=self.parse)

    def parse(self, response):
        hxs = HtmlXPathSelector(response)
        pages_qty = hxs.select('//*[contains(.,"Página 1 de")]').re('de (\d+)')[0]

        for p in xrange(int(pages_qty)):
            yield Request("http://www1.hcdn.gov.ar/proyectos_search/proyectosd.asp?pagesize=50&giro_giradoA=&" \
                          "chkFirmantes=on&chkTramite=on&chkDictamenes=on&chkComisiones=on&titulo=&tipo_de_proy=&" \
                          "diputado=&ultResultado=&ordenar=3&pageorig=1&whichpage=%s" % (p+1),
                          callback=self.parse_proyectos)



    def parse_proyectos(self, response):
        # el html de diputados.gov.ar es TAN asqueroso que tengo que prettifiarlo con BeautifulSoup
        # antes de poder consultarlo con XPath
        hxs = HtmlXPathSelector(text=BeautifulSoup(response.body).prettify())

        for ul in hxs.select('//body/ul[contains(@class, "toc")]'):
            l = ProyectoItemLoader(selector=ul)


            # Tipo.
            # Ex: 'PROYECTO DE DECLARACION'
            tipo_verbose = ul.select('li/span/b[1]/text()').extract()[0].strip().lower()

            m = _RE_TIPO_PROYECTO.search(tipo_verbose)
            if m:
                tipo = m.group(1)
                l.add_value('tipo', tipo)
            else:
                # Could be just a plain mensaje,
                if 'mensaje' in tipo_verbose:
                    l.add_value('tipo', u'M') # <- gets normalized later.
                else:
                    l.add_value('tipo', None)
                    with open('/tmp/fr2346', 'ab') as f:
                        print >> f, tipo_verbose.encode('utf8')

            # Mensaje: Código.
            m = _RE_MENSAJE_CODIGO.search(tipo_verbose)
            if m:
                l.add_value('mensaje_codigo', m.group(1))
            else:
                l.add_value('mensaje_codigo', None)

            # Origen: Camara
            camara_origen = normalize_camara(ul.select('child::*//b[contains(., "Iniciado")]//following-sibling::text()[1]').extract()[0].strip().upper())
            l.add_value('camara_origen', camara_origen)

            # Origen: Expediente
            # Ex: '1453-S-2010'
            camara_origen_expediente = first_or_value(ul.select('child::*//b[contains(., "Iniciado")]//following-sibling::b[1]/following-sibling::text()[1]').extract()).strip().upper()
            l.add_value('camara_origen_expediente', camara_origen_expediente)

            # Origen: (de donde surge el proyecto, no necesariamente una cámara)
            if   '-S-'   in camara_origen_expediente: origen = 'S' # Senadores
            elif '-D-'   in camara_origen_expediente: origen = 'D' # Diputados
            elif '-CD-'  in camara_origen_expediente: origen = 'D' # Diputados (siendo revisado en el senado)
            elif '-PE-'  in camara_origen_expediente: origen = 'E' # Poder Ejecutivo
            elif '-JGM-' in camara_origen_expediente: origen = 'J' # Jefe de Gabinete de Ministros
            elif '-OV-'  in camara_origen_expediente: origen = 'O' # Organismos Oficiales
            elif '-OVD-' in camara_origen_expediente: origen = 'O' # Organismos Oficiales (siendo revisado en el senado)
            elif '-P-'   in camara_origen_expediente: origen = 'P' # Particulares

            l.add_value('origen', origen)

            # Publicación
            # Ex: 'Diario de Asuntos Entrados'
            l.add_xpath('publicacion_en',
                'child::*//b[contains(., "Publicado en")]//following-sibling::text()[1]')

            # Publicación: Fecha
            # Ex: '19/05/2010'
            l.add_xpath('publicacion_fecha',
                'child::*//b[contains(., "Publicado en")]//following-sibling::b[contains(., "Fecha")][1]/following-sibling::text()[1]')

            # Cámara Revisora:
            l.add_xpath('camara_revisora', 'child::*//b[contains(., "Cámara revisora")]//following-sibling::text()[1]')

            # Cámara Revisora: Expediente
            # XXX ésto anda?
            camara_revisora_expediente = first_or_value(ul.select('child::*//b[contains(., "Cámara revisora")]//following-sibling::b[1]/following-sibling::text()[1]').extract()).strip().upper()
            l.add_value('camara_revisora_expediente', camara_revisora_expediente)

            # Resource data
            l.add_value('id', 'proyecto:%s:%s' % (camara_origen, camara_origen_expediente))
            l.add_value('resource_id', 'proyecto:%s:%s' % (camara_origen, camara_origen_expediente))
            l.add_value('resource_source', u'www1.hcdn.gov.ar')
            proyecto_resource_url = self._get_proyecto_url(camara_origen, camara_origen_expediente)
            l.add_value('resource_url', proyecto_resource_url)

            # Ley Número
            # XXX checkear
            l.add_xpath('ley_numero',
                'child::*//div[contains(@style, "underline") and contains(., "LEY")]/text()',
                re=r'LEY ([\.\d]+)')

            # Sumario
            # Ex: 'ADHERIR AL ANIVERSARIO DEL DIARIO DIGITAL "JUJUY AL DIA".'
            sumario = first_or_value(ul.select('child::*//hr[1]/following-sibling::text()[1]').extract())
            l.add_value('sumario', sumario)

            # Reproducción: Codigo Expediente
            if 'REPRODUCCI' in sumario:
                m = _RE_REPRODUCCION.search(sumario)
                if m:
                    m1 = _RE_EXPEDIENTE.search(m.group(0))
                    if m1:
                        l.add_value('reproduccion_expediente', m1.group(0))
            else:
                l.add_value('reproduccion_expediente', None)

            # Senado URL Texto
            # Ex: javascript:OpenWindow("http://www.senado.gov.ar/web/proyectos/verExpe.php?origen=S&nro_comision=&tipo=PD&numexp=1449/10&tConsulta=3",400,400)
            l.add_xpath('texto_completo_url',
                'child::*//a[contains(., "Texto completo del proyecto")]/@href',
                re=r'OpenWindow\("(.*)"')

            # Diputados URL Texto
            # XXX checkear
            l.add_xpath('texto_mediasancion_diputados_url',
                'parent::*//a[contains(., "Texto de la media sanción en Diputados")]/@href',
                re=r'OpenWindow\("(.*)"')

            # Senado URL
            # XXX checkear
            l.add_xpath('texto_mediasancion_senadores_url',
                'parent::*//a[contains(@href, "senado.gov.ar") and contains(., "Media sanción")]/@href')


            # Firmantes
            _firmantes_seen = set()
            for i,tr in enumerate(ul.select('child::*//table//td[contains(., "FIRMANTES:")]//parent::tr/following-sibling::tr')):
                assert len(tr.select('td/text()')) == 3

                nombre_completo = tr.select('td[1]/text()').extract()[0].strip()

                if nombre_completo in _firmantes_seen:
                    continue # sometimes the same firmante is listed more than twice, see Diputados 1326-D-2010
                _firmantes_seen.add(nombre_completo)

                fpl = FirmaProyectoItemLoader(selector=tr)

                if i == 0:
                    fpl.add_value('tipo_firma', 'F')
                else:
                    fpl.add_value('tipo_firma', 'C')

                # proyecto
                fpl.add_value('proyecto_camara_origen', camara_origen)
                fpl.add_value('proyecto_camara_origen_expediente', camara_origen_expediente)

                try:
                    # firmante_special (non-human 'special' firmantes takes precedence)
                    fpl.add_value('firmante_special', normalize_firmante_special(nombre_completo))
                    fpl.add_value('firmante_apellido', None)
                    fpl.add_value('firmante_nombre', None)
                except KeyError:
                    fpl.add_value('firmante_special', None)
                    apellido, nombre = pad_list(nombre_completo.split(','), 2) # <-- ape could be missing
                    # firmante_apellido
                    fpl.add_value('firmante_apellido', apellido)
                    # firmante_nombre
                    fpl.add_value('firmante_nombre', nombre)

                # firmante_poder
                if tr.select('td[2][contains(., "PODER EJECUTIVO")]/text()').extract():
                    fpl.add_value('firmante_poder', u'E')
                else:
                    fpl.add_value('firmante_poder', u'L')

                # firmante_bloque_nombre
                fpl.add_xpath('firmante_bloque',
                    'td[2][not(contains(., "PODER EJECUTIVO"))]/text()')

                # firmante_distrito_nombre
                fpl.add_xpath('firmante_distrito',
                    'td[3]/text()')

                # Resource
                fpl.add_value('id', 'firma:%s:%s' % (camara_origen_expediente, nombre_completo))
                fpl.add_value('resource_url', proyecto_resource_url)
                fpl.add_value('resource_source', u'www1.hcdn.gov.ar')

                yield fpl.load_item()


            # Giro a comisiones en DIPUTADOS
            comisiones_diputados = []
            for tr in ul.select('child::*//table//td[contains(., "GIRO A COMISIONES EN DIPUTADOS:")]//../following-sibling::tr'):
                if tr.select('*[contains(@align, "left")]').extract():
                    break
                comisiones_diputados.append(first_or_value(tr.select('td/text()').extract()))
            l.add_value('comisiones_diputados', comisiones_diputados)

            # Giro a comisiones en SENADORES
            comisiones_senadores = []
            for tr in ul.select('child::*//table//td[contains(., "GIRO A COMISIONES EN SENADO:")]//../following-sibling::tr'):
                if tr.select('*[contains(@align, "left")]').extract():
                    break
                comisiones_senadores.append(first_or_value(tr.select('td/text()').extract()))
            l.add_value('comisiones_senadores', comisiones_senadores)


            # Dictamenes
            for i,tr in enumerate(ul.select('child::*//table//td[contains(., "DICTAMENES DE COMISION:")]//parent::tr/following-sibling::tr')):
                dpl = DictamenProyectoItemLoader(selector=tr)

                # index: we keep this value so that we can later sort this dictamenes list.
                dpl.add_value('index', '%s' % i)

                # proyecto
                dpl.add_value('proyecto_camara_origen', camara_origen)
                dpl.add_value('proyecto_camara_origen_expediente', camara_origen_expediente)

                # camara
                camara = tr.select('td[1]/text()').extract()[0].strip()
                dpl.add_value('camara', camara)

                # descripcion
                descripcion = tr.select('td[2]/text()').extract()[0].strip()
                dpl.add_value('descripcion', descripcion)

                # orden_del_dia (could be missing)
                # NOTE: The ':40' here is to lower the error margin for the regex match
                s = unicodedata.normalize('NFD', descripcion[:36]).encode('ascii', 'ignore').lower()
                m = _RE_DICTAMEN_OD.search(s)
                if m:
                    dpl.add_value('orden_del_dia', m.group(1))

                # fecha (could be missing)
                fecha = first_or_value(tr.select('td[3]/text()').extract()).strip()
                dpl.add_value('fecha', fecha)

                # resultado (could be missing)
                dpl.add_xpath('resultado', 'td[4]/text()')

                # Resource
                dpl.add_value('id', 'dictamen:%s:%s:%s:%s' % (camara_origen_expediente, camara, descripcion, fecha))
                dpl.add_value('resource_url', proyecto_resource_url)
                dpl.add_value('resource_source', u'www1.hcdn.gov.ar')

                yield dpl.load_item()

            # Tramites
            for i,tr in enumerate(ul.select('child::*//table//td[contains(., "TRAMITE:")]//parent::tr/following-sibling::tr')):
                tpl = TramiteProyectoItemLoader(selector=tr)

                # index: we keep this value so that we can later sort this tramites list.
                tpl.add_value('index', '%s' % i)

                # proyecto
                tpl.add_value('proyecto_camara_origen', camara_origen)
                tpl.add_value('proyecto_camara_origen_expediente', camara_origen_expediente)

                assert len(tr.select('td/text()')) == 4

                # camara
                camara = tr.select('td[1]/text()').extract()[0].strip()
                tpl.add_value('camara', camara)

                # descripcion
                descripcion = tr.select('td[2]/text()').extract()[0].strip()
                tpl.add_value('descripcion', descripcion)

                # fecha
                fecha = tr.select('td[3]/text()').extract()[0].strip()
                tpl.add_value('fecha', fecha)

                # resultado
                tpl.add_xpath('resultado',
                    'td[4]/text()')

                # Resource
                tpl.add_value('id', 'tramite:%s:%s:%s:%s' % (camara_origen_expediente, camara, descripcion, fecha))
                tpl.add_value('resource_url', proyecto_resource_url)
                tpl.add_value('resource_source', u'www1.hcdn.gov.ar')

                yield tpl.load_item()

            yield l.load_item()


    def _get_proyecto_url(self, camara_origen, camara_origen_expediente):
        if camara_origen == 'D':
            proy_iniciado = u'Diputados'
        elif camara_origen == 'S':
            proy_iniciado = u'Senado'
        else:
            raise ValueError(camara_origen)

        # XXX is this OK?
        m = _RE_EXPEDIENTE.match(camara_origen_expediente.strip())
        if not m:
            raise ValueError(camara_origen_expediente)

        return u'http://www1.hcdn.gov.ar/proyectos_search/proyectosd.asp?%s' % \
            urllib.urlencode({
                'proy_iniciado' : proy_iniciado,
                'proy_expdipN'  : m.group(1),
                'proy_expdipT'  : m.group(2),
                'proy_expdipA'  : m.group(3),
                'whichpage'     : '1',
                'chkComisiones' : 'on',
                'chkDictamenes' : 'on',
                'chkFirmantes'  : 'on',
                'chkTramite'    : 'on' })





SPIDER = DiputadosProyectosSpider()

