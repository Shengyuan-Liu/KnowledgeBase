from pathlib import Path
import json,hashlib
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import pypdfium2 as pdfium
root=Path('/Users/lucas/Documents/Projects/KnowledgeBase/evals/materials/pdf-v2-closeout-dependency')
docs={
'assignment.pdf':['Project Juniper - laboratory assignment','Fictional release-test document. No real organization or project is described.','Decision date: September 17, 2026.','Project Juniper was assigned to Quenwick Laboratory.','The laboratory register defines the calibration interval.','This assignment memo does not state a calibration interval.'],
'laboratory-register.pdf':['Laboratory calibration register','Fictional release-test document. No real organization or project is described.','The following intervals are effective September 1, 2026.','Quenwick Laboratory: calibration interval is 17 days.','Darnell Laboratory: calibration interval is 29 days.','Merriton Laboratory: calibration interval is 43 days.','Intervals are measured in calendar days.']}
for name,lines in docs.items():
 target=root/name;assert not target.exists(); c=canvas.Canvas(str(target),pagesize=letter,invariant=1)
 c.setTitle(lines[0]);c.setFont('Helvetica-Bold',16);c.drawString(48,744,lines[0]);c.setFont('Helvetica',10)
 for i,line in enumerate(lines[1:]):c.drawString(48,704-36*i,line)
 c.drawString(48,40,'1');c.save()
 pdf=pdfium.PdfDocument(str(target));pdf[0].render(scale=1.2).to_pil().save(str(target.with_suffix('.png')))
(root/'manifest.json').write_text(json.dumps({'provenance':'Original synthetic fixtures authored by Codex for controller execution acceptance; not a real-world quality population.','files':[{ 'file':name,'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest(),'pages':1} for name in docs]},indent=2)+'\n')
held=Path('/Users/lucas/Documents/Projects/KnowledgeBase/evals/materials/pdf-v2-closeout-heldout')
for name,pages in [('attention.pdf',[0,2,7]),('bert.pdf',[2,3])]:
 pdf=pdfium.PdfDocument(str(held/name))
 texts=[]
 for i in range(len(pdf)):
  texts.append(pdf[i].get_textpage().get_text_range())
 (held/(name+'.txt')).write_text('\n\f\n'.join(texts))
 for i in pages:pdf[i].render(scale=1.2).to_pil().save(str(held/f'{name}-page{i+1}.png'))
 print(name,'pages',len(pdf))
