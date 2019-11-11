# -*- coding: utf-8 -*-

from reportlab.lib.styles import StyleSheet1, ParagraphStyle
from reportlab.lib.enums import *
from reportlab.lib.units import mm
from reportlab.lib.colors import black

def getStyleSheet(csStyle):
    """Returns a stylesheet object"""
    stylesheet = StyleSheet1()

    stylesheet.add(ParagraphStyle(name='Master',
                                  fontname=csStyle.font))
    
    stylesheet.add(ParagraphStyle(name='Title',
                                  leading=csStyle.lineSpacing*csStyle.titleFontSize,
                                  fontSize=csStyle.titleFontSize,
                                  alignment=TA_CENTER,
                                  parent=stylesheet['Master'])
                   )

    stylesheet.add(ParagraphStyle(name='Subtitle',
                                  leading=csStyle.lineSpacing*csStyle.subtitleFontSize,
                                  fontSize=csStyle.subtitleFontSize,
                                  alignment=TA_CENTER,
                                  parent=stylesheet['Master'])
                   )
    stylesheet.add(ParagraphStyle(name='Credits',
                                  leading=csStyle.lineSpacing*csStyle.creditsFontSize,
                                  fontSize=csStyle.creditsFontSize,
                                  alignment=TA_CENTER,
                                  parent=stylesheet['Master'])
                   )

    stylesheet.add(ParagraphStyle(name='Tempo',
                                  leading=csStyle.lineSpacing*csStyle.tempoFontSize,
                                  fontSize=csStyle.tempoFontSize,
                                  alignment=TA_LEFT,
                                  parent=stylesheet['Master'])
                   )

    stylesheet.add(ParagraphStyle(name='Heading',
                                  leading=csStyle.lineSpacing*csStyle.headingFontSize,
                                  fontSize=csStyle.headingFontSize,
                                  alignment=TA_LEFT,
                                  parent=stylesheet['Master'], 
                                  spaceAfter=2*mm)
                   )

    return stylesheet