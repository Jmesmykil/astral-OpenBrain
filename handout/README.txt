OpenBrain meeting handout: 2026-09-04
=======================================

FILES
  OpenBrain-Handout.html   the source. One self-contained file: print CSS, inline SVG
                           figures, no external images, no scripts, no network requests.
                           Open it in any browser; File > Print gives the same 13 pages.
  OpenBrain-Handout.pdf    the primary deliverable. A4, 13 pages, rendered from the HTML
                           with headless Chrome.
  OpenBrain-Handout.docx   a Word version, converted from the HTML with macOS `textutil`.

ABOUT THE DOCX
  Neither `pandoc` nor `python-docx` is installed on this machine, so the DOCX was made
  with the built-in macOS converter:

      textutil -convert docx -output OpenBrain-Handout.docx OpenBrain-Handout.html

  The inline SVG figures do NOT survive that conversion: the DOCX carries the text,
  headings and tables only. The PDF is the version to hand over or print; the DOCX is for
  anyone who needs to edit the wording.

  If you want a DOCX that keeps the figures, either of these works:

  1. Word opens HTML directly.
       Open OpenBrain-Handout.html in Microsoft Word, then File > Save As > .docx.
       Word keeps the layout and most of the vector figures.

  2. Install pandoc and re-convert:
       brew install pandoc
       pandoc OpenBrain-Handout.html -o OpenBrain-Handout.docx
       (pandoc also drops inline SVG; use route 1 if the figures matter.)

RE-RENDERING THE PDF AFTER AN EDIT
  Edit OpenBrain-Handout.html, then:

      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
        --headless=new --disable-gpu --no-pdf-header-footer \
        --print-to-pdf=OpenBrain-Handout.pdf OpenBrain-Handout.html

  Each printed page is one <section class="sheet"> of fixed height (296 mm). If you add
  text to a section, check it still fits inside its own sheet: content that overruns a
  sheet is not pushed to a new page, it runs under the footer rule. The page numbers come
  from a CSS counter over those sheets, and the total ("of 13") is written in the
  .folio .pg::after rule near the top of the file; update it if you add or remove a sheet.

SOURCES
  Every number in the handout is taken from MEETING-SCRIPT.md, GRANT-APPLICATION.md,
  MEETING.md, README.md or KNOWN-BUGS.md in the parent directory, plus the demo
  line-by-line figures supplied for section 7, and the repository list for section 5.
  Nothing is estimated or rounded up.

  Page 8 is "Previous work": the three public OpenHome repositories under the account
  Jmesmykil are linked in full; the private ones are named "private, available on request".
  The document is complete. There are no blanks left to fill in before the meeting.
