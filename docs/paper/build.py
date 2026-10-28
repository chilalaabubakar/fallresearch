"""Build the manuscript (Word) from the Markdown sources, in the house style of
the authors' earlier manuscript: US Letter, Times New Roman 10 pt, 1.5 line
spacing, justified, numbered headings "1. Introduction" / "2.1 ...", bold
"Table N." captions above three-line tables, bold "Figure N." captions below
figures, numbered equations, author-year citations and an alphabetical
reference list with hanging indent.

    python docs/paper/build.py

* Citations [@key] or [@a; @b] become (Author et al. 2023; ...); after a name
  already in the sentence ("Riboldi and Nord [@riboldi2018]") only the year is
  kept: "Riboldi and Nord (2018)". Entries come from references.yaml.
* Caption blocks "> **Fig. N.** ..." become the image with "Figure N." below.
* {{TABLE_S1}} in the supplementary material becomes the parameter table.
* Checks: 3-5 highlights of at most 85 characters, abstract of at most 250
  words; prints the word count and the references still marked "check".
Outputs: paper.docx, supplementary.docx and highlights.docx in docs/paper/ (and cover_letter.docx when a
private cover_letter.md is present).
"""

import copy
import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import pandas as pd
import yaml
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIGURE_WIDTH = "16cm"  # = topside.style.PRINT_WIDTH_IN
# Figure label -> image (results/paper/, made by python -m topside.figures)
FIGURES = {"1": "fig00_system", "2": "fig02_demand_map", "3": "fig04_cases", "4": "fig05_example_week",
           "5": "fig06_gt_load_duration", "6": "fig07_injection_mechanism",
           "7": "fig09_sensitivity_overview", "8": "fig12_demand_reserve_map",
           "9": "fig10_validation", "10": "fig11_multi_year",
           "S1": "fig01_wind_resource", "S2": "fig03_gt_part_load", "S3": "fig08_monthly_co2"}
MAX_HIGHLIGHT_CHARS, HIGHLIGHTS = 85, (3, 5)
MAX_ABSTRACT_WORDS = 250
CITE = re.compile(r"\[(@[\w-]+(?:\s*;\s*@[\w-]+)*)\]")
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"

# House style
FONT, SIZE, LINE = "Times New Roman", Pt(10), 1.5
PAGE_W, PAGE_H, MARGIN = Cm(21.59), Cm(27.94), Cm(2.54)
HANGING = Cm(0.8)


# --------------------------------------------------------------------------
# Author-year citations
# --------------------------------------------------------------------------
def _is_person(name):
    return re.fullmatch(r"[^\s,]+(?:[\s-][^\s,]+)*\s[A-Z][A-Z-]*", name.strip()) is not None


def authors_of(entry):
    return re.match(r"^(.*?)\.\s", entry["text"]).group(1)


def short_label(entry):
    """'Svendsen HG, Vrana TK, ...' -> 'Svendsen et al.'; organisations keep their name."""
    if "label" in entry:
        return entry["label"]
    names = [n.strip() for n in authors_of(entry).split(",") if n.strip() and n.strip() != "et al"]
    etal = "et al" in authors_of(entry)
    if all(_is_person(n) for n in names):
        surnames = [n.rsplit(" ", 1)[0] for n in names]
        if len(surnames) == 1 and not etal:
            return surnames[0]
        if len(surnames) == 2 and not etal:
            return f"{surnames[0]} and {surnames[1]}"
        return f"{surnames[0]} et al."
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return names[0] if len(names) == 1 else f"{names[0]} et al."


def year_of(key, entry):
    if "year" in entry:
        return str(entry["year"])
    m = re.search(r"(19|20)\d\d$", key)
    return m.group(0) if m else "n.d."


def citation_labels(refs):
    """key -> (label, year with a/b suffix where label and year coincide)."""
    base = {k: (short_label(v), year_of(k, v)) for k, v in refs.items()}
    groups = {}
    for k, ly in sorted(base.items(), key=lambda kv: kv[0]):
        groups.setdefault(ly, []).append(k)
    out = {}
    for (label, year), keys in groups.items():
        for i, k in enumerate(sorted(keys, key=lambda k: refs[k]["text"])):
            out[k] = (label, year + ("abcdefgh"[i] if len(keys) > 1 else ""))
    return out


