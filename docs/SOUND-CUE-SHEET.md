# Limitless Success — Sound Design v2 (cue sheet & change log)

## Change log (v1 → v2)

### Removed — every bell / chime / coin-like sound
| Removed | Where it played | Why |
|---|---|---|
| `accent-soft` (bell shimmer) | Legacy title, At-a-glance, Wall of Honour, Streams converge, Value title, Opportunities title, Support title, both award arches, **every award category** | Game-like chime |
| `accent-rise` (whoosh + chime) | Upcoming projects, Five differences, Flight path, Rewards intro, closing title | Chime |
| `accent-bright` (brass + bell sting) | Brokerage, Executive incentives, Payout | Coin/reward-like bells |
| Bell layers inside the old Ananta reveal, Reward 1, Reward 2, Reward 3, opening and finale cues | Those moments | Replaced by library-based cues (below) |
| Bell layers in the background score (opening and luxury beds) | Throughout | Score fully rewritten |

**Accents were also pruned:** award categories, leadership/figures/honours, the partnership and the closing title are now silent, as are the Executive Incentives slide and the support intro.

### Library evaluation (client's Google Drive folder, 11 files)
I analysed the files rather than listening (impact timing, level envelopes, spectrograms, and a ringing/bell detector):

| File | Verdict | Used for |
|---|---|---|
| breakzstudios-epic-cinematic-reveal-logo-201065 | **Used.** Dense 3.5 s build, built-in dip, impact at 4.82 s, epic sustain; harmonic, no bell ring | **ANANTA grand reveal** core |
| breakzstudios-epic-cinematic-logo-reveal-333643 | **Used, tamed.** Big impact at 2.29 s; its tail rings at ~3.1 kHz (metallic), so the tail is low-passed at 1.8 kHz after the transient | **Reward 3** climax impact |
| universfield-logo-reveal-intro-352299 | **Used as-is.** Short swoosh-reveal, peak at 0.59 s, no ringing | **Reward 1** |
| artificiallyinspired-quick-impact-logo-swoosh-reveal-578002 | **Used.** Clean swoosh plus impact, no ringing | **Reward 2** impact layer; chapter-opener whoosh |
| ES_Designed, Stinger, Complex 18 | **Used, tamed.** Rise plus very deep impact at 1.59 s; tail ring removed | Opening title, Reward 3 depth, finale |
| ES_Designed, Riser, Transition, Fast, Short, Clean 01 | **Used.** Clean riser cutting off at 4.17 s | **Reward 2** build |
| ES_Designed, Source, Distorted, Airy Texture, Noisy Surge 02 | **Used.** Airy, non-tonal surge | Reward 3 build; transition surge |
| universfield-clean-logo-reveal-139678 | **Rejected.** Sustained pure partials up to 12 kHz (shimmer/bell) | — |
| ES_Magic, Spell, Transition, Oscillating Chimes 04 | **Rejected.** Chimes (10–12 kHz tonal) | — |
| ES_Magic, Spell, Swell, Short, Mystic Thrill 03 | **Rejected.** Chime swell | — |
| ES_Aircraft, Rocket, …, Ring Out 02 | **Not used.** Metallic ring-out; the deck already has a takeoff sound synced to the runway animation | — |

**Licensing:**
- The **Pixabay** files (breakzstudios, universfield, artificiallyinspired) fall under the Pixabay Content License: free for commercial use including live events, with no attribution required. They must not be redistributed as standalone audio.
- **"350cc bike firing"** (rsn267 via Pixabay, Pixabay Content License: commercial/live use, no attribution) is the Royal Enfield recording used for Reward 3; file `assets/media/sfx/reward-3-enfield.ogg`.
- The **Epidemic Sound** files are used on the client's confirmation that their Epidemic subscription covers live/public use at this event.
- ⚠ The Epidemic copies supplied are **64 kbps** (preview quality). Before the event, re-download the 3 used files (Stinger Complex 18, Riser Fast Short Clean 01, Airy Noisy Surge 02) at full quality from the Epidemic account, then rerun `tools/make-cues.py`.

### New background score (all original; `tools/make-score.py`)
The pad-led beds were replaced with rhythm-led cinematic beds: kick/snare/toms/taiko, spiccato string ostinatos, a hybrid pulse synth with sidechain pumping, brass and sub bass. Tempos rose from 66–112 bpm to **92–128 bpm**. Measured rhythmic drive (envelope pulse on the beat) is **4–11 dB stronger** in every section. There are no bells anywhere in the score.

| Bed | Key · tempo | Sections | Character |
|---|---|---|---|
| prestige | D minor · 92 | Opening, pre-reveal (silhouette, "Ananta emerges") | Taiko heartbeat, hybrid pulse, dark brass |
| legacy | D major · 104 | Jain Group story, leadership, achievements, hotels | Spiccato strings, piano, toms, horns |
| momentum | D major · 116 | Real-estate portfolio, partnerships | Driving 16ths, kick/snare, brass hits |
| luxury | F major · 98 | Ananta lifestyle, master plan, specs, prices | Sleek groove, warm pulse, piano, strings |
| opportunity | E major · 124 | Takeoff headline → brokerage → earnings; rewards recap | Four-on-the-floor, claps, pumping bass, brass stabs |
| tension | A minor · 108 | "Darkens", "deserves more", "beyond brokerage", rewards intro | Low ostinato, taiko and tom builds, tremolo |
| honour | G major · 96 | Award certificates (both parts), support | Anthemic toms, strings, horns |
| finale | D major · 128 | Closing lines, two choices, call to action | Full drums, brass fanfare figures, big toms |

