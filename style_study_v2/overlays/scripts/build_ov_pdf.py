import json
from reportlab.lib.pagesizes import A4,landscape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from PIL import Image as PI
ss=getSampleStyleSheet()
H1=ParagraphStyle('h1',parent=ss['Heading1'],fontSize=17,spaceAfter=4)
H2=ParagraphStyle('h2',parent=ss['Heading2'],fontSize=13,spaceBefore=2,spaceAfter=3,textColor=colors.HexColor('#1e3a8a'))
B=ParagraphStyle('b',parent=ss['BodyText'],fontSize=8.6,leading=11.2)
S=ParagraphStyle('s',parent=B,fontSize=7.4,leading=9,textColor=colors.HexColor('#374151'))
TC=ParagraphStyle('tc',parent=B,fontSize=7.8,leading=9.8)
ST=json.load(open('/home/user/ov/stats.json'))
EX='/home/user/ov/ex/'
def img(p,w,hmax=None):
    a,b=PI.open(p).size; h=w*b/a
    if hmax and h>hmax: w=w*hmax/h; h=hmax
    return Image(p,width=w,height=h)
def tbl(rows,cw):
    rows=[[Paragraph(c,TC) if isinstance(c,str) else c for c in r] for r in rows]
    t=Table(rows,colWidths=cw); t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#9ca3af')),('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5e7eb')),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3)])); return t
def where(k):
    s=ST[k]; x,y=s['cx'],s['cy']
    hx='left' if x<0.33 else 'right' if x>0.67 else 'centre'; vy='top' if y<0.25 else 'bottom' if y>0.75 else 'middle'
    return f'{vy}-{hx} (median centre x {x*100:.0f}%, y {y*100:.0f}%; size {s["w"]*100:.0f}% × {s["h"]*100:.0f}% of frame)'