def author_year_citations(markdown, refs):
    labels = citation_labels(refs)
    cited = []

    def repl(m):
        keys = [k.strip().lstrip("@") for k in m.group(1).split(";")]
        for k in keys:
            if k not in refs:
                raise KeyError(f"unknown reference [@{k}]")
            if k not in cited:
                cited.append(k)
        before = " ".join(markdown[max(0, m.start() - 120):m.start()].split())
        if len(keys) == 1 and before.endswith(labels[keys[0]][0]):
            return f"({labels[keys[0]][1]})"                       # narrative: "Svendsen (2022)"
        parts, by_label = [], {}
        for k in keys:
            label, year = labels[k]
            by_label.setdefault(label, []).append(year)
        for label, years in by_label.items():
            parts.append(f"{label} {', '.join(years)}")
        return "(" + "; ".join(parts) + ")"

    markdown = CITE.sub(repl, markdown)
    return markdown, cited, labels


def reference_entry(key, entry, labels):
    """'Authors. Title. Energy 2013;55:716–27. doi' -> 'Authors (2013) Title. Energy 55:716–27. doi'."""
    authors = authors_of(entry)
    rest = entry["text"][len(authors) + 1:].strip()
    year = labels[key][1]
    plain = re.sub(r"[a-h]$", "", year)
    if plain != "n.d.":
        rest = re.sub(rf"(\S)\s{plain};", r"\1 ", rest)          # journal year before volume
        rest = re.sub(rf";\s*{plain}\.", ".", rest)               # '; 2021.' after publisher
        rest = re.sub(rf"\.\s{plain}\.$", ".", rest)               # trailing '. 2022.' 
    if authors.endswith("et al"):
        authors += "."
    return f"{authors} ({year}) {rest}"


def reference_list(cited, refs, labels):
    def sort_key(k):
        s = unicodedata.normalize("NFKD", authors_of(refs[k])).encode("ascii", "ignore").decode().lower()
        return (s, labels[k][1])
    return "\n\n".join(reference_entry(k, refs[k], labels) for k in sorted(cited, key=sort_key))


# --------------------------------------------------------------------------
# Markdown -> house-style Markdown
# --------------------------------------------------------------------------
def house_markdown(markdown):
    lines = markdown.split("\n")
    title = lines[0].lstrip("# ").strip() if lines[0].startswith("# ") else None
    body = "\n".join(lines[1:]) if title else markdown
    # numbered headings: "## 1 Introduction" -> "# 1. Introduction"; "### 2.1 X" -> "## 2.1 X"
    body = re.sub(r"(?m)^## (S?\d+) ", r"# \1. ", body)
    body = re.sub(r"(?m)^### ", "## ", body)
    body = re.sub(r"(?m)^## (?!\S*\d)", "# ", body)               # unnumbered sections
    # abstract heading -> bold run-in label
    body = re.sub(r"(?m)^# Abstract\s*\n+", "**Abstract.** ", body)
    # front matter: affiliations and corresponding author in their own styles
    # Author line: the first line after the title that carries the ^a^ affiliation mark
    body = re.sub(r"(?m)^(?!\^)([^\n#]*\^a[,^][^\n]*)$", r'::: {custom-style="Author"}\n\1\n:::', body, count=1)
    body = re.sub(r"(?m)^(\^[a-z]\^(?: \*[^\n]*\*)?)$", r'::: {custom-style="Affiliation"}\n\1\n:::', body)
    # "Fig. 3" in the text -> "Figure 3" (captions are rebuilt below)
    body = re.sub(r"(?<!\*\*)\bFigs?\. (S?\d)", lambda m: "Figure " + m.group(1), body)
    return title, body


def insert_figures(markdown):
    def repl(m):
        block = re.sub(r"^>\s?", "", m.group(0), flags=re.M).strip()
        label = re.match(r"\*\*Fig\. (S?\d+)\.\*\*", block).group(1)
        path = (ROOT / "results" / "paper" / f"{FIGURES[label]}.png").relative_to(ROOT).as_posix()
        if not (ROOT / path).exists():
            raise FileNotFoundError(f"{path} (run python -m topside.figures)")
        caption = " ".join(block.split()).replace(f"**Fig. {label}.**", f"**Figure {label}.**", 1)
        return (f'::: {{custom-style="Figure"}}\n![]({path}){{width={FIGURE_WIDTH}}}\n:::\n\n'
                f'::: {{custom-style="Figure Caption"}}\n{caption}\n:::\n')
    return re.sub(r"(?m)^> \*\*Fig\. S?\d+\.\*\*.*(?:\n>.*)*", repl, markdown)


def parameter_table():
    t = pd.read_csv(ROOT / "results" / "paper" / "tables" / "T1_parameters.csv")
    t = t[["parameter", "value", "unit", "source"]].fillna("")
    for c in t:
        t[c] = t[c].astype(str).str.replace("|", "/", regex=False)
    return t.to_markdown(index=False)


# --------------------------------------------------------------------------
# Word styling
# --------------------------------------------------------------------------
def _set_font(style, size=SIZE, bold=None, italic=None):
    style.font.name = FONT
    style.font.size = size
    style.font.color.rgb = RGBColor(0, 0, 0)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(attr), FONT)
    for theme in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        fonts.attrib.pop(qn(theme), None)


def _para(style, before=0, after=6, align=WD_ALIGN_PARAGRAPH.JUSTIFY, line=LINE, indent=None, hanging=None,
          keep_next=None):
    pf = style.paragraph_format
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    pf.alignment = align
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = line
    pf.first_line_indent = -hanging if hanging else indent
    if hanging:
        pf.left_indent = hanging
    if keep_next is not None:
        pf.keep_with_next = keep_next


def _style(doc, name, base="Normal"):
    """Style by its exact name (pandoc writes 'Heading 1', which python-docx would
    otherwise translate to the built-in 'heading 1'); created if missing."""
    from docx.enum.style import WD_STYLE_TYPE
    for st in doc.styles:
        if st.name == name:
            return st
    st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    st.base_style = _style(doc, base) if base != name else None
    return st


def reference_doc(path):
    """pandoc's default reference.docx restyled to the house style."""
    subprocess.run(["pandoc", "-o", str(path), "--print-default-data-file", "reference.docx"], check=True)
    doc = Document(path)
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.PORTRAIT
    sec.page_width, sec.page_height = PAGE_W, PAGE_H
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, MARGIN)
    for name in ("Normal", "Body Text", "First Paragraph", "Compact", "Block Text", "Bibliography",
                 "Table", "Author", "Affiliation", "Figure", "Figure Caption", "Captioned Figure",
                 "Image Caption", "Table Caption", "Abstract", "Date", "Footnote Text"):
        _set_font(_style(doc, name))
    for name in ("Normal", "Body Text", "First Paragraph", "Block Text"):
        _para(_style(doc, name), after=6)
    _para(_style(doc, "Compact"), after=2)
    _para(_style(doc, "Author"), before=6, after=6, align=WD_ALIGN_PARAGRAPH.LEFT)
    _set_font(_style(doc, "Affiliation"), italic=True)
    _para(_style(doc, "Affiliation"), after=4, align=WD_ALIGN_PARAGRAPH.LEFT)
    _para(_style(doc, "Figure"), before=6, after=0, align=WD_ALIGN_PARAGRAPH.CENTER, line=1.0, keep_next=True)
    _para(_style(doc, "Figure Caption"), before=4, after=10)
    _para(_style(doc, "Bibliography"), after=4, hanging=HANGING, align=WD_ALIGN_PARAGRAPH.LEFT)  # long URLs
    title = _style(doc, "Title")
    _set_font(title, size=SIZE, bold=True)
    ppr = title.element.get_or_add_pPr()
    for old in ppr.findall(qn("w:pBdr")):                      # no rule under the title
        ppr.remove(old)
    _para(_style(doc, "Title"), before=0, after=12, align=WD_ALIGN_PARAGRAPH.LEFT)
    for level, before in (("Heading 1", 14), ("Heading 2", 10), ("Heading 3", 8)):
        st = _style(doc, level)
        _set_font(st, bold=True, italic=False)
        _para(st, before=before, after=6, align=WD_ALIGN_PARAGRAPH.LEFT, keep_next=True)
    for name in ("Hyperlink",):
        try:
            _style(doc, name).font.color.rgb = RGBColor(0, 0, 0)
            _style(doc, name).font.underline = False
        except KeyError:
            pass
    # centred page number in the footer
    footer = sec.footer.paragraphs[0] if sec.footer.paragraphs else sec.footer.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for text, kind in (("", "begin"), (" PAGE ", None), ("", "end")):
        run = footer.add_run()
        if kind:
            fld = OxmlElement("w:fldChar")
            fld.set(qn("w:fldCharType"), kind)
            run._r.append(fld)
        else:
            instr = OxmlElement("w:instrText")
            instr.set(qn("xml:space"), "preserve")
            instr.text = text
            run._r.append(instr)
    doc.save(path)
    return path