**Dynamic level (automatic):**
- Every slide change lifts the score to **62%** for 4.5 s (transition / visual moment), then it settles to **40%** while the presenter talks.
- On explanation-heavy slides it settles to **28%**: brokerage, incentives, payout, calculator, 71%, specs, configurations, positioning, master plan, airport, figures, hotels, real estate.
- It dips to **28% of that** under the major cues and stays down 3 s after them (the applause window).
- It is silent under both films, the takeoff and the four big reveals.

## Cue sheet (v2)

| Slide | Effect | Built from | Trigger · impact | Level | Score |
|---|---|---|---|---|---|
| LIMITLESS SUCCESS (opening title) | Low rumble and timpani pulse → **Epidemic stinger** rise → deep impact + dark brass chord as the title lands | ES Stinger 18 + original | Next · **4.4 s** | high | prestige |
| Limitless Legacy (Ch. 1) | Clean swoosh-impact | artificiallyinspired 578002 | Next · 0.57 s | low | legacy |
| Real estate · Upcoming | Airy surge | ES Airy Surge 02 | Next | low | momentum |
| **ANANTA grand reveal** (first view of the building after the film) | **breakzstudios 201065**, aligned so its 3.5 s build and built-in dip lead into the impact on the frame the building appears out of the dark. Reinforced by original sub boom and timpani, then an **uplifting orchestral swell** (strings + brass, D major) that carries the excitement and fades by ~11 s while the presenter starts | breakzstudios 201065 + original | Next · **3.5 s** | **highest** | silent, then luxury |
| The difference is visible (Ch. 4) | Swoosh-impact | artificiallyinspired 578002 | Next | low | luxury |
| Flight Path of Success | Airy surge | ES Airy Surge 02 | Next | low | opportunity |
| Limitless Opportunities (Ch. 5) | Swoosh-impact | artificiallyinspired 578002 | Next | low | opportunity |
| Ongoing Brokerage · 7-day payout | Refined brass-and-timpani stinger (no bells) | original | Next · 0.15 s | low-medium | opportunity |
| The landscape darkens | Low boom + descending air + strings | original | Next | medium | tension |
| Awards part 1 / part 2 (trophy arch) | Swoosh-impact | artificiallyinspired 578002 | Next | low | honour |
| LIMITLESS REWARDS intro | Airy surge | ES Airy Surge 02 | Next | low | tension |
| **Reward 1 · MacBook Neo** | Short riser → **clean reveal impact** | universfield 352299 | Next · **0.6 s** | medium (−6 dBFS peak) | silent |
| **Reward 2 · International trip** | **Epidemic clean riser** + snare build → **deeper impact** (swoosh-impact + sub boom + timpani) → **celebratory brass flourish** (G major) | ES Riser 01 + artificiallyinspired + original | Next · **1.6 s** | high (−3 dBFS) | silent, applause window |
| **Reward 3 · Royal Enfield Bullet** | **Real Royal Enfield 350**: the bike fires up as the sun fades → climbing revs (crescendo) → brief shift gap → **hardest rev slams in on the reveal** with a library impact + sub boom → two bars of driving 128 bpm beat under the revs → rev-down fade by ~9 s. Replaces the orchestral build/fanfare | Pixabay "350cc bike firing" (rsn267) + breakzstudios 333643 + original beat | Next · **3.4 s** | **highest** (−0.5 dBFS) | silent, applause window |
| THE CHOICE IS YOURS · Register / Schedule / Start · final QR | **No effect** — background music only (removed at the client's request) | — | — | — | finale |

Every other slide has **no effect**: score only.

**Measured reward escalation (RMS in the 0.5 s after impact):** R1 −19.7 dB → R2 −14.0 dB → R3 −9.3 dB (Royal Enfield version). Each has a different build, impact source and ending.

## Playback rules (unchanged)
- Cues fire only when the presenter moves **forward** onto the slide, or presses **R**. Backward moves, jumps and reloads never fire them.
- One cue at a time: a new cue, or leaving the slide, fades the previous one out.
- One score bed at a time, with a 3 s crossfade.
- **P** freezes all audio in sync.
- **M** mutes everything.
- The bottom-right corner (move the mouse) has an **FX on/off** button and a **volume** slider.
- The presenter console's music toggle still switches the score on and off.
- All audio is decoded into memory at "Click to begin", so nothing streams mid-show.

## Regenerate
```bash
python tools/make-score.py out/score
python tools/make-cues.py  <library_wav_dir> out/cues   # client library decoded to 48 kHz WAV
# encode: ffmpeg -i X.wav -c:a libopus -b:a 160k  (score)  /  -b:a 192k  (cues)  -> assets/media/{score,sfx}/X.ogg
```