def counts(k): c=ST[k]['count']; return ', '.join(f'{n} {c.get(v,0)}' for v,n in [('amy','Amy'),('caylee','Caylee'),('noida','Noida')])
SEC=[
('date','1. Date & time stamps',['amy_1','noida_14','amy_21','noida_72'],
 '<b>Look:</b> a small line in thin light-grey caps on top (“MARCH 24”, “11 DECEMBER”, or “AM/PM” under a clock time), with a large bold condensed white year or time (“1998”, “12:08”) beneath it. Two thin white rules sit either side and fade out towards their ends, with a soft white glow. No box or background.<br/><b>Use:</b> marks every jump in time: a year when a chapter opens, then clock times through the key night (Noida runs 10:00 → 11:00 → 12:08 → 4:00 → 8:30). It often appears together with a section tag.<br/><b>Animation:</b> the rules slide outwards from the centre while the text fades and sharpens in (about 0.9 s). It holds for about 2 s, then quickly fades (about 0.2 s) or cuts away with the shot.'),
('quote','2. Quote cards (quoted statements)',['caylee_72','caylee_77','amy_40','caylee_39','amy_11','noida_30'],
 '<b>Look:</b> bold condensed white caps (Bebas/Oswald-like), 1–5 lines, left-aligned, with a slight glow. A large opening quote mark sits top-left, in white or the accent red, and a closing mark bottom-right. A thin white open frame (L-bracket lines, sometimes dashed) wraps the text. The speaker’s name is in small dark caps on a white tab at the bottom-right (“-JUDGE BELVIN PERRY”, “ASHTON”). There is no fill behind the text, so the dark 3D shot shows through. Text messages and phone calls use the same card.<br/><b>Placement:</b> in empty dark space next to the speaking mannequin, usually upper-middle or upper-right. Over 2D scenes the quote sits beside the line art.<br/><b>Animation (most complex in the set):</b> the opening mark pops in, then the frame lines draw (top line, down, then along the bottom), the speaker tab slides in, and finally the text types on letter by letter. In total that takes about 1.6 s. It holds for about 1.5 s, then leaves on the shot cut with no exit animation.'),
('keyword','2b. Keyword call-outs (short quoted phrases)',['amy_39','amy_86','noida_45','caylee_67'],
 '<b>Look:</b> the same font and quote marks as the quote cards but with no frame: 1–3 words (“MENACING LOOK”, “NECK BREAKING / SELF-DEFENSE / HOUSEHOLD WEAPONS”, “$210,000”, “JAS”). Profanity is masked with asterisks (“B******”). A variant uses a red quote mark, a thin box, and a small red attribution underneath (“UNUSUALLY EARLY / INVESTIGATORS”).<br/><b>Placement:</b> top-centre over the scene, above the relevant figure or prop.<br/><b>Animation:</b> types on or fades in (about 1 s), stays for 2–4 s, and cuts out with the shot. This is the device the channel uses most to underline a word in the narration. Timing figures are counted together with the quote cards.'),
('section_tag','3. Section tags',['noida_23','caylee_37','amy_30','noida_4'],
 '<b>Look:</b> small white condensed caps (“THE 911 CALLS AND POLICE ARRIVAL”, “DISCOVERY OF HEMRAJ’S BODY”, “BACKGROUND”) in a box with a dark fill and a rough white, slightly glowing border, like a brush or chalk edge.<br/><b>Placement:</b> always top-left, tight to the corner.<br/><b>Use:</b> names each sub-section. They appear every 1–4 minutes and are the most frequent graphic in Noida (18).<br/><b>Animation:</b> the box and text wipe in from left to right (about 0.7 s), hold for about 2.5 s, and wipe or fade out (about 0.45 s).'),
('title','4. Title & chapter cards',['caylee_2','noida_2','amy_26','amy_103'],
 '<b>Episode title</b> (about 0:35–0:45, right after the cold open): bold condensed caps in red-orange with a red glow (“DEATH OF CAYLEE ANTHONY”, “THE NOIDA DOUBLE MURDER CASE”) over a white line-art scene (crime-tape playhouse, a figure in a red-lit doorway). The whole thing sits inside camcorder viewfinder corners with a “REC” label at top-left. It flickers or glitches in.<br/><b>Chapter cards</b> (4–5 per film, ending with “CONCLUSION”): a white dry-brush stroke on a black screen carries a <i>thin italic geometric sans</i> in dark grey caps (Montserrat Italic-like, the only non-condensed type in the films). A darkened, vignetted preview of the next 3D scene sits below it. The brush paints on from left to right with the text (about 1.2 s), holds for about 3 s, then cuts.'),
('whos_who','5. Name labels & who’s-who cards',['caylee_6','noida_27','amy_58','amy_59'],
 '<b>Portrait cards</b> (2D): a black-and-white cross-hatched drawing in a rough white photo frame. Faces are drawn, or for some people (the doctor, the father) blacked out with a scribble. Below it: the name in bold condensed white caps, then the role (“VICTIM”, “FATHER”, “DOCTOR”) in tiny red italics, with a short red underline glow. The card is centred, sometimes with a section tag at top-left, and scales or fades in (about 1.8 s).<br/><b>Descriptor labels</b> (3D): eyewitness descriptions (“RED-HAIRED / RED BEARD”, “DARK-HAIRED / 5 FT 11 IN”) type on inside a thin bracket frame above a mannequin. A name can also appear as a quoted keyword above a figure (“ALISTER DOUGLAS”). There are no lower-third name straps anywhere in the three films.'),
('place','6. Place & object labels',['caylee_36','noida_15','amy_52','caylee_5'],
 '<b>Mostly diegetic:</b> place names are built into the 3D model as glowing signs, not overlaid (“SOUTHEAST COMMUNITY POLICE OFFICE”, “STELARIS LOUNGE”, “VIKING LOUNGE”, “NOIDA CLINIC”, “CBI”, “CREW ONLY AREA”, “EVIDENCE BOX”). These are white condensed caps or emissive neon.<br/><b>Floor-plan labels:</b> in the Noida cut-away dollhouse, room names lie flat on the floor (“AARUSHI’S ROOM”, “HEMRAJ’S ROOM”, “LIVING ROOM”) in white condensed caps, and the camera slowly tracks over them for 16–22 s.<br/><b>2D:</b> a street or neighbourhood sign is drawn into the line art (“CHICKASAW OAKS”, “HOPESPRING DRIVE”). There are no generic “LOCATION:” supers.'),
('line_art','7. 2D line-art illustrations',['amy_4','amy_9','caylee_12','noida_10'],
 '<b>Look:</b> white ink drawings with fine cross-hatching on pure black, standing on a faint white perspective grid floor. People are faceless, with a dark scribble over the face. Small red-orange accents pick out one detail each (a basketball, a pencil cup, a check-mark list, a swimsuit). A red-orange swoosh line sometimes leads the eye across the frame.<br/><b>Use:</b> backstory before the timeline starts (childhood, school, job, daily routine), about 1:00–2:30 into each film, plus occasional evidence explainers.<br/><b>Animation:</b> elements fade or slide in one by one (about 1.4 s), and the camera drifts slowly across the scene. They hold for 7–23 s, the longest graphics after documents, and dissolve out (about 2–3 s).'),
('family_tree','8. Family-tree & link boards',['amy_3','caylee_8','noida_6'],
 '<b>Look:</b> portrait cards (see section 5) arranged in a tree on black, joined by thin red-orange lines with small red nodes. The victim sits at the bottom, with parents and siblings above.<br/><b>Animation:</b> builds up over about 3 s, one card at a time (the card scales or slides in, then its red connector draws on). It holds for up to about 15 s while the narration introduces each person. A date stamp can appear at the top.'),
('map','9. Maps & map cards',['amy_12','caylee_4','noida_7','noida_8'],
 '<b>Variants:</b> (a) a region silhouette filled black with a glowing red outline, a small white landmark icon, and a white city name on a red tab, on a black grid. A curved white arc animates between two cities (Delhi → Noida). (b) A tilted map card with a white frame and a magenta glow showing a dotted red-orange cruise route with small white island labels. (c) A minimal street map in thin grey lines with a red route line drawing along the named street. (d) A state shape filled red-orange on a card held by an illustrated hand (see STYLE_GUIDE.pdf).<br/><b>Animation:</b> the outline or route draws on (about 1.4 s), holds 5–9 s, then cuts.'),
('document','10. Evidence documents, phone records & timelines',['noida_29','noida_41','caylee_16','noida_77'],
 '<b>Look:</b> white sheets tilted about 15–20° on the black grid with a red curved swoosh. Headings are in bold red-orange caps (“THE POST-MORTEM REPORT”), with small grey-white body text and red highlighted lines (time of death). Small inset photo cards carry a red label (“KUKRI KNIFE”). Phone records are a white table (DATE / TIME / ACTIVITY) with a red title and quote mark. A calendar-and-hourglass illustration stands in for a timeline. At the end, white-framed “polaroids” of the earlier 3D crime-scene renders slide in as a recap.<br/><b>Animation:</b> sheets slide in one after another and the camera pushes slowly across them. Each one stays long enough to read: 9–54 s (the Noida post-mortem section is about 83 s).'),
('arrows','11. Arrows & highlights',['amy_37','amy_38','noida_36'],
 '<b>Arrows:</b> rare. Hand-drawn white chalk-style hooked arrows draw on over the 3D scene to point at a specific mannequin (about 0.9 s), hold for 2–3 s, and fade.<br/><b>Highlights:</b> done mostly with 3D light rather than graphics: a red spotlight or emissive red on the key object, a red neon body outline on the floor (Noida), and red blood decals. In 2D, red-orange lines and underlines do the highlighting. There are no circles, zoom boxes or glow rings.'),
('bookends','12. Disclaimer, CTA & end cards',['amy_0','amy_106','caylee_88','amy_107'],
 '<b>Disclaimer</b> (0:00–0:03): “THE FOLLOWING ANIMATIONS WERE MADE BY A HUMAN” in small white condensed caps, centred on black, with a fast fade.<br/><b>Memorial card</b> (last ~10 s): the only real photograph in each film. A black-and-white photo of the victim sits in a rough white frame with a red glitch or brush smear behind it; the name in white condensed caps and the years (“1974–1998”) sit below it.<br/><b>Credits</b> (last ~5 s): “CHANNEL PATRONS” and “MEMBERS” headings in white-bordered boxes (the same style as the section tags), with small white names and coloured dot icons.<br/><b>CTA:</b> spoken only (“So, what do you guys think really happened?”). No on-screen subscribe or comment graphic was found.'),
('sponsor','13. Sponsor segment (found in 2 of 3 films)',['caylee_19','caylee_21'],
 'Amy (3:37–4:54) and Caylee (3:53–4:37) contain a Zocdoc ad read after the who’s-who section. It reuses the house 2D style (black grid, a line-art hand holding a phone with real app screenshots), then switches to the brand’s yellow and cream end card. Noida has none. This tells us the ad slot sits at about 4 minutes, after the cold open, title and backstory.'),
]
st=[]
st.append(Paragraph('On-screen text & graphics: the 2D overlay layer',H1))
st.append(Paragraph('This covers everything drawn on top of (or instead of) the 3D in the three reference films. Every frame at 2 fps of the whole runtime was scanned for sharp white or red-orange graphic pixels, and candidate frames were OCR’d with Tesseract. Hits were grouped into instances, split at scene cuts and with duplicates removed, and every instance was then checked and categorised by eye. Each instance keeps its clearest frame. <b>250 distinct instances</b> were found: Amy 91, Caylee 85 and Noida 74. In/out timing was measured at 30 fps on each instance (the median time for the graphic’s white pixels to go from 10% to 90%). Full-resolution frames (854×480, the source resolution) are in the category folders, and the contact sheets are sheet_amy_*.jpg, sheet_caylee_*.jpg and sheet_noida_*.jpg. index.json lists every instance with its time, category and time on screen.',B))
st.append(Spacer(1,3*mm))
rows=[['Category','Count (Amy, Caylee, Noida)','On screen (median, p10–p90)','Animate in','Animate out','Where on screen']]
for k,title,_,_ in SEC:
    if k=='keyword': continue
    s=ST[k]; rows.append([title.split('. ',1)[1],counts(k),'%.1f s (%.1f–%.1f)'%(s['dur_med'],s['dur_p10'],s['dur_p90']),('%.1f s'%s['rin']) if s['rin'] is not None else '–',('%.2f s'%s['rout']) if s['rout'] is not None else '–',where(k)])
st.append(tbl(rows,[52*mm,40*mm,34*mm,18*mm,18*mm,88*mm]))
st.append(Paragraph('On-screen times are rounded to the 0.5 s scan step. “Out” near 0 means the graphic leaves on the shot cut. Counts for the 2D sequences (line art, trees, maps, documents) count each distinct composition, not each element inside it.',S))
st.append(Spacer(1,3*mm))
st.append(Paragraph('Shared design system',H2))
st.append(tbl([['Element','Rule'],
['Type','One workhorse face: a <b>bold condensed grotesque, all caps</b> (reads like Bebas Neue or Oswald Bold), white, with a faint glow. Second face for chapter cards only: <b>thin italic geometric sans caps</b> (Montserrat Italic-like). Tiny supporting text (roles, AM/PM, attributions) is the condensed face at 30–40% size, in grey or red.'],
['Colour','White #F2F2F2 for all text and lines. One accent, <b>red-orange #E8401A</b> (2D lines, map fills, role labels, document headings), deepening to <b>#C0141F</b> for glows, quote marks and the episode title. Grey for secondary text. No other hues.'],
['Frames','Rough or brush-edged white borders (section tags, portraits, memorial card, credits). Open thin-line brackets for quotes and descriptors. A dry-brush stroke for chapter titles. Camcorder viewfinder corners for the episode title. Fills are either none or near-black.'],
['Grid','All 2D screens sit on pure black with a faint white perspective grid floor (and a soft vignette), so 2D and 3D share the same darkness.'],
['Motion','Things draw on rather than pop. Text types on (quotes, descriptors), boxes wipe from the left (tags), lines extend from the centre (dates), and connectors and routes draw along their path. Entries take 0.7–1.8 s. Most graphics have no exit animation and simply leave on the next cut.'],
['Density','About 1.5–2 overlay instances per minute. Most shots carry at most one graphic plus an optional date stamp. Never more than three graphic elements at once outside the 2D boards.'],
],[30*mm,220*mm]))
st.append(PageBreak())
for k,title,ex,desc in SEC:
    st.append(Paragraph(title,H2))
    meta=''
    if k in ST: s=ST[k]; meta='<b>Count:</b> %s. <b>On screen:</b> median %.1f s. <b>Position:</b> %s.'%(counts(k),s['dur_med'],where(k))
    if meta: st.append(Paragraph(meta,S))
    st.append(Paragraph(desc,B)); st.append(Spacer(1,2*mm))
    n=len(ex); w=(250*mm)/min(n,3)-4*mm
    ims=[img(EX+f'{k}_{e}.png',w,58*mm) for e in ex]
    caps=[Paragraph(e.replace('_',' #'),S) for e in ex]
    rowsI=[];rowsC=[]
    for j in range(0,n,3): rowsI.append(ims[j:j+3]+['']*(3-len(ims[j:j+3]))); rowsC.append(caps[j:j+3]+['']*(3-len(caps[j:j+3])))
    data=[]
    for a,b in zip(rowsI,rowsC): data+= [a,b]
    t=Table(data,colWidths=[(250*mm)/3]*3); t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE')])); st.append(t)
    st.append(PageBreak())
st.append(Paragraph('What to take for Seldom',H2))
st.append(tbl([['Keep (cheap in Python/PIL + ffmpeg)','Change (so it is not a clone)'],
['Type-on quote cards placed next to the speaker; keyword call-outs to underline narration; top-left section tag + top-centre date/clock stamp as the time spine; draw-on routes and connector lines; 2D boards on a black grid; long holds on documents; memorial photo card at the end; spoken CTA.',
 'Swap the brush/distressed borders for clean 1 px amber brackets; replace the dry-brush chapter card with a typed case-file divider; use Oswald SemiBold + a mono (JetBrains Mono) for dates and times; amber #F2A33A instead of red-orange as the accent; cyanotype (white-on-petrol) line art instead of black hatching; drop the “REC” viewfinder title device.'],
],[125*mm,125*mm]))
doc=SimpleDocTemplate('/home/user/Muhammed/style_study_v2/overlays/OVERLAYS.pdf',pagesize=landscape(A4),leftMargin=14*mm,rightMargin=14*mm,topMargin=10*mm,bottomMargin=10*mm,title='Seldom style study: overlays')
doc.build(st); print('ok')