def _border(tag, val="single", sz="4"):
    el = OxmlElement(f"w:{tag}")
    el.set(qn("w:val"), val)
    el.set(qn("w:sz"), sz)
    el.set(qn("w:space"), "0")
    el.set(qn("w:color"), "000000")
    return el


def full_width_columns(table, text_width=Cm(16.51), min_share=0.08):
    """Table across the text width, columns in proportion to their longest line of text."""
    pr = table._tbl.tblPr
    w = pr.find(qn("w:tblW"))
    if w is None:
        w = OxmlElement("w:tblW")
        pr.append(w)
    w.set(qn("w:type"), "pct")
    w.set(qn("w:w"), "5000")
    ncol = len(table.columns)
    need = [1] * ncol
    for row in table.rows:
        for j, cell in enumerate(row.cells[:ncol]):
            longest = max((len(word) for word in cell.text.split()), default=1)
            need[j] = max(need[j], min(len(cell.text), 40), longest)
    share = [max(n / sum(need), min_share) for n in need]
    share = [x / sum(share) for x in share]
    widths = [int(text_width.twips * x) for x in share]
    for col, tw in zip(table._tbl.tblGrid.findall(qn("w:gridCol")), widths):
        col.set(qn("w:w"), str(tw))
    for row in table.rows:
        for cell, tw in zip(row.cells, widths):
            cell.width = tw * 635  # twips -> EMU


def three_line_tables(doc, skip=()):
    """Rule above the table, below the header and at the bottom; header bold."""
    for t in doc.tables:
        if t._tbl in skip:
            continue
        pr = t._tbl.tblPr
        for old in pr.findall(qn("w:tblBorders")):
            pr.remove(old)
        full_width_columns(t)
        borders = OxmlElement("w:tblBorders")
        for tag in ("top", "bottom"):
            borders.append(_border(tag))
        for tag in ("left", "right", "insideH", "insideV"):
            borders.append(_border(tag, "nil"))
        pr.append(borders)
        for cell in t.rows[0].cells:
            tcpr = cell._tc.get_or_add_tcPr()
            tcb = OxmlElement("w:tcBorders")
            tcb.append(_border("bottom"))
            tcpr.append(tcb)
            for p in cell.paragraphs:
                for r in p.runs:
                    r.bold = True
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.line_spacing = 1.0
                    p.paragraph_format.space_after = Pt(1)
                    for r in p.runs:
                        r.font.size = SIZE
        # Space between the bottom rule and the text that follows
        nxt = t._tbl.getnext()
        if nxt is not None and nxt.tag == qn("w:p"):
            Paragraph(nxt, t._parent).paragraph_format.space_before = Pt(10)


def numbered_equations(doc):
    """Display equations -> borderless 3-column table: blank | equation | (n)."""
    tables = []
    n = 0
    for p in list(doc.paragraphs):
        para = p._p.find(f"{M}oMathPara")
        if para is None or p.text.strip():
            continue
        n += 1
        t = doc.add_table(rows=1, cols=3)
        tbl = t._tbl
        pr = tbl.tblPr
        borders = OxmlElement("w:tblBorders")
        for tag in ("top", "left", "bottom", "right", "insideH", "insideV"):
            borders.append(_border(tag, "nil"))
        pr.append(borders)
        # The default table style rules off the first row; an equation table has
        # only one row, so switch the header formatting off and clear cell borders.
        look = pr.find(qn("w:tblLook"))
        if look is not None:
            look.set(qn("w:firstRow"), "0")
            look.set(qn("w:firstColumn"), "0")
            look.set(qn("w:val"), "0000")
        widths = (Cm(1.2), Cm(13.3), Cm(1.5))
        for col, w in zip(tbl.tblGrid.findall(qn("w:gridCol")), widths):
            col.set(qn("w:w"), str(int(w.twips)))
        for cell, w in zip(t.rows[0].cells, widths):
            cell.width = w
            tcb = OxmlElement("w:tcBorders")
            for tag in ("top", "left", "bottom", "right"):
                tcb.append(_border(tag, "nil"))
            cell._tc.get_or_add_tcPr().append(tcb)
        mid, right = t.rows[0].cells[1].paragraphs[0], t.rows[0].cells[2].paragraphs[0]
        mid.alignment = WD_ALIGN_PARAGRAPH.CENTER
        mid._p.append(copy.deepcopy(para))
        right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        right.add_run(f"({n})").font.size = SIZE
        for q in (mid, right):
            q.paragraph_format.space_before = Pt(3)
            q.paragraph_format.space_after = Pt(3)
        p._p.addprevious(tbl)
        p._p.getparent().remove(p._p)
        tables.append(tbl)
    return tables


