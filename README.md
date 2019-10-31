# Chordsheet

Chordsheet is a piece of software that generates a chord sheet, with a simple GUI.
It can load and save chordsheets in its own XML-based format, and can save them in PDF format for printing.

I wrote Chordsheet because no other software offered what I was looking for. I did not want to have to enter lyrics (most of the music I am charting is instrumental anyway), needed definite timing information, and wanted to be able to represent guitar chords (with a view to supporting other instruments in future).

Chordsheet works on a system of blocks, each with a certain length. Blocks may have an assigned chord, or additional information. These blocks can then be ordered and the output generated. 

## Current status

Chordsheet is alpha-grade software. At present, the program will crash readily given user input it doesn't expect. 
### Limitations
- No support for multiple pages
- Only guitar chords can be entered and shown
- No support for lyrics or melody (use something else!)
- PDF preview is blurry on high DPI monitors
- Chord names and notes can spill out of their block if it's not big enough
- Poor font handling (choice of either FreeSans or Helvetica Neue if installed)

## Dependencies
Chordsheet depends on pymupdf (to show the preview), reportlab (to generate the PDF), and PyQt5 (for the GUI).
Also, a font that supports musical symbols is required. A copy of FreeSans is bundled (in the fonts folder).