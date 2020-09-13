## This project has moved to https://git.radivan.net/ivan/chordsheet. All future releases and development will occur there.

# Chordsheet
Chordsheet is a piece of software that generates a chord sheet, with a simple GUI.
It can load and save chordsheets in its own XML-based format, and can save them in PDF format for printing.

I wrote Chordsheet because no other software offered what I was looking for. I did not want to have to enter lyrics (most of the music I am charting is instrumental anyway), needed definite timing information, and wanted to be able to represent guitar chords (with a view to supporting other instruments in future).

Chordsheet works on a system of blocks, each with a certain length. Blocks may have an assigned chord, or additional information. These blocks can then be ordered and the output generated. 

## Get started
To run Chordsheet, go to the Releases tab and download the most recent version for your OS. Releases are currently provided for macOS and Windows. These binaries are created with PyInstaller and so can't be used for development. You do not need to install anything else to run Chordsheet this way.

To develop Chordsheet, clone this repository and run gui.py using a recent Python 3 interpreter. Make sure you have the dependencies installed!

## Current status
Chordsheet is alpha-grade software. At present, the program will crash readily given user input it doesn't expect. 

### Limitations
- Only guitar chords can be entered and shown
- No support for lyrics or melody (use something else!)
- PDF preview is blurry on high DPI monitors
- Chord names and notes can spill out of their block if it's not big enough (partially remedied by allowing the user to change the beat width)
- Poor font handling (choice of either FreeSans or Helvetica Neue if installed)
- No support for printing

## Dependencies
Chordsheet depends on pymupdf (to show the preview), reportlab (to generate the PDF), and PyQt5 (for the GUI).
Also, a font that supports musical symbols is required. A copy of FreeSans is bundled (in the fonts folder).
This command should sort you out:
```bash
pip3 install pymupdf reportlab pyqt5
```

## License
Chordsheet is licensed under the AGPLv3, included in full in 'LICENSE'.