def reference_paragraphs(doc):
    started = False
    for p in doc.paragraphs:
        if p.style.name in ("Heading 1", "heading 1") and p.text.strip() == "References":
            started = True
            continue
        if started and p.text.strip():
            p.style = _style(doc, "Bibliography")


def to_docx(markdown, out, title=None, references=False):
    ref = HERE / ".reference_house.docx"
    reference_doc(ref)
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tmp:
        if title:
            tmp.write("---\ntitle: " + yaml.safe_dump(title, allow_unicode=True).strip() + "\n---\n\n")
        tmp.write(markdown)
    subprocess.run(["pandoc", tmp.name, "-f", "markdown", "-t", "docx", "-o", str(out),
                    "--resource-path", str(ROOT), "--reference-doc", str(ref)], check=True)
    Path(tmp.name).unlink()
    ref.unlink()
    doc = Document(out)
    eq_tables = numbered_equations(doc)
    three_line_tables(doc, skip=set(eq_tables))
    if references:
        reference_paragraphs(doc)
    doc.save(out)
    return out


# --------------------------------------------------------------------------
# Checks and main
# --------------------------------------------------------------------------
def words(text):
    text = re.sub(r"(?m)^\|.*$", "", text)            # tables
    text = re.sub(r"(?m)^>.*$", "", text)             # figure captions
    text = re.sub(r"\$\$.*?\$\$", "", text, flags=re.S)
    text = re.sub(r"~(\w+)~", r"\1", text)             # subscripts such as CO~2~
    return len(re.findall(r"[A-Za-z0-9][\w'’–-]*", text))


def section(md, start, end):
    return md[md.index(start): md.index(end)]


def check_highlights(md):
    items = [l[2:].strip() for l in md.splitlines() if l.startswith("* ")]
    problems = [f"{len(h)} chars: {h}" for h in items if len(h) > MAX_HIGHLIGHT_CHARS]
    if not HIGHLIGHTS[0] <= len(items) <= HIGHLIGHTS[1]:
        problems.append(f"{len(items)} highlights (need {HIGHLIGHTS[0]}-{HIGHLIGHTS[1]})")
    return items, problems


def main():
    refs = yaml.safe_load((HERE / "references.yaml").read_text(encoding="utf-8"))
    paper = (HERE / "paper.md").read_text(encoding="utf-8")
    n_abstract = words(section(paper, "## Abstract", "**Keywords:**")) - 1
    n_body = words(section(paper, "## 1 Introduction", "## Nomenclature"))
    md, cited, labels = author_year_citations(paper, refs)
    md = md.replace("{{REFERENCES}}", reference_list(cited, refs, labels))
    title, md = house_markdown(md)
    print("Saved", to_docx(insert_figures(md), HERE / "paper.docx", title=title, references=True))

    supp = (HERE / "supplementary.md").read_text(encoding="utf-8").replace("{{TABLE_S1}}", parameter_table())
    stitle, supp = house_markdown(supp)
    print("Saved", to_docx(insert_figures(supp), HERE / "supplementary.docx", title=stitle))

    letter = HERE / "cover_letter.md"
    if letter.exists():
        print("Saved", to_docx(letter.read_text(encoding="utf-8"), HERE / "cover_letter.docx"))

    hl = (HERE / "highlights.md").read_text(encoding="utf-8")
    items, problems = check_highlights(hl)
    htitle, hmd = house_markdown(hl)
    print("Saved", to_docx(hmd, HERE / "highlights.docx", title=htitle))

    print(f"\nAbstract: {n_abstract} words (limit {MAX_ABSTRACT_WORDS})"
          + ("  ** TOO LONG **" if n_abstract > MAX_ABSTRACT_WORDS else ""))
    print(f"Main text (Introduction to Conclusions, without tables and captions): {n_body} words")
    print(f"Highlights: {len(items)}, longest {max(map(len, items))} characters"
          + "".join(f"\n  ** {p}" for p in problems))
    unused = sorted(set(refs) - set(cited))
    print(f"References cited: {len(cited)}" + (f"; not cited: {', '.join(unused)}" if unused else ""))
    to_check = [f"{labels[k][0]} {labels[k][1]} ({k})" for k in cited if refs[k].get("check")]
    if to_check:
        print("References to confirm against the original:\n  " + "\n  ".join(to_check))


if __name__ == "__main__":
    main()
