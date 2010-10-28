# -*- coding: utf-8 -*-

# XXX This file is a mess.


import re
import logging
import time
import unicodedata
from datetime import date

from mscrap import constants

log = logging.getLogger(__name__)


def first_or_value(l, value=u''):
    """ first element of l if len(l) > 0 or value """
    return l[0] if len(l) > 0 else value


def pad_list(l, n, pad=''):
    """ pad list l with value pad so len(l) == n """
    if len(l) < n:
      for i in range(n-len(l)): l.append(pad)
    return l

def format_personal_name(text):
    """Turns a personal name like 'JUAN CARLOS' or 'juan carlos' to 'Juan Carlos'"""
    return u' '.join(x.capitalize() for x in text.split())


_rx_whitespace = re.compile(r'(\s)+')
def fix_space(text):
    """Replaces non-breaking space for normal space. Remove duplicate whitespace."""
    text = text.strip().replace(u'\xa0', u' ').replace(u'\r\n', u'\n').replace(u'\r', u'\n')
    return _rx_whitespace.sub(r'\1', text)


def spanish_date(text, separator=None, allow_empty=False):
    """
    Parses a date string DD/MM/YYYY into a datetime.date object.

    If separator==None, then try to use separators: '/', '-', ''
    """
    if not text and allow_empty:
        return None
    separators = [separator] if separator else ('/', '-', '')
    for s in separators:
        fmt = '%d' + s + '%m' + s + '%Y'
        try:
            return date.fromtimestamp(time.mktime(time.strptime(text, fmt)))
        except ValueError:
            pass
    raise ValueError(text)

def dict_values_composer(compose):
    """Returns a function that, when called on a dict, applies ``compose`` to every dict value"""
    def _f(dic):
        return dict((k, compose(v)) for (k,v) in dic.iteritems())
    return _f


def normalize_distrito_name(text, allow_empty=False):
    text = text.strip()
    if not text and allow_empty:
        return None
    k = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').lower()
    return constants.DISTRITOS_NORM[k]

def normalize_bloque_name(text, allow_empty=False):
    """
    Normalizes bloque names.

    Prepends ':' to the given text if normalization not available.
    """
    text = fix_space(text)
    if not text and allow_empty:
        return None
    k = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').lower()
    if k in constants.BLOQUES_NORM:
        return constants.BLOQUES_NORM[k]
    else:
        log.warning(u"Bloque name not normalized: " + text)
        return u":" + text

def normalize_camara(text, allow_empty=False):
    """
    Normalize camara names.

    Turns ``text`` like 'Senado' or ' diputados' to their canonical names u'S' and u'D'

    If ``allow_empty``, then empty values are allowed and turned into None.
    """
    c = text.strip().upper()[:1]
    if not c and allow_empty:
        return None
    elif c in 'SD':
        return unicode(c)
    raise ValueError(text)

def normalize_proyecto_origen(text, allow_empty=False):
    """
    Normalize proyecto origen name

    Possible values are:
     - 'S' for Cámara de Senadores
     - 'D' for Cámara de Diputados
     - 'E' for Poder Ejecutivo
     - 'J' for Jefe de Gabinete
     - 'O' for Organismos Oficiales
     - 'P' for Particular

    If ``allow_empty``, then empty values are allowed, resulting in the canonical name u''
    """
    c = text.strip().upper()
    if not (c in 'SDEJOP' or (not c and not allow_empty)):
        raise ValueError(text)
    return unicode(c)


_rx_exp = re.compile(r'^(\d{1,4})-([A-Za-z]+)-(\d{1,4})$')
def normalize_codigo_expediente(text, allow_empty=False):
    """
    Normalizes codigo de expediente.

    Things like '114-D-08' are turned into '0114-D-2008'.
    """
    m = _rx_exp.match(text)
    if not m:
        if allow_empty:
            return None
        raise ValueError(text)

    a,b,c = m.groups()

    assert len(a) <= 4

    return u'%04d-%s-%d' % (int(a), b.upper(), normalize_year(c))


