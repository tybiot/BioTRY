# -*- coding: utf-8 -*-
"""
chemdataextractor.parse.by
~~~~~~~~~~~~~~~~~~~~~~~~~~~

biosyn text parser.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re

from .cem import cem, chemical_label, lenient_chemical_label, solvent_name
from .common import lbrct, dt, rbrct
from ..utils import first
from ..model import Compound, BiosynYield
from .actions import merge, join
from .base import BaseParser
from .elements import W, I, R, Optional, Any, OneOrMore, Not, ZeroOrMore

log = logging.getLogger(__name__)

prefix = Optional(I('to') + I('and') + I('range') + Optional(I('of'))) | I('obtained')

delim = R('^[:;\.,]$')

# TODO: Consider allowing degree symbol to be optional. The prefix should be restrictive enough to stop false positives.
units = (W('mg')+Optional(W('/'))+ W('L') )('units').add_action(merge)
#units = (W('°') + Optional(R('^[CFK]\.?$')) | W('K\.?'))('units').add_action(merge)

joined_range = R('^[\+\-–−]?\d+(\.\d+)?[\-–−~∼˜]\d+(\.\d+)?$')('value').add_action(merge)
spaced_range = (R('^[\+\-–−]?\d+(\.\d+)?$') + Optional(units).hide() + (R('^[\-–−~∼˜]$') + R('^[\+\-–−]?\d+(\.\d+)?$') | R('^[\+\-–−]\d+(\.\d+)?$')))('value').add_action(merge)
to_range = (R('^[\+\-–−]?\d+(\.\d+)?$') + Optional(units).hide() + (I('to') + R('^[\+\-–−]?\d+(\.\d+)?$') | R('^[\+\-–−]\d+(\.\d+)?$')))('value').add_action(join)
temp_range = (Optional(R('^[\-–−]$')) + (joined_range | spaced_range | to_range))('value').add_action(merge)
temp_value = (Optional(R('^[~∼˜\<\>]$')) + Optional(R('^[\-–−]$')) + R('^[\+\-–−]?\d+(\.\d+)?$'))('value').add_action(merge)
temp = Optional(lbrct).hide() + (temp_range | temp_value)('value') + Optional(rbrct).hide()

mp = (prefix + Optional(delim).hide() + temp + units)('mp')


bracket_any = lbrct + OneOrMore(Not(mp) + Not(rbrct) + Any()) + rbrct

solvent_phrase = (R('^(re)?crystalli[sz](ation|ed)$', re.I) + (I('with') | I('from')) + cem | solvent_name)
cem_mp_phrase = (Optional(solvent_phrase).hide() + Optional(cem) + Optional(I('having')).hide() + Optional(delim).hide() + Optional(bracket_any).hide() + Optional(delim).hide() + Optional(lbrct) + mp + Optional(rbrct))('mp_phrase')
to_give_mp_phrase = ((I('to') + (I('give') | I('afford') | I('yield') | I('obtain')) | I('affording') | I('afforded') | I('gave') | I('yielded')).hide() + Optional(dt).hide() + (cem | chemical_label | lenient_chemical_label) + ZeroOrMore(Not(mp) + Not(cem) + Any()).hide() + mp)('mp_phrase')
obtained_mp_phrase = ((cem | chemical_label) + (I('is') | I('are') | I('was')).hide() + (I('afforded') | I('obtained') | I('yielded')).hide() + ZeroOrMore(Not(mp) + Not(cem) + Any()).hide() + mp)('mp_phrase')
#ty_test = (I('obtained') |mp)('mp')
mp_phrase = cem_mp_phrase | to_give_mp_phrase | obtained_mp_phrase

class ByParser(BaseParser):
    """"""
    root = mp_phrase
    # print ('outside parser', mp_phrase, type(mp_phrase))
    #print (ty_test, type(ty_test))
    #print("1"*10)
    #root = ty_test


    def interpret(self, result, start, end):
        #print (type(result))
        #print (result.xpath('./mp/value/text()'))
        #print (type(result.xpath('./mp/value/')))
        #print("3"*10)


        compound = Compound(
            biosyn_yields=[
                BiosynYield(
                    value=first(result.xpath('./mp/value/text()')),
                    units=first(result.xpath('./mp/units/text()'))
                )
            ]
        )
        cem_el = first(result.xpath('./cem'))
        if cem_el is not None:
            compound.names = cem_el.xpath('./name/text()')
            compound.labels = cem_el.xpath('./label/text()')
        yield compound
