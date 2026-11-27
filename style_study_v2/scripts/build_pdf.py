import json,os,numpy as np
from reportlab.lib.pagesizes import A4,landscape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
W='/home/user/work/'; P=W+'pdfimg/'; OUT='/home/user/Muhammed/style_study_v2/'
ss=getSampleStyleSheet()
H1=ParagraphStyle('h1',parent=ss['Heading1'],fontSize=17,spaceAfter=6,textColor=colors.HexColor('#111827'))
H2=ParagraphStyle('h2',parent=ss['Heading2'],fontSize=12.5,spaceBefore=8,spaceAfter=4,textColor=colors.HexColor('#1e3a8a'))
B=ParagraphStyle('b',parent=ss['BodyText'],fontSize=8.6,leading=11.2)
S=ParagraphStyle('s',parent=B,fontSize=7.6,leading=9.6,textColor=colors.HexColor('#374151'))
TC=ParagraphStyle('tc',parent=B,fontSize=7.8,leading=9.8)
def p(t,st=B): return Paragraph(t,st)
def tbl(rows,cw,head=True,fs=7.8):
    rows=[[c if not isinstance(c,str) else Paragraph(c,TC) for c in r] for r in rows]
    t=Table(rows,colWidths=cw,repeatRows=1 if head else 0)
    st=[('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#9ca3af')),('VALIGN',(0,0),(-1,-1),'TOP'),('FONTSIZE',(0,0),(-1,-1),fs),
        ('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]
    if head: st+= [('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5e7eb'))]
    t.setStyle(TableStyle(st)); return t
def img(path,w):
    from PIL import Image as PI
    a,b=PI.open(path).size; return Image(path,width=w,height=w*b/a)
def sw(hexes):
    cells=[[Paragraph('<font color="%s">%s</font>'%('#ffffff' if i<len(hexes) else '#000', h),TC) for i,(h,_) in enumerate(hexes)],[Paragraph(n,S) for _,n in hexes]]
    t=Table(cells,colWidths=[(250*mm)/len(hexes)]*len(hexes),rowHeights=[14*mm,None])
    st=[('BACKGROUND',(i,0),(i,0),colors.HexColor(h)) for i,(h,_) in enumerate(hexes)]
    st+=[('VALIGN',(0,0),(-1,-1),'MIDDLE'),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#9ca3af'))]
    t.setStyle(TableStyle(st)); return t

V=[('amy','The Unsolved Disappearance of Amy Bradley'),('caylee','The Nanny Who Never Existed: Inside the Caylee Anthony Case'),('noida','The Noida Double Murder: India’s Most Controversial Murder Mystery')]
M={}
for v,_ in V:
    c=json.load(open(W+v+'.cuts.json')); cuts=np.array(c['cuts']); dur=c['dur']
    sh=np.diff(np.concatenate([[0],cuts,[dur]]))
    hook=((cuts<60)).sum()
    cl=json.load(open(W+'classify.json'))[v]
    wpm='n/a'
    if os.path.exists(W+v+'.asr.json'):
        a=json.load(open(W+v+'.asr.json')); words=sum(len(s['t'].split()) for s in a); wpm='%d'%round(words/(dur/60))
    M[v]=dict(dur=dur,n=len(cuts),cpm=len(cuts)/dur*60,asl=sh.mean(),med=np.median(sh),p10=np.percentile(sh,10),p90=np.percentile(sh,90),hook=hook,d2=cl['2d_frac'],dates=len(cl['date_runs']),wpm=wpm)
LUFS={'amy':-16.0,'caylee':-13.7,'noida':-14.0}; LUMA={'amy':14.8,'caylee':13.3,'noida':14.8}
def mmss(s): return '%d:%02d'%(s//60,s%60)

st=[]
st.append(p('Style Study v2 — 3D “blue-room” true-crime references',H1))
st.append(p('For the Seldom channel. Three reference films (one creator, red “V” bug top-right) downloaded from the shared Drive folder and measured with ffmpeg (shot detection, colour, loudness), frame grabs, and Whisper transcripts. Numbers are machine-measured; the shot detector was checked by hand against 1-fps grabs and is within roughly ±15% (it can merge cuts between two very dark shots).',B))
st.append(p('1. Files received',H2))
rows=[['File (as named in Drive)','Duration','Resolution','Aspect','Video / audio','Size']]
for v,t in V:
    rows.append([t+'.mp4',mmss(M[v]['dur']),'854 × 480','16:9 (427:240)','H.264 30 fps / AAC 44.1 kHz stereo',{'amy':'67 MB','caylee':'90 MB','noida':'79 MB'}[v]])
st.append(tbl(rows,[95*mm,18*mm,22*mm,24*mm,60*mm,16*mm]))
st.append(p('All 3 files downloaded; none failed. <b>Note:</b> the Amy Bradley file has a <b>Russian dubbed narration</b> (Whisper language ID 1.00 “ru”) and a single audio track, while all on-screen text is English. Caylee and Noida are English. 480p is a low-bitrate copy, so fine texture detail and font edges are softer than the originals.',S))

st.append(p('2. Measurements',H2))
rows=[['Metric']+[t.split(':')[0] for _,t in V]]
def r(name,f): rows.append([name]+[f(M[v],v) for v,_ in V])
r('Runtime',lambda m,v: mmss(m['dur']))
r('Shots detected',lambda m,v: str(m['n']+1))
r('Cuts per minute (whole film)',lambda m,v: '%.1f'%m['cpm'])
r('Average shot length (mean / median)',lambda m,v: '%.1f s / %.1f s'%(m['asl'],m['med']))
r('Shot length 10th–90th percentile',lambda m,v: '%.1f – %.1f s'%(m['p10'],m['p90']))
r('Cuts in first 60 s (cold open)',lambda m,v: '%d (%.0f/min, ~2× body rate)'%(m['hook'],m['hook']))
r('Share of runtime on flat 2D/black graphics',lambda m,v: '%.0f%%'%(100*m['d2']))
r('Date-stamp appearances',lambda m,v: str(m['dates']))
r('Mean frame brightness (0–255)',lambda m,v: '%.1f (very dark)'%LUMA[v])
r('Narration language / speed',lambda m,v: 'English, '+m['wpm']+' words/min' if m['wpm']!='n/a' else '<b>Russian voice-over</b> (on-screen text English); wpm not comparable')
r('Loudness (integrated / range)',lambda m,v: '%.1f LUFS / ~3 LU'%LUFS[v])
st.append(tbl(rows,[62*mm,62*mm,62*mm,62*mm]))
st.append(p('Within a shot the picture barely moves: 66–82% of frame-to-frame pairs are essentially identical at 64×36 px. Camera moves are slow pushes and drifts; there are no whip pans, handheld shake or fast moves. Transitions are hard cuts, often with a 2–6-frame dip to near black. Shot-to-shot fades are rare (1–2 per film).',B))
st.append(PageBreak())

st.append(p('3. Common style rules (true for all three films)',H2))
rules=[
['Look','<b>Full 3D, stylised realism.</b> Real-scale, realistic sets (cruise-ship decks, flats, courtrooms, police stations) with simple, plausible geometry and props. Sets are dioramas floating in a black void: walls stop and the edges fall into darkness.'],
['Characters','<b>Faceless mannequins.</b> Smooth, matte clay figures with no eyes, mouths or hair strands. Clothes, caps and uniforms are sculpted in the same pale lilac-grey material. Identity comes from silhouette (police cap, suit, hazmat suit, dress, hair mass). The figures pose and gesture with slow, minimal motion. No real faces in 3D.'],
['Colour','Monochrome <b>navy/cobalt</b> world. About 70% of pixels are below luma 20, and the dominant tones are #05173C, #081F57 and #15387D. Figures catch a <b>magenta/pink</b> rim or key light (~#C86A9A to #E0708A). Story-critical objects get a <b>hot red</b> accent (#C0141F to #E8401A): blood, a phone, a weapon, a lamp, cards on a table. Almost no other hues; the odd green (a boat) is incidental.'],
['Lighting','Low-key night lighting. Blue ambient/moon fill, one or two warm-red practicals or spots, strong radial vignette, and <b>wet glossy floors</b> with puddle reflections and mild haze. Shadows read as solid dark blue. The red pool of light usually marks the focus point.'],
['Camera','Mostly <b>high 3/4 overhead wides</b> (30–60° down) that read like a dollhouse or crime-scene diorama. Medium shots on 2–3 figures; low inserts on single props (phone, router, bottle). Lens about 35–50 mm, deep focus with slight DOF on inserts. Moves: slow push-in, lateral drift, slow orbit.'],
['Pacing','Narration-led, one shot per sentence or two: ~5.5–7 cuts/min, median shot ~7–10 s. The cold open is about twice as fast (10–15 cuts in the first minute). The picture illustrates the line being spoken quite literally.'],
['2D layer','5–9% of runtime, mostly in the first 4 minutes and inside evidence sections. Black background with a faint perspective grid. <b>White engraved/cross-hatched line-art</b> illustrations (faceless, with a scribble over the face). Polaroid-style portrait cards of the people (hatched drawing, name in bold condensed caps, role in small italics, red underline) linked by red lines into family trees. Maps are a white-framed card with the region filled red-orange, sometimes held by an illustrated hand. Documents (autopsy report) are tilted white paper with red headings.'],
['Type','One family: bold <b>condensed grotesque, all caps</b> (Bebas/Oswald-like) with a slightly distressed print edge. (1) <b>Section tag</b> top-left: white text in a rough white-bordered box, e.g. “THE 911 CALLS AND POLICE ARRIVAL”. (2) <b>Date stamp</b> top-centre: small “11 DECEMBER” above a large “2008” between two thin rules (also clock times like “12:08”). (3) <b>Quote card</b>: bracket frame with big quote marks, italic caps, speaker tab below. (4) Diegetic 3D signage (“SOUTHEAST COMMUNITY POLICE OFFICE”, “STELARIS LOUNGE”).'],
['Structure','(1) Disclaimer card “THE FOLLOWING ANIMATIONS WERE MADE BY A HUMAN”. (2) Cold open of ~35–45 s that states the mystery (“for more than a month almost no one knew she was gone”). (3) Title card. (4) 2D “who’s who”: portraits, family tree, map. (5) Strict chronology driven by date stamps and section tags (every 2–4 min). (6) Discovery, investigation, evidence (2D document inserts), trial/verdict. (7) Narrator weighs the theories in the first person. (8) CTA “So, what do you guys think really happened?”. (9) Patron credits. Reveals are slow pushes onto a red-lit object and a date jump, not stingers.'],
['Sound','Narration wall-to-wall (~160 wpm, ~100% coverage), one calm, even narrator voice. Under it a <b>constant dark tonal drone/ambient score</b>: never silent, sitting ~15 dB below the voice (pause floor about −30 dBFS RMS), bass-heavy (sub plus low bands ≈50% of pause energy) and very tonal (spectral flatness ~0). Loudness −14 to −16 LUFS with a tiny range (~3 LU). SFX are sparse and diegetic (phone ring, room tone, water). No regular stinger pattern shows in the loudness curve.'],
]
st.append(tbl([['Area','Rule']]+rules,[24*mm,226*mm]))
st.append(PageBreak())
st.append(p('Palette (measured from 72 sampled frames)',H2))
st.append(sw([('#05173C','Base void 45%'),('#081F57','Shadow blue 28%'),('#15387D','Lit blue 9%'),('#4E2B5C','Violet bounce'),('#C86A9A','Figure rim (magenta)'),('#B6B7BF','Mannequin highlight'),('#C0141F','Accent red (logo/3D)'),('#E8401A','2D accent orange-red')]))
st.append(Spacer(1,4*mm))
st.append(p('Graphic vocabulary (crops from the references)',H2))
g=[[img(P+'tag.png',80*mm),img(P+'date.png',80*mm),img(P+'quote.png',70*mm)],[p('Section tag (top-left)',S),p('Date stamp (top-centre)',S),p('Quote card',S)],
   [img(P+'portrait.png',62*mm),img(P+'map.png',70*mm),img(P+'doc.png',62*mm)],[p('2D portrait card (hatched, faceless)',S),p('Map card held by illustrated hand',S),p('Evidence document insert',S)]]
t=Table(g,colWidths=[85*mm,85*mm,80*mm]); t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE')])); st.append(t)
st.append(PageBreak())
st.append(p('Typical 3D frames',H2))
g=[[img(P+'caylee_1153.jpg',82*mm),img(P+'noida_2240.jpg',82*mm),img(P+'amy_2236.jpg',82*mm)],[p('Caylee 19:13: high 3/4 wide, red torch accent, date stamp, section tag',S),p('Noida 37:20: single figure, red practical, void beyond the wall',S),p('Amy 37:16: overhead deck wide, wet floor',S)],
   [img(P+'caylee_1213.jpg',82*mm),img(P+'amy_1717.jpg',82*mm),img(P+'noida_1500.jpg',82*mm)],[p('Caylee 20:13: medium group, wet ground, magenta rim',S),p('Amy 28:37: real photo shown only inside a 3D prop (TV)',S),p('Noida 25:00: prop insert, red object as focus',S)]]
t=Table(g,colWidths=[84*mm]*3); t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER')])); st.append(t)
st.append(PageBreak())

st.append(p('4. Per-video notes',H2))
notes=[['Video','Notes'],
['Amy Bradley (45:59)','Cruise-ship world: large exterior ship model, decks, bars, cabins, Coast Guard boat. The most open sets, so the most void and water. Russian voice-over in this copy. Cold open (0–45 s, 11 cuts): “early morning of 24 March 1998… less than an hour later she vanished… what really happened?”, then title “THE VOYAGE THAT BECAME A MYSTERY” over the ship, then the 2D family tree and a Virginia map card held by a hand (0:46–2:10). Date stamp “MARCH 24 / 1998” anchors the night. Many quote cards for witness statements. Ending: sighting theories, CTA, credits.'],
['Caylee Anthony (41:57)','Suburban Orlando: house exterior from above, playhouse and back yard, cars, police office, woods search, courtroom, press conference with flags, autopsy table with skeleton highlighted red. Longest 2D intro (0:52–2:33, ~100 s of who’s-who and timeline). Highest cut rate (7.1/min). Ends on ~2.5 min of first-person narrator analysis (“I think the prosecution weakened its own case…”) before the CTA.'],
['Noida (55:38)','Interior chamber piece: a two-bedroom flat rebuilt as a cut-away dollhouse (top-down cut-away shot at ~4:43), plus terrace, hospital, CBI building and court. Uses the most graphics: ~26 section tags, ~19 date/clock stamps (“12:08” router log), and a long 2D post-mortem/evidence section (13:42–15:49). Slowest cutting (5.6/min, median 9.7 s). Red blood decals and red practicals do heavy lifting. Ends with theory comparison and the CTA.'],
]
st.append(tbl(notes,[38*mm,212*mm]))
st.append(Spacer(1,3*mm))
st.append(p('5. What this costs with OUR pipeline',H2))
st.append(p('Pipeline: code-driven Blender on a 4-core CPU box with no GPU (fast preset ≈ 23 s/frame at 960×540, 16 spp), code-made 2D motion graphics (ffmpeg/Python), and AI stills made by the user in ChatGPT.',B))
cost=[['Element','Cost for us','How'],
['Fully animated 3D like the references','<font color="#b91c1c"><b>Not feasible</b></font>','45 min × 24 fps = 64,800 frames × 23 s ≈ 414 CPU-hours (~17 days) at preview quality. Even a 12-min film is ~110 h.'],
['3D stills + 2D camera move','<font color="#15803d"><b>Cheap</b></font>','The refs barely move inside a shot, so one render per shot plus an ffmpeg push/drift on a 1.3× oversized frame reads almost the same. 1280×720 at 32 spp + denoise ≈ 80–100 s per still. A 12-min film is ~80 shots ≈ 2–2.5 h.'],
['A few true animated hero shots','<font color="#b45309"><b>Medium</b></font>','Budget 4–6 shots of 4–6 s (slow orbit or push across the main set) at 960×540 16 spp, upscaled: ~120–150 frames × 23 s ≈ 50 min each, so 4–5 h total. Animate the camera only; keep figures static.'],
['Faceless mannequin figures','<font color="#15803d"><b>Cheap</b></font> to look right, <font color="#b45309"><b>medium</b></font> to pose','One matte material and no faces, hair or cloth sim, which hides the weaknesses of low-poly or procedural humans. The work is a library of ~10 code-posed base poses (stand, sit, lie, point, kneel, hold phone, walk) built from a CC0 rigged base mesh, plus prop hats/caps as silhouette cues.'],
['Sets in a void','<font color="#15803d"><b>Cheap</b></font>','Rooms are boxes plus a few props, and darkness hides missing walls and detail. The fog volume is the expensive part: fake it with a 2D haze gradient in compositing instead of volumetrics.'],
['Look: blue world, magenta rim, red accent, wet floor','<font color="#15803d"><b>Cheap</b></font>','Two to three lights per shot (blue area fill, magenta rim, red spot or practical), a glossy floor shader with a noise roughness map, and a vignette in post. All of it is code-reproducible as one scene template.'],
['Low-light noise on CPU','<font color="#b45309"><b>Medium risk</b></font>','Dark scenes with small hot lights cause fireflies at 16 spp. Use OIDN denoise, clamp indirect at 3–5 and light-path limits. Grain and vignette in post hide the rest.'],
['2D layer: tags, date stamps, quote cards, red family-tree lines, map cards, documents','<font color="#15803d"><b>Cheap</b></font>','All of it is text, boxes and lines, easy in Python/PIL + ffmpeg with an open condensed font (Oswald, Bebas Neue or Anton; all OFL licensed) and a rough-edge mask.'],
['Hatched line-art portraits and illustrations','<font color="#15803d"><b>Cheap</b></font> via ChatGPT','Prompt for “white cross-hatched ink illustration on pure black, faceless, no text” and composite in code. Never prompt for a recognisable real person: use faceless or scribbled faces as the refs do.'],
['Narration, drone bed, sparse SFX','<font color="#15803d"><b>Cheap</b></font>','One continuous tonal drone (CC0 or generated pad) at −15 to −18 dB under the voice, a few diegetic SFX per minute, mastered to −14 LUFS.'],
]
st.append(tbl(cost,[55*mm,32*mm,163*mm]))
st.append(PageBreak())

st.append(p('6. Recommendation: how Seldom should look',H2))
st.append(p('<b>Adopt the grammar, not the skin.</b> The references work because of a few cheap decisions: a dark void hides cost, faceless clay figures avoid likeness and uncanny faces, one accent colour points the eye, and narration drives slow, literal shots. All of these suit our CPU pipeline <i>if we render stills and move the camera in 2D</i>. Copying the exact blue+magenta+red palette, distressed Bebas tags and hatched polaroids would make Seldom look like a clone of the “V” channel, so change the signature elements:',B))
rec=[['Decision','Seldom version'],
['World colour','Deep <b>ink-teal/petrol</b> instead of cobalt: base #06141A, shadow #0B2530, lit #1D4A57. Same low-key darkness (mean luma ~14).'],
['Accent','<b>Sodium amber</b> #F2A33A for the story-critical object, plus a cool white rim #CFE3E8 on figures (instead of magenta). Keep red (#D7263D) only for blood or danger, used rarely, so it hits harder.'],
['Figures','Faceless mannequins in one matte warm-grey clay (#B9B4AC). Silhouette cues only (caps, coats, bags).'],
['Camera','High 3/4 diorama wides as the default. Every shot gets a 2D push or drift of 4–8% over its length. 4–6 true Blender camera moves per film for the key reveals.'],
['Pacing','Cold open at 10–12 cuts/min for 30–40 s, then ~6 cuts/min (median shot 8 s).'],
['Graphics','Clean (not distressed) <b>Oswald SemiBold caps</b>. Section tag bottom-left in a thin amber bracket. Date stamp top-left as “16 MAY 2008 · 23:47” in a mono font (JetBrains Mono, OFL) to give Seldom a “case-file timestamp” signature. Quote cards as typed transcript strips.'],
['2D layer','Black background with a faint dot grid. Portraits as AI <b>cyanotype/blueprint-style line drawings</b> (white on petrol), faceless. Maps drawn in code from Natural Earth data, with amber land fill and a pulsing pin.'],
['Sound','Narration ~150–160 wpm. A continuous low drone bed ~16 dB under the voice. 1–3 diegetic SFX per minute. Master to −14 LUFS.'],
]
st.append(tbl(rec,[30*mm,220*mm]))
st.append(Spacer(1,3*mm))
st.append(p('Three example frames for the next film',H2))
ex=[['#','Frame','Build notes'],
['1','<b>Cold-open establishing wide (0:04).</b> High 3/4 overhead of an apartment block’s courtyard at night, seen as a diorama whose edges dissolve into black. Ground wet and reflective. One window on the third floor glows sodium-amber; everything else is petrol-teal. A single faceless figure stands under a streetlamp, cool-white rim on the shoulders. Top-left in mono: “16 MAY 2008 · 23:47”. The camera pushes in 6% over 7 s toward the lit window.','Blender still 1280×720 at 32 spp: box buildings with window-grid emission, glossy ground with a noise-roughness map, 1 area light (teal), 1 point light (amber) behind the window, 1 rim spot. ~90 s render. Push and timestamp done in ffmpeg/PIL.'],
['2','<b>Evidence insert (mid-film).</b> Low 30° view of a bedside table in the void: a landline phone lit by a tight amber spot, its cord trailing off into darkness, a faint glossy reflection on the table. Bottom-left section tag in a thin amber bracket: “THE CALL AT 00:12”. 4-frame dip to black before the cut.','Cheapest shot type: 3 props, 1 spot plus weak teal fill, DOF on. ~60 s still. Cut on the line that names the phone.'],
['3','<b>2D who’s-who card (0:50).</b> Black background with a faint dot grid. Three faceless cyanotype-style line portraits (white lines on deep petrol) slide in, each with an Oswald name in caps and a mono role line (“FATHER · DENTIST”). Thin amber connector lines draw on between them, and a small code-drawn map of the city fades in at the right with an amber pin.','Portraits from ChatGPT (fictional or faceless, never a real likeness), keyed and composited in Python. Line draw-on, slides and map (Natural Earth) all code. Zero render time.'],
]
st.append(tbl(ex,[8*mm,140*mm,102*mm]))
st.append(Spacer(1,2*mm))
st.append(p('<b>Budget check (12-min film):</b> ~80 stills × ~90 s ≈ 2 h, plus 5 hero moves ≈ 4–5 h, plus 2D and audio in minutes. That is ≈ 7 CPU-hours total, versus ~110 h to animate everything as the references do. <b>Suggested first step:</b> build one Blender scene template (lights, floor shader, void, vignette, 3 posed mannequins) and render frame 1 above as the look test.',B))
st.append(Spacer(1,3*mm))
st.append(p('Contact sheets (24 frames each, with timecodes) are in the same folder: contact_amy.jpg, contact_caylee.jpg, contact_noida.jpg.',S))

doc=SimpleDocTemplate(OUT+'STYLE_GUIDE.pdf',pagesize=landscape(A4),leftMargin=14*mm,rightMargin=14*mm,topMargin=11*mm,bottomMargin=11*mm,title='Seldom Style Study v2')
doc.build(st); print('ok',{k:(round(v['cpm'],1),v['wpm']) for k,v in M.items()})
