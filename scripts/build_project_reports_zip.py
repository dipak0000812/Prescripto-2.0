"""
Prescripto AI 2.0 — Academic Report & Documentation Packager
Converts all Markdown dossiers to professional DOCX and PDF formats and bundles them into a single ZIP archive.
Contains ONLY .docx and .pdf files.
"""

import os
import re
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import zipfile
import subprocess
from pathlib import Path

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

import markdown


def set_cell_background(cell, fill_hex):
    """Sets background color of a Word table cell."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets cell padding in dxa (1 pt = 20 dxa)."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def add_formatted_text(paragraph, text, is_bold=False, is_italic=False, is_code=False, font_size=10.5, font_color=None):
    """Parses inline bold, italic, code, and links in markdown lines."""
    # Pattern to match bold, italic, inline code, and links
    tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*|`.*?`|\[.*?\]\(.*?\))', text)
    for token in tokens:
        if not token:
            continue
        run = paragraph.add_run()
        run.font.name = 'Calibri'
        run.font.size = Pt(font_size)
        
        if token.startswith('**') and token.endswith('**') and len(token) >= 4:
            run.text = token[2:-2]
            run.bold = True
        elif token.startswith('*') and token.endswith('*') and len(token) >= 2:
            run.text = token[1:-1]
            run.italic = True
        elif token.startswith('`') and token.endswith('`') and len(token) >= 2:
            run.text = token[1:-1]
            run.font.name = 'Consolas'
            run.font.size = Pt(font_size - 1)
            run.font.color.rgb = RGBColor(180, 40, 40)
        elif token.startswith('[') and '](' in token and token.endswith(')'):
            m = re.match(r'\[(.*?)\]\((.*?)\)', token)
            if m:
                run.text = m.group(1)
                run.font.color.rgb = RGBColor(14, 116, 144)
                run.underline = True
            else:
                run.text = token
        else:
            run.text = token
            run.bold = is_bold
            run.italic = is_italic
        
        if font_color:
            run.font.color.rgb = font_color


def md_to_docx(md_path: Path, docx_path: Path):
    """Converts a Markdown file into a styled Microsoft Word document (.docx)."""
    doc = Document()
    
    # Page setup: Standard Letter / A4 with 1-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
    
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    i = 0
    in_code_block = False
    code_block_lines = []
    
    while i < len(lines):
        line = lines[i].rstrip('\r\n')
        
        # Check code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                # End code block
                code_text = '\n'.join(code_block_lines)
                table = doc.add_table(rows=1, cols=1)
                table.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = table.cell(0, 0)
                set_cell_background(cell, "F3F4F6")
                set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                run = p.add_run(code_text)
                run.font.name = 'Consolas'
                run.font.size = Pt(9.0)
                run.font.color.rgb = RGBColor(31, 41, 55)
                doc.add_paragraph()  # Spacing
                in_code_block = False
                code_block_lines = []
            else:
                in_code_block = True
                code_block_lines = []
            i += 1
            continue
            
        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue
            
        # Empty lines
        if not line.strip():
            i += 1
            continue
            
        # Check tables (Markdown pipe tables)
        if '|' in line and (line.strip().startswith('|') or line.count('|') >= 2):
            table_lines = [line]
            while i + 1 < len(lines) and '|' in lines[i + 1] and (lines[i + 1].strip().startswith('|') or lines[i + 1].count('|') >= 2):
                i += 1
                table_lines.append(lines[i].rstrip('\r\n'))
                
            # Filter separator lines (e.g. |---|---|)
            parsed_rows = []
            for tl in table_lines:
                cells = [c.strip() for c in tl.strip().strip('|').split('|')]
                if all(re.match(r'^:?-+:?$', c) for c in cells if c):
                    continue  # Separator row
                parsed_rows.append(cells)
                
            if parsed_rows:
                num_cols = max(len(r) for r in parsed_rows)
                # Pad rows to num_cols
                for r in parsed_rows:
                    while len(r) < num_cols:
                        r.append('')
                        
                table = doc.add_table(rows=len(parsed_rows), cols=num_cols)
                table.alignment = WD_TABLE_ALIGNMENT.CENTER
                table.autofit = True
                
                for row_idx, row_data in enumerate(parsed_rows):
                    is_header = (row_idx == 0)
                    for col_idx, cell_value in enumerate(row_data):
                        cell = table.cell(row_idx, col_idx)
                        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
                        if is_header:
                            set_cell_background(cell, "0F766E")  # Teal header
                        elif row_idx % 2 == 1:
                            set_cell_background(cell, "F8FAFC")  # Light zebra
                        else:
                            set_cell_background(cell, "FFFFFF")
                            
                        p = cell.paragraphs[0]
                        p.paragraph_format.space_before = Pt(2)
                        p.paragraph_format.space_after = Pt(2)
                        
                        if is_header:
                            add_formatted_text(p, cell_value, is_bold=True, font_size=9.5, font_color=RGBColor(255, 255, 255))
                        else:
                            add_formatted_text(p, cell_value, font_size=9.0)
                            
                doc.add_paragraph()  # Spacing
            i += 1
            continue
            
        # Headings
        if line.startswith('# '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(line[2:].strip())
            run.font.name = 'Calibri'
            run.font.size = Pt(20)
            run.font.bold = True
            run.font.color.rgb = RGBColor(15, 118, 110)  # Primary teal
        elif line.startswith('## '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(5)
            run = p.add_run(line[3:].strip())
            run.font.name = 'Calibri'
            run.font.size = Pt(15)
            run.font.bold = True
            run.font.color.rgb = RGBColor(30, 41, 59)  # Slate 800
        elif line.startswith('### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(line[4:].strip())
            run.font.name = 'Calibri'
            run.font.size = Pt(12.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(71, 85, 105)  # Slate 600
        elif line.startswith('#### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            run = p.add_run(line[5:].strip())
            run.font.name = 'Calibri'
            run.font.size = Pt(11)
            run.font.bold = True
            run.font.italic = True
        elif line.startswith('> '):
            # Blockquote
            table = doc.add_table(rows=1, cols=1)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            cell = table.cell(0, 0)
            set_cell_background(cell, "F0FDFA")
            set_cell_margins(cell, top=100, bottom=100, left=180, right=150)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            add_formatted_text(p, line[2:].strip(), is_italic=True, font_color=RGBColor(15, 118, 110))
        elif line.strip().startswith(('-', '*', '+ ')) and not line.strip().startswith('---'):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            clean_line = re.sub(r'^[\-\*\+]\s+', '', line.strip())
            add_formatted_text(p, clean_line)
        elif re.match(r'^\d+\.\s+', line.strip()):
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            clean_line = re.sub(r'^\d+\.\s+', '', line.strip())
            add_formatted_text(p, clean_line)
        elif line.strip() == '---':
            # Horizontal divider line
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run('—' * 55)
            run.font.color.rgb = RGBColor(203, 213, 225)
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_text(p, line)
            
        i += 1
        
    doc.save(str(docx_path))


def md_to_pdf_via_edge(md_path: Path, pdf_path: Path, edge_exe: str):
    """Converts a Markdown file to styled HTML and renders it to PDF using Microsoft Edge headless."""
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
        
    # Convert markdown to HTML with tables, fenced code, and attr_list extensions
    html_body = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'attr_list'])
    
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{md_path.stem}</title>
<style>
  @page {{
    size: A4;
    margin: 20mm 18mm 20mm 18mm;
    @bottom-right {{
      content: counter(page);
    }}
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    font-size: 10pt;
    line-height: 1.5;
    background-color: #ffffff;
  }}
  h1 {{
    color: #0f766e;
    font-size: 19pt;
    border-bottom: 2px solid #0f766e;
    padding-bottom: 6px;
    margin-top: 18px;
    margin-bottom: 12px;
    page-break-after: avoid;
  }}
  h2 {{
    color: #1e293b;
    font-size: 14pt;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 4px;
    margin-top: 16px;
    margin-bottom: 8px;
    page-break-after: avoid;
  }}
  h3 {{
    color: #334155;
    font-size: 11.5pt;
    margin-top: 14px;
    margin-bottom: 6px;
    page-break-after: avoid;
  }}
  h4 {{
    color: #475569;
    font-size: 10.5pt;
    margin-top: 10px;
    margin-bottom: 4px;
  }}
  p {{
    margin-top: 4px;
    margin-bottom: 8px;
  }}
  ul, ol {{
    margin-top: 4px;
    margin-bottom: 8px;
    padding-left: 24px;
  }}
  li {{
    margin-bottom: 3px;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin-top: 12px;
    margin-bottom: 16px;
    font-size: 8.5pt;
    page-break-inside: avoid;
  }}
  th, td {{
    border: 1px solid #cbd5e1;
    padding: 6px 9px;
    text-align: left;
    vertical-align: top;
  }}
  th {{
    background-color: #0f766e;
    color: #ffffff;
    font-weight: 600;
  }}
  tr:nth-child(even) td {{
    background-color: #f8fafc;
  }}
  pre, code {{
    font-family: Consolas, Monaco, "Courier New", monospace;
  }}
  pre {{
    background-color: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 10px;
    font-size: 8.5pt;
    overflow-x: auto;
    page-break-inside: avoid;
    margin-top: 8px;
    margin-bottom: 12px;
  }}
  code {{
    background-color: #f1f5f9;
    color: #b91c1c;
    padding: 2px 4px;
    border-radius: 3px;
    font-size: 9pt;
  }}
  pre code {{
    background-color: transparent;
    color: #1e293b;
    padding: 0;
  }}
  blockquote {{
    border-left: 4px solid #0f766e;
    background-color: #f0fdfa;
    padding: 8px 14px;
    margin: 8px 0;
    color: #134e4a;
    font-style: italic;
  }}
  hr {{
    border: 0;
    height: 1px;
    background: #cbd5e1;
    margin: 16px 0;
  }}
  a {{
    color: #0f766e;
    text-decoration: underline;
  }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""
    temp_html = pdf_path.with_suffix('.temp.html')
    with open(temp_html, 'w', encoding='utf-8') as f:
        f.write(html_doc)
        
    cmd = [
        edge_exe,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={pdf_path.resolve()}",
        f"file:///{temp_html.resolve().as_posix()}"
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    
    # Clean up temporary HTML
    if temp_html.exists():
        temp_html.unlink()


def main():
    root_dir = Path(__file__).resolve().parent.parent
    docs_src_dir = root_dir / "project-documentation"
    output_bundle_dir = root_dir / "Prescripto_AI_2.0_Reports"
    docx_dir = output_bundle_dir / "DOCX_Files"
    pdf_dir = output_bundle_dir / "PDF_Files"
    zip_dest_path = root_dir / "Prescripto_AI_2.0_Academic_Report_and_Project_Dossiers.zip"
    
    docx_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_exe):
        edge_exe = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_exe):
        print(f"Error: Microsoft Edge executable not found at {edge_exe}")
        sys.exit(1)
        
    md_files = sorted(list(docs_src_dir.glob("*.md")))
    print(f"Found {len(md_files)} documentation files to convert.\n")
    
    converted_docx = []
    converted_pdf = []
    
    for idx, md_file in enumerate(md_files, 1):
        stem = md_file.stem
        out_docx = docx_dir / f"{stem}.docx"
        out_pdf = pdf_dir / f"{stem}.pdf"
        
        print(f"[{idx}/{len(md_files)}] Processing: {stem}...")
        
        # 1. Convert to DOCX
        try:
            md_to_docx(md_file, out_docx)
            converted_docx.append(out_docx)
            print(f"  [OK] Word Document (.docx) created ({out_docx.stat().st_size // 1024} KB)")
        except Exception as e:
            print(f"  [FAIL] Failed DOCX conversion for {stem}: {e}")
            
        # 2. Convert to PDF
        try:
            md_to_pdf_via_edge(md_file, out_pdf, edge_exe)
            converted_pdf.append(out_pdf)
            print(f"  [OK] PDF Document (.pdf) created ({out_pdf.stat().st_size // 1024} KB)")
        except Exception as e:
            print(f"  [FAIL] Failed PDF conversion for {stem}: {e}")
            
    # Also place copies of the Master Report at the root of the output bundle
    master_docx_src = docx_dir / "00_MASTER_SEMESTER_PROJECT_REPORT.docx"
    master_pdf_src = pdf_dir / "00_MASTER_SEMESTER_PROJECT_REPORT.pdf"
    if master_docx_src.exists():
        import shutil
        shutil.copy2(master_docx_src, output_bundle_dir / "00_MASTER_SEMESTER_PROJECT_REPORT.docx")
    if master_pdf_src.exists():
        import shutil
        shutil.copy2(master_pdf_src, output_bundle_dir / "00_MASTER_SEMESTER_PROJECT_REPORT.pdf")
        
    print("\nCreating final ZIP archive (containing ONLY .docx and .pdf files)...")
    with zipfile.ZipFile(zip_dest_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in output_bundle_dir.rglob("*"):
            if file_path.is_file():
                # Enforce STRICT file format restriction
                if file_path.suffix.lower() in [".docx", ".pdf"]:
                    rel_path = file_path.relative_to(output_bundle_dir)
                    zf.write(file_path, arcname=str(rel_path))
                    
    zip_size_mb = zip_dest_path.stat().st_size / (1024 * 1024)
    print(f"\n==================================================================")
    print(f"SUCCESS: Package created at:")
    print(f"{zip_dest_path}")
    print(f"Archive Size: {zip_size_mb:.2f} MB")
    print(f"Total DOCX Files: {len(converted_docx)}")
    print(f"Total PDF Files: {len(converted_pdf)}")
    print(f"==================================================================")


if __name__ == "__main__":
    main()
