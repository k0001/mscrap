# -*- coding: utf8 -*-

from functools import partial
from datetime import date

from scrapy.contrib.loader import XPathItemLoader
from scrapy.contrib.loader.processor import TakeFirst, MapCompose, Compose, Identity

from mscrap.items import LegisladorItem, ProyectoItem, FirmaProyectoItem, TramiteProyectoItem, \
                         DictamenProyectoItem, ActaVotacionItem

from mscrap.utils import (
        fix_space,
        digits_only,
        spanish_date,
        format_personal_name,
        normalize_distrito_name,
        normalize_camara,
        normalize_proyecto_origen,
        normalize_codigo_expediente,
        normalize_orden_del_dia,
        normalize_codigo_mensaje,
        normalize_tipo_proyecto,
        normalize_firmante_special,
        normalize_poder,
        normalize_publicacion_en,
        normalize_bloque_name,
        normalize_sesion_tipo,
        normalize_votacion_resultado,
        normalize_votacion_tipo) # <-- what a mess D:


class LegisladorItemLoader(XPathItemLoader):
    default_item_class = LegisladorItem
    default_input_processor = MapCompose(fix_space, unicode.strip)
    default_output_processor = TakeFirst()

    apellido_in = MapCompose(fix_space, format_personal_name)
    nombre_in = MapCompose(fix_space, format_personal_name)
    camara_in = MapCompose(fix_space, unicode.strip, normalize_camara)
    distrito_nombre_in = MapCompose(fix_space, unicode.strip, normalize_distrito_name)
    bloque_nombre_in = MapCompose(fix_space, unicode.strip, normalize_bloque_name)

    mandato_inicio_in = MapCompose(fix_space, unicode.strip, spanish_date)
    mandato_inicio_out = Compose(lambda v: v[0].isoformat())

    mandato_fin_in = MapCompose(fix_space, unicode.strip, spanish_date)
    mandato_fin_out = Compose(lambda v: v[0].isoformat())


class ProyectoItemLoader(XPathItemLoader):
    default_item_class = ProyectoItem
    default_input_processor = MapCompose(fix_space, unicode.strip)
    default_output_processor = TakeFirst()

    tipo_in = MapCompose(fix_space, unicode.strip, normalize_tipo_proyecto)
    camara_origen_in = MapCompose(fix_space, unicode.strip, normalize_camara)
    camara_origen_expediente_in = MapCompose(fix_space, unicode.strip, normalize_codigo_expediente)
    origen_in = MapCompose(fix_space, unicode.strip, normalize_proyecto_origen)
    reproduccion_expediente_in = MapCompose(fix_space, unicode.strip, partial(normalize_codigo_expediente, allow_empty=True))
    camara_revisora_in = MapCompose(fix_space, unicode.strip, partial(normalize_camara, allow_empty=True))
    camara_revisora_expediente_in = MapCompose(fix_space, unicode.strip, partial(normalize_codigo_expediente, allow_empty=True))
    ley_numero_in = MapCompose(fix_space, unicode.strip, digits_only)
    mensaje_codigo_in = MapCompose(fix_space, unicode.strip, partial(normalize_codigo_mensaje, allow_empty=True))


    publicacion_en_in = MapCompose(fix_space, unicode.strip, partial(normalize_publicacion_en, allow_empty=True))
    publicacion_fecha_in = MapCompose(fix_space, unicode.strip, spanish_date)
    publicacion_fecha_out = Compose(lambda v: v[0].isoformat())

    comisiones_diputados_out = Identity()
    comisiones_senadores_out = Identity()


class FirmaProyectoItemLoader(XPathItemLoader):
    default_item_class = FirmaProyectoItem
    default_input_processor = MapCompose(fix_space, unicode.strip)
    default_output_processor = TakeFirst()

    proyecto_camara_origen_in = MapCompose(fix_space, unicode.strip, normalize_camara)
    proyecto_camara_origen_expediente_in = MapCompose(fix_space, unicode.strip, normalize_codigo_expediente)
    firmante_nombre_in = MapCompose(fix_space, format_personal_name)
    firmante_apellido_in = MapCompose(fix_space, format_personal_name)
    firmante_distrito_in = MapCompose(fix_space, unicode.strip, partial(normalize_distrito_name, allow_empty=True))
    firmante_special_in = MapCompose(fix_space, unicode.strip, normalize_firmante_special)
    firmante_poder_in = MapCompose(fix_space, unicode.strip, normalize_poder)
    firmante_bloque_in = MapCompose(fix_space, unicode.strip, partial(normalize_bloque_name, allow_empty=True))


class TramiteProyectoItemLoader(XPathItemLoader):
    default_item_class = TramiteProyectoItem
    default_input_processor = MapCompose(fix_space, unicode.strip)
    default_output_processor = TakeFirst()

    proyecto_camara_origen_in = MapCompose(fix_space, unicode.strip, normalize_camara)
    proyecto_camara_origen_expediente_in = MapCompose(fix_space, unicode.strip, normalize_codigo_expediente)
    camara_in = MapCompose(fix_space, unicode.strip, normalize_camara)
    fecha_in = MapCompose(fix_space, unicode.strip, partial(spanish_date, allow_empty=True))
    fecha_out = Compose(lambda v: v[0].isoformat())
    index_in = MapCompose(digits_only)


class DictamenProyectoItemLoader(XPathItemLoader):
    default_item_class = DictamenProyectoItem
    default_input_processor = MapCompose(fix_space, unicode.strip)
    default_output_processor = TakeFirst()

    proyecto_camara_origen_in = MapCompose(fix_space, unicode.strip, normalize_camara)
    proyecto_camara_origen_expediente_in = MapCompose(fix_space, unicode.strip, normalize_codigo_expediente)
    camara_in = MapCompose(fix_space, unicode.strip, normalize_camara)
    fecha_in = MapCompose(fix_space, unicode.strip, partial(spanish_date, allow_empty=True))
    fecha_out = Compose(lambda v: v[0].isoformat())
    orden_del_dia_in = MapCompose(fix_space, unicode.strip, normalize_orden_del_dia)
    index_in = MapCompose(digits_only)


class ActaVotacionItemLoader(XPathItemLoader):
    default_item_class = ActaVotacionItem
    default_input_processor = MapCompose(fix_space, unicode.strip)
    default_output_processor = TakeFirst()

    camara_in = MapCompose(fix_space, unicode.strip, normalize_camara)
    tipo_in = MapCompose(fix_space, unicode.strip, normalize_votacion_tipo)
    resultado_in = MapCompose(fix_space, unicode.strip, normalize_votacion_resultado)
    reunion_fecha_in = MapCompose(fix_space, unicode.strip, partial(spanish_date, allow_empty=True))
    reunion_fecha_out = Compose(lambda v: v[0].isoformat())
    sesion_tipo_in = MapCompose(fix_space, unicode.strip, normalize_sesion_tipo)

    sesion_numero_in = MapCompose(digits_only)
    reunion_numero_in = MapCompose(digits_only)
    year_inicio_in = MapCompose(digits_only)
    year_fin_in = MapCompose(digits_only)
