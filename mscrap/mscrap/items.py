# -*- coding: utf8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

import time
from datetime import date

from scrapy.item import Item, Field
from scrapy.contrib.loader.processor import TakeFirst, MapCompose, Compose

from mscrap.utils import fix_space, spanish_date, format_personal_name



class MscrapBaseItem(Item):
    # Internal item id. Set it to something unique among items of the same class.
    id = Field()
    # Remote resource data.
    resource_source = Field()
    resource_id = Field()
    resource_url = Field()


class LegisladorItem(MscrapBaseItem):
    camara = Field()
    apellido = Field()
    nombre = Field()
    distrito_nombre = Field()
    bloque_nombre = Field()
    partido_nombre = Field()
    foto_url = Field()
    email = Field()
    telefono = Field()
    mandato_inicio = Field()
    mandato_fin = Field()


class FirmaProyectoItem(MscrapBaseItem):
    proyecto_camara_origen = Field()
    proyecto_camara_origen_expediente = Field()
    tipo_firma = Field()
    firmante_nombre = Field()
    firmante_apellido = Field()
    firmante_bloque = Field()
    firmante_poder = Field()
    firmante_distrito = Field()
    # A veces el que firma no es un tipo. Esto tiene prioridad ante el nombre.
    firmante_special = Field()


class TramiteProyectoItem(MscrapBaseItem):
    proyecto_camara_origen = Field()
    proyecto_camara_origen_expediente = Field()
    camara = Field()
    descripcion = Field()
    fecha = Field()
    resultado = Field()


class DictamenProyectoItem(MscrapBaseItem):
    proyecto_camara_origen = Field()
    proyecto_camara_origen_expediente = Field()
    camara = Field()
    descripcion = Field()
    orden_del_dia = Field()
    fecha = Field()
    resultado = Field()


class ProyectoItem(MscrapBaseItem):
    tipo = Field()
    camara_origen = Field()
    camara_origen_expediente = Field()
    origen = Field()
    reproduccion_expediente = Field()
    publicacion_en = Field()
    publicacion_fecha = Field()
    camara_revisora = Field()
    camara_revisora_expediente = Field()
    mensaje_codigo = Field()
    ley_numero = Field()
    sumario = Field()
    texto_completo_url = Field()
    texto_mediasancion_senadores_url = Field()
    texto_mediasancion_diputados_url = Field()
    comisiones_diputados = Field()
    comisiones_senadores = Field()

