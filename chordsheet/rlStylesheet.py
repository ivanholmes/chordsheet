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

    # stylesheet.add(ParagraphStyle(name='Heading3',
    #                               parent=stylesheet['Normal'],
    #                               fontName = csStyle.font,
    #                               fontSize=12,
    #                               leading=14,
    #                               spaceBefore=12,
    #                               spaceAfter=6),
    #                alias='h3')

    # stylesheet.add(ParagraphStyle(name='Heading4',
    #                               parent=stylesheet['Normal'],
    #                               fontName = csStyle.font,
    #                               fontSize=10,
    #                               leading=12,
    #                               spaceBefore=10,
    #                               spaceAfter=4),
    #                alias='h4')

    # stylesheet.add(ParagraphStyle(name='Heading5',
    #                               parent=stylesheet['Normal'],
    #                               fontName = csStyle.font,
    #                               fontSize=9,
    #                               leading=10.8,
    #                               spaceBefore=8,
    #                               spaceAfter=4),
    #                alias='h5')

    # stylesheet.add(ParagraphStyle(name='Heading6',
    #                               parent=stylesheet['Normal'],
    #                               fontName = csStyle.font,
    #                               fontSize=7,
    #                               leading=8.4,
    #                               spaceBefore=6,
    #                               spaceAfter=2),
    #                alias='h6')

    # stylesheet.add(ParagraphStyle(name='Bullet',
    #                               parent=stylesheet['Normal'],
    #                               firstLineIndent=0,
    #                               spaceBefore=3),
    #                alias='bu')

    # stylesheet.add(ParagraphStyle(name='Definition',
    #                               parent=stylesheet['Normal'],
    #                               firstLineIndent=0,
    #                               leftIndent=36,
    #                               bulletIndent=0,
    #                               spaceBefore=6,
    #                               bulletFontName=csStyle.font),
    #                alias='df')

    # stylesheet.add(ParagraphStyle(name='Code',
    #                               parent=stylesheet['Normal'],
    #                               fontName='Courier',
    #                               fontSize=8,
    #                               leading=8.8,
    #                               firstLineIndent=0,
    #                               leftIndent=36,
    #                               hyphenationLang=''))

    return stylesheet