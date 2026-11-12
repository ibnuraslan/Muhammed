# PLAN B — Chapters 3, 4, 5 (chat B)

Look: cinematic grade on every shot (overcast or low late sun, one hard key, haze, teal shadows / amber highlights).
Every camera moves slowly and something in frame moves. Ursula is never shown; the box is always empty evidence.
The convicted man appears only as an unnamed figure, from behind or at medium distance, never committing any act.
Reused from chat A (new angles): Herrmann hallway, lakeside path bend, forest.

## CAST (fixed looks, all film long; unnamed MakeHuman figures, no likenesses) — `b_common.py`

| Person (never named on screen) | Era | Look | Helper |
|---|---|---|---|
| Michael, the brother | 2008–2013 | ~47, slim, short greying hair, dark plain navy sweater | `B.michael()` |
| The acquaintance questioned (Ch3) | 1981 | ~31, slim, longer dark 80s hair, olive work jacket | `B.pfaffinger()` |
| The convicted man | 1981 | 44, heavier and shorter, dark hair, dark brown work shirt; only in his workshop | `B.mazurek(era=1981)` |
| The convicted man | 2007–2010 | 58, heavier, grey hair, grey-green jacket; only at his shop, searched, arrested, in court (behind / medium) | `B.mazurek(era=2007)` |
| The convicted man | 2023 | 72, white hair, same jacket, a holdall; only leaving prison, from behind | `B.mazurek(era=2023)` |
| Detectives 1981 | 1981 | grey suit (older) and brown suit (younger) | interrogation set |
| Judges / prosecutor / counsel | 2009–10 | black robes; the two lay judges in plain civilian clothes | courtroom set |
| Forensic staff | 2000s | plain pale lab gowns (no logos) | DNA lab, phonetics |

## Chapter Three · The Man with the Spade — 339 words ≈ 1 min 51 s (+3 s title lead)

| Set | Script line | Shot A | Shot B |
|---|---|---|---|
| Path bend (A's set, seen from the woods side, low late sun) | "...a hundred and forty meters of green wire through the trees..." | Title card; slow crane down as an investigator in a 1981 parka follows a low green wire between the trunks. | Knee-height dolly along the wire to the second lookout spot, where a second officer looks back down the path. |
| 1981 forensic lab | "Forensic investigators lift a fingerprint from adhesive tape on the box." | Medium shot: a technician in a white coat brushes powder on a tape strip on the empty box under a hard lamp. | Slow push as she lays a lifted tape card under a magnifier lamp; dust hangs in the light. |
| Fingerprint card archive | "...around twenty thousand fingerprints. They find no match..." | A clerk walks a long aisle of card drawers and pulls one open. | Two officers compare cards at a light table, one shakes his head and sets a card aside. |
| TV repair workshop (dusk) | "...a trained mechanic with a television repair business and substantial debts." | A man seen from behind works at a soldering bench, CRT sets flicker, an oscilloscope trace moves. | Slow push past a pile of unopened debt letters on the bench, the man soft in the background. |
| 1981 living room | "...playing the board game Risk with his wife and two friends." | Four figures around a lamp-lit generic map board game, one rolls dice. | Next day, grey light: two detectives lift cushions and open a sideboard, then leave empty-handed. |
| Rented flat exterior | "His landlord has reported seeing him with a spade strapped to his moped..." | A moped with a spade strapped on the side idles outside a plain 1970s block, exhaust drifting. | The landlord behind a lace curtain upstairs watches; camera pushes slowly toward the window. |
| 1981 interrogation room | "Under questioning, Pfaffinger tells the detectives..." | Two detectives sit across from a man, a reel recorder turns, cigarette smoke curls in the lamp. | The man holds his hands apart to show a size, a detective writes it down (medium). |
| Forest (A's woods, new angle, overcast) | "...the detectives take him into the woods... He fails to lead them to it." | Three men walk through spruces, the man in front slows and looks around. | He points one way, turns, points another; the detectives exchange a glance. |
| Interrogation room (reverse angle, night) | "Back at the police station, he retracts his story." | The man shakes his head and pushes the typed statement back across the table. | The door opens; he walks out down a dim corridor with his coat over his arm. |
| 1980s TV studio | "A television appeal puts the case in front of viewers across West Germany." | A presenter at a plain desk under studio lights, a studio camera dollies past. | Officers at a row of desks answer ringing phones and write tips on slips. |
| Steel cabinet archive | "...the files on the leads fill twelve steel cabinets... The calls are still on tape." | Slow track along twelve grey cabinets as a clerk slides a drawer shut. | Push to a tape box on top of the last cabinet as the fluorescent tube flickers and dims. |

## Chapter Four · The Clicks — 615 words ≈ 3 min 21 s (+3 s title lead)

| Set | Script line | Shot A | Shot B |
|---|---|---|---|
| 2000s DNA lab | "...investigators go back to the physical evidence. This time, they have DNA profiling." | Title card; a technician in mask and gown swabs a corner of the empty box on a steel table (medium). | A sequencer's trays slide in and a monitor draws peaks as she watches. |
| DNA lab, evidence bench | "...one from a screw appears to match a sample from a drinking glass..." | An analyst lays a bagged screw beside a bagged glass on a light table. | She leans back from a printout, then slides the two bags apart. |
| Northern harbour town 2007 (overcast) | "Mazurek has moved to northern Germany and sells boat accessories." | Wide: boats bob in a grey harbour, gulls cross, a small shop on the quay. | Inside the shop a man seen from behind hangs coils of rope among fenders and buoys. |
| 2007 investigation office | "...carries a thirty-year limitation period." | A detective pins a file to a cork wall as rain runs down the window. | Slow push past file boxes to a wall clock whose second hand ticks. |
| Surveillance car | "Police put Mazurek under surveillance..." | Two officers in a parked 2000s car at dusk watch the shop across the road; a wiper sweeps. | Over their shoulders, through the windscreen, the man locks the shop and walks off. |
| House search 2007 | "...and search his home. They take a saliva sample." | Officers in gloves carry evidence boxes down a hallway past the camera. | Medium: an officer hands a swab tube to a man seated at a kitchen table, seen from behind. |
| House front steps | "...something he says he bought at a flea market just weeks earlier." | An officer carries a reel-to-reel recorder in an open evidence box down the steps to a van. | Memory haze: a flea-market stall with old radios and a reel recorder, shoppers drift past. |
| Evidence bench (hard top light) | "A reel-to-reel tape recorder. A Grundig TK Two Forty-Eight." | The unbadged recorder sits on a black bench, slow orbit as its reels begin to turn. | Low push across its keys and VU meter, the needle twitching. |
| Forensic phonetics lab | "A forensic phonetics specialist... listens to the old calls." | The expert in headphones in front of waveform screens, slow push from behind. | Over her shoulder: three waveform segments line up on a screen as a cursor sweeps them. |
| Phonetics lab, test bench | "Investigators test eleven comparable recorders." | Slow track along eleven reel-to-reel recorders on a long bench, reels starting one by one. | The seized recorder at the end with a microphone in front, its pause key drops, a waveform jumps behind. |
| Dawn street 2008 | "Police arrest Mazurek in May 2008." | Blue dawn: two unmarked cars stop outside a house, officers walk up the path. | Medium from behind: a man is led to a car, the door shuts, the car pulls away. |
| 2009 courtroom (Augsburg style) | "In court, his explanation is still the flea market." | The defendant seen from behind in the dock while his lawyer stands to speak. | An elderly market seller in the witness chair shrugs and shakes his head. |
| Michael's study | "He asks to see the files and reads thousands of pages..." | A man in his forties reads at a desk stacked with binders under a desk lamp, turning a page. | He stops, looks up toward an upright piano in the dark behind him; slow push. |
| Court reconstruction 1: the table | "...someone records and edits the jingle on the Grundig. That version is copied onto a smaller player." | Label "Court reconstruction": a 1980 radio plays beside the recorder, its reels turning, VU needle bouncing. | Track to a small cassette player beside it, its record light on and spools turning. |
| Court reconstruction 2: the phone booth | "The player goes to a public phone booth, where its speaker plays into the mouthpiece." | A yellow phone booth on a dark country road, a faceless figure from behind steps inside. | From behind the figure: the small player is held up to the mouthpiece, the booth light buzzing. |
| Court reconstruction 3: the line | "The signal travels down the phone line and is recorded at the Herrmanns' end." | Track along telephone wires on wooden poles across a dusk field toward the village lights. | Herrmann hallway (A's set, from the stairs side): the police reel recorder turns beside the rotary phone. |
| Michael's study (night) | "If you hear a click on the police tape, where did it enter the chain?" | Michael in headphones replays the tape on a laptop, a waveform loops, slow push. | He types his objections at the desk, a printer feeds pages into the lamplight. |

## Chapter Five · After the Verdict — 405 words ≈ 2 min 12 s (+3 s title lead)

| Set | Script line | Shot A | Shot B |
|---|---|---|---|
| 2010 courtroom | "The judges weigh the tape alongside the rest of the evidence." | Title card; slow push to the panelled judges' bench as the presiding judge turns pages. | A clerk carries a pair of bagged binoculars to the exhibit table under the window light. |
| 2010 courtroom (verdict) | "In March 2010... the court finds Werner Mazurek guilty..." | Wide from the public seats: everyone rises as the judges stand to read. | From behind the dock: the man stands still while reporters' heads turn in the gallery. |
| Federal court exterior | "Germany's Federal Court of Justice upholds the conviction." | Wide, overcast: a long modern stone court building, flags moving, people on the steps. | A lawyer in a coat walks down the steps past press cameras. |
| Civil court corridor 2013 | "In 2013, he sues Mazurek for twenty thousand euros." | Michael walks down a long corridor carrying a folder, footsteps echoing. | He sits on a bench outside a courtroom door and waits, slow push. |
| Michael's music room | "Michael has developed tinnitus..." | He plays a few notes on the piano and stops; the room goes still, slow push. | Night: he sits on the piano bench facing the dark window, the camera creeping in. |
| Physicist's home workbench | "...spends about a year testing it against the call recordings." | An older man in headphones listens at a cluttered workbench, the borrowed recorder's reels turning. | Calendar pages fall away as the window light swings from summer to winter across the bench. |
| Civil courtroom | "The civil court initially awards Michael seven thousand euros." | A small civil courtroom, a single judge reads the ruling, Michael seen from behind. | Boarding school in fog: an old school building beyond the woods, fog drifting past, no figure. |
| Civil courtroom (empty) | "The award is overturned on appeal in 2020." | The emptied courtroom, a clerk stacks files and switches off a light. | Slow pull back as the last ceiling light goes out over the empty bench. |
| Prison gate, dawn 2023 | "In June 2023... Mazurek is released on probation." | The steel gate slides open at dawn and a man walks out, seen from behind. | Wide: he walks away along the long prison wall into the haze. |
| TV edit suite 2024 | "In 2024, German public broadcasters revisit the case..." | Two journalists watch archive footage on monitors in a dark edit suite, scrubbing it. | A reel-to-reel image paused on screen, the camera drifting past their silhouettes. |
| Herrmann hallway (A's set, low angle from the floor) | "Two names. Something her daughter would know. On the other end of the line, nobody answered." | Slow push along the dark hallway toward the phone table, the police reels turning. | The receiver lies off the hook; the reels slow and stop; silence. |