_rx_digits = re.compile(r'\d+')
def digits_only(text):
    """Keeps only the digits found in the input text"""
    return u''.join(_rx_digits.findall(text))


def normalize_orden_del_dia(text, allow_empty=False):
    """
    Normalizes orden del día codes.

    Things like '142/10', '0142-2010', '0142 10', etc. are turned into '142/2010'.
    """
    text = text.strip()
    if not text and allow_empty:
        return None
    try:
        number, year = _rx_digits.findall(text)
    except ValueError:
        raise ValueError(text)

    return u'%d/%d' % (int(number), normalize_year(year))

def normalize_codigo_mensaje(text, allow_empty=False):
    """
    Normalizes codigo mensaje

    Things like '142/10', '0142-2010', '0142 10', etc. are turned into '142/2010'.
    """
    text = text.strip()
    if not text and allow_empty:
        return None
    try:
        number, year = _rx_digits.findall(text)
    except ValueError:
        raise ValueError(text)

    return u'%d/%d' % (int(number), normalize_year(year))


def normalize_tipo_proyecto(text, allow_empty=False):
    """
    Normalizes tipo de proyecto.

    Things like 'PROYECTO DE LEY' are turned into 'L'
    """
    text = text.upper().strip()
    if not text and allow_empty:
        return None

    if len(text) == 1 and text in 'LRDCEM':
        return text

    if 'LEY' in text:
        return 'L'
    elif 'RESOLUCION' in text:
        return 'R'
    elif 'DECLARACION' in text:
        return 'D'
    elif 'COMUNICACION' in text:
        return 'C'
    elif 'DECRETO' in text:
        return 'E'
    elif 'MENSAJE' in text:
        return 'M'

    raise ValueError(text)


def normalize_year(val):
    """
    Normalizes a year as a 4 digit int.

    Things like 08 and 99 are turned into 2008 and 1999 respectively.

    From '00' till '80', we treat them as 20XX.
    From '81' till '99', we treat them as 19XX.

    Takes both int and str types.
    """
    c = int(val)
    if c <= 80:     # from '00' till '80', we treat them as 20XX
        c += 2000
    elif c <= 99:   # from '81' till '99', we treat them as 19XX
        c += 1900
    assert 1980 < c < 9999 # YEAH BABY! WE ARE GOING TO THE FUTURE!!1
    return c

def normalize_firmante_special(text, allow_empty=False):
    text = text.strip()
    if not text and allow_empty:
        return None
    k = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').lower()
    return constants.FIRMANTES_SPECIAL_NORM[k]

def normalize_poder(text, allow_empty=False):
    text = text.strip()
    if not text and allow_empty:
        return None
    k = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').lower()
    if u'ejecutivo' in k or 'e' == k:
        return u'E'
    elif u'legislativo' in k or 'l' == k: # not used, but just to be complete
        return u'L'
    elif u'judicial' in k or 'j' == k: # not used, but just in case
        return u'J'
    raise ValueError(text)

def normalize_publicacion_en(text, allow_empty=False):
    """
    Normalizes Publicacion En values.

    'Tramite Parlamentario n 35'    => u'Trámite Parlamentario 35'
    'Tramite Parlamentario'         => u'Trámite Parlamentario'
    'Diario de Asuntos Entrados 40' => u'Diario de Asuntos Entrados 40'
    'Diario de Asuntos Entrados'    => u'Diario de Asuntos Entrados'
    """
    text = text.strip()
    if not text and allow_empty:
        return None
    k = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').lower()
    k = re.sub(r'\s+', ' ', k)
    if 'parlamentario' in k:
        out = u'Trámite Parlamentario'
    elif 'asuntos' in k:
        out = u'Diario de Asuntos Entrados'
    else:
        raise ValueError(text)
    m = _rx_digits.search(k[::-1])
    if m:
        out += ' %s' % m.group(0)[::-1]
    return out




