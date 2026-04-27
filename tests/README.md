# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

This system scores every song in the catalog based on a user's preferences for genre, mood, energy, valence, danceability, and acousticness. Genre and mood are the most important because they show what a listener truly wants at any moment. Numeric features are scored by how close they are to the target rather than just by loudness or speed. A song that matches your desired energy ranks higher than one that is only louder or faster. Each recommendation comes with a clear explanation so you can understand why a song was selected.

- Each `Song` uses: `genre`, `mood`, `energy`, `valence`, `danceability`, `acousticness`
- The `UserProfile` stores: a preferred genre, mood, and target value for each numeric feature
- Scores are computed as a weighted proximity sum, normalized to a 0.0–1.0 scale
- All 18 songs are scored and sorted; the top k are returned with explanations

---

### Algorithm Recipe

**Step 1 — Load the Catalog**
Read every row from `songs.csv` and cast numeric columns (`energy`, `valence`, `danceability`, `acousticness`, `tempo_bpm`) from strings to floats. All 18 songs enter the scoring pipeline.

**Step 2 — Score Each Song**
For every song, compute a normalized score in [0.0, 1.0] using this formula:

```
score = (
    0.30 × genre_match        +   # 1.0 if exact match, else 0.0
    0.30 × mood_match         +   # 1.0 if exact match, else 0.0
    0.20 × (1 − |song.energy       − user.energy|)       +
    0.12 × (1 − |song.valence      − user.valence|)      +
    0.05 × (1 − |song.danceability − user.danceability|) +
    0.03 × (1 − |song.acousticness − user.acousticness|)
)
```

Weight rationale:
- **Genre (0.30)** and **mood (0.30)** together carry 60% of the score. Genre is a hard stylistic boundary; mood is the user's emotional intent. They are weighted equally because mood cuts across genres — a chill user might enjoy lofi *or* ambient *or* jazz.
- **Energy (0.20)** is the most discriminating numeric feature in the catalog (range 0.28–0.97), so it gets the strongest numeric weight.
- **Valence (0.12)**, **danceability (0.05)**, and **acousticness (0.03)** handle fine-grained refinement once the top candidates are already surfaced.

**Step 3 — Generate an Explanation**
After scoring, the system checks which features drove the result:
- Exact genre or mood match → named explicitly
- Numeric similarity ≥ 0.85 → noted as "close to your target"
- No strong signal → falls back to "partial match across multiple features"

**Step 4 — Rank and Return Top K**
All 18 scored songs are sorted by score descending. The top `k` (default 5) are returned as `(song, score, explanation)` tuples. No song is excluded before scoring.

---

### Potential Biases

- **Genre over-prioritization:** Because genre and mood together account for 60% of the score, a song that perfectly matches genre and mood but has mismatched energy will still outrank a song with no genre match but a near-perfect numeric profile. A user who listens across genres could miss great discoveries.
- **Small catalog amplifies exact-match luck:** With 15 distinct genres across only 18 songs, most genres appear just once. If a user's favorite genre has no representative in the catalog, they score at most 0.70 — effectively penalized for an unusual taste, not a flaw in their preferences.
- **Mood labels are subjective:** "Chill" and "relaxed" feel similar to a human listener, but the binary match treats them as completely different. A jazz fan in a relaxed mood gets no mood credit for a chill lofi song, even though the vibe is close.
- **No listening history:** The system treats every user identically on the first run. It cannot learn that a specific user always skips high-energy songs despite listing `intense` as their favorite mood.

---

### Sample Output — `pop / happy / energy 0.8` profile

```
============================================================
                   MUSIC RECOMMENDATIONS
               For: pop / happy / energy 0.8
============================================================

  #1  Sunrise City by Neon Echo
       [####################] 4.96 / 5.0
       Genre: pop  |  Mood: happy
       Why recommended:
         - genre match (+2.0)
         - mood match (+1.0)
         - energy 0.82 vs target 0.80 (+0.98)
         - valence 0.84 vs target 0.82 (+0.59)
         - danceability 0.79 vs target 0.78 (+0.25)
         - acousticness 0.18 vs target 0.20 (+0.15)

  #2  Gym Hero by Max Pulse
       [###############-----] 3.79 / 5.0
       Genre: pop  |  Mood: intense
       Why recommended:
         - genre match (+2.0)
         - energy 0.93 vs target 0.80 (+0.87)
         - valence 0.77 vs target 0.82 (+0.57)
         - danceability 0.88 vs target 0.78 (+0.23)
         - acousticness 0.05 vs target 0.20 (+0.13)

  #3  Rooftop Lights by Indigo Parade
       [############--------] 2.92 / 5.0
       Genre: indie pop  |  Mood: happy
       Why recommended:
         - mood match (+1.0)
         - energy 0.76 vs target 0.80 (+0.96)
         - valence 0.81 vs target 0.82 (+0.59)
         - danceability 0.82 vs target 0.78 (+0.24)
         - acousticness 0.35 vs target 0.20 (+0.13)

  #4  Golden Hour by The Drift
       [###########---------] 2.76 / 5.0
       Genre: soul  |  Mood: happy
       Why recommended:
         - mood match (+1.0)
         - energy 0.65 vs target 0.80 (+0.85)
         - valence 0.88 vs target 0.82 (+0.56)
         - danceability 0.77 vs target 0.78 (+0.25)
         - acousticness 0.55 vs target 0.20 (+0.10)

  #5  Block by Block by Cipher K
       [########------------] 1.92 / 5.0
       Genre: hip-hop  |  Mood: uplifting
       Why recommended:
         - energy 0.78 vs target 0.80 (+0.98)
         - valence 0.76 vs target 0.82 (+0.56)
         - danceability 0.85 vs target 0.78 (+0.23)
         - acousticness 0.15 vs target 0.20 (+0.14)

============================================================
```

**Why this output is correct for the `pop / happy` profile:**
- `#1 Sunrise City` is the only song hitting genre + mood + all numeric features simultaneously — near-perfect 4.96/5.0 is expected.
- `#2 Gym Hero` keeps its high rank from the genre match (+2.0) despite missing the mood match — genre weight dominates.
- `#3–#4` have no genre match but earn mood credit (+1.0 each) and score well on energy/valence proximity.
- `#5 Block by Block` earns its slot purely on numeric similarity — zero categorical matches, but energy 0.78 and valence 0.76 are both very close to the user's targets.

---

## Terminal Output — All Profiles

Run with `python -m src.main`. Results for every named and adversarial profile are shown below.

---

### Profile 1 — High-Energy Pop

```
============================================================
                      HIGH-ENERGY POP                       
                  pop / happy / energy 0.9                  
============================================================

  #1  Sunrise City by Neon Echo
       [###################-] 4.87 / 5.0
       Genre: pop  |  Mood: happy
       Why recommended:
         - genre match (+2.0)
         - mood match (+1.0)
         - energy 0.82 vs target 0.90 (+0.92)
         - valence 0.84 vs target 0.85 (+0.59)
         - danceability 0.79 vs target 0.88 (+0.23)
         - acousticness 0.18 vs target 0.05 (+0.13)

  #2  Gym Hero by Max Pulse
       [################----] 3.92 / 5.0
       Genre: pop  |  Mood: intense
       Why recommended:
         - genre match (+2.0)
         - energy 0.93 vs target 0.90 (+0.97)
         - valence 0.77 vs target 0.85 (+0.55)
         - danceability 0.88 vs target 0.88 (+0.25)
         - acousticness 0.05 vs target 0.05 (+0.15)

  #3  Rooftop Lights by Indigo Parade
       [###########---------] 2.78 / 5.0
       Genre: indie pop  |  Mood: happy
       Why recommended:
         - mood match (+1.0)
         - energy 0.76 vs target 0.90 (+0.86)
         - valence 0.81 vs target 0.85 (+0.58)
         - danceability 0.82 vs target 0.88 (+0.23)
         - acousticness 0.35 vs target 0.05 (+0.10)

  #4  Golden Hour by The Drift
       [###########---------] 2.63 / 5.0
       Genre: soul  |  Mood: happy
       Why recommended:
         - mood match (+1.0)
         - energy 0.65 vs target 0.90 (+0.75)
         - valence 0.88 vs target 0.85 (+0.58)
         - danceability 0.77 vs target 0.88 (+0.22)
         - acousticness 0.55 vs target 0.05 (+0.07)

  #5  Block by Block by Cipher K
       [#######-------------] 1.80 / 5.0
       Genre: hip-hop  |  Mood: uplifting
       Why recommended:
         - energy 0.78 vs target 0.90 (+0.88)
         - valence 0.76 vs target 0.85 (+0.55)
         - danceability 0.85 vs target 0.88 (+0.24)
         - acousticness 0.15 vs target 0.05 (+0.14)

============================================================
```

**Observation:** Sunrise City wins easily with genre + mood + near-perfect numerics (4.87/5.0). Gym Hero holds #2 on genre alone despite missing the mood match — demonstrates how 2.0 genre weight dominates. #3–#5 have no genre match; they survive on mood credit or numeric proximity only.

---

### Profile 2 — Chill Lofi

```
============================================================
                         CHILL LOFI                         
                 lofi / chill / energy 0.3                  
============================================================

  #1  Library Rain by Paper Lanterns
       [###################-] 4.78 / 5.0
       Genre: lofi  |  Mood: chill
       Why recommended:
         - genre match (+2.0)
         - mood match (+1.0)
         - energy 0.35 vs target 0.30 (+0.95)
         - valence 0.60 vs target 0.45 (+0.51)
         - danceability 0.58 vs target 0.35 (+0.19)
         - acousticness 0.86 vs target 0.70 (+0.13)

  #2  Midnight Coding by LoRoom
       [###################-] 4.75 / 5.0
       Genre: lofi  |  Mood: chill
       Why recommended:
         - genre match (+2.0)
         - mood match (+1.0)
         - energy 0.42 vs target 0.30 (+0.88)
         - valence 0.56 vs target 0.45 (+0.53)
         - danceability 0.62 vs target 0.35 (+0.18)
         - acousticness 0.71 vs target 0.70 (+0.15)

  #3  Focus Flow by LoRoom
       [###############-----] 3.74 / 5.0
       Genre: lofi  |  Mood: focused
       Why recommended:
         - genre match (+2.0)
         - energy 0.40 vs target 0.30 (+0.90)
         - valence 0.59 vs target 0.45 (+0.52)
         - danceability 0.60 vs target 0.35 (+0.19)
         - acousticness 0.78 vs target 0.70 (+0.14)

  #4  Spacewalk Thoughts by Orbit Bloom
       [###########---------] 2.81 / 5.0
       Genre: ambient  |  Mood: chill
       Why recommended:
         - mood match (+1.0)
         - energy 0.28 vs target 0.30 (+0.98)
         - valence 0.65 vs target 0.45 (+0.48)
         - danceability 0.41 vs target 0.35 (+0.23)
         - acousticness 0.92 vs target 0.70 (+0.12)

  #5  Velvet Dusk by Celeste Noir
       [#######-------------] 1.71 / 5.0
       Genre: classical  |  Mood: melancholic
       Why recommended:
         - energy 0.52 vs target 0.30 (+0.78)
         - valence 0.43 vs target 0.45 (+0.59)
         - danceability 0.28 vs target 0.35 (+0.23)
         - acousticness 0.96 vs target 0.70 (+0.11)

============================================================
```

**Observation:** Three lofi songs dominate the top 3 — the catalog has enough lofi coverage to serve this profile well. #5 Velvet Dusk (classical/melancholic) sneaks in with no categorical match, surviving only on acousticness and energy proximity.

---

### Profile 3 — Deep Intense Rock

```
============================================================
                     DEEP INTENSE ROCK                      
                rock / intense / energy 0.92                
============================================================

  #1  Storm Runner by Voltline
       [###################-] 4.81 / 5.0
       Genre: rock  |  Mood: intense
       Why recommended:
         - genre match (+2.0)
         - mood match (+1.0)
         - energy 0.91 vs target 0.92 (+0.99)
         - valence 0.48 vs target 0.30 (+0.49)
         - danceability 0.66 vs target 0.40 (+0.18)
         - acousticness 0.10 vs target 0.08 (+0.15)

  #2  Drop Zone by Axel Wave
       [###########---------] 2.64 / 5.0
       Genre: electronic  |  Mood: intense
       Why recommended:
         - mood match (+1.0)
         - energy 0.95 vs target 0.92 (+0.97)
         - valence 0.62 vs target 0.30 (+0.41)
         - danceability 0.92 vs target 0.40 (+0.12)
         - acousticness 0.03 vs target 0.08 (+0.14)

  #3  Gym Hero by Max Pulse
       [##########----------] 2.58 / 5.0
       Genre: pop  |  Mood: intense
       Why recommended:
         - mood match (+1.0)
         - energy 0.93 vs target 0.92 (+0.99)
         - valence 0.77 vs target 0.30 (+0.32)
         - danceability 0.88 vs target 0.40 (+0.13)
         - acousticness 0.05 vs target 0.08 (+0.15)

  #4  Fury Road by Iron Siege
       [#######-------------] 1.86 / 5.0
       Genre: metal  |  Mood: angry
       Why recommended:
         - energy 0.97 vs target 0.92 (+0.95)
         - valence 0.31 vs target 0.30 (+0.59)
         - danceability 0.71 vs target 0.40 (+0.17)
         - acousticness 0.04 vs target 0.08 (+0.14)

  #5  Night Drive Loop by Neon Echo
       [######--------------] 1.61 / 5.0
       Genre: synthwave  |  Mood: moody
       Why recommended:
         - energy 0.75 vs target 0.92 (+0.83)
         - valence 0.49 vs target 0.30 (+0.49)
         - danceability 0.73 vs target 0.40 (+0.17)
         - acousticness 0.22 vs target 0.08 (+0.13)

============================================================
```

**Observation:** Storm Runner is the clear winner with a near-perfect categorical + numeric fit (4.81/5.0). The gap to #2 is large (2.17 points) because rock only has one catalog entry. #2–#4 all share the "intense" mood, showing mood acting as a secondary tiebreaker.

---

### Edge Case 1 — Conflicting: High Energy + Sad Mood

```
============================================================
        EDGE 1 - Conflicting: high energy + sad mood        
                  indie / sad / energy 0.9                  
============================================================

  #1  Broken Clocks by Sable Lane
       [##########----------] 2.40 / 5.0
       Genre: r&b  |  Mood: sad
       Why recommended:
         - mood match (+1.0)
         - energy 0.45 vs target 0.90 (+0.55)
         - valence 0.32 vs target 0.15 (+0.50)
         - danceability 0.55 vs target 0.50 (+0.24)
         - acousticness 0.62 vs target 0.40 (+0.12)

  #2  Fury Road by Iron Siege
       [#######-------------] 1.73 / 5.0
       Genre: metal  |  Mood: angry
       Why recommended:
         - energy 0.97 vs target 0.90 (+0.93)
         - valence 0.31 vs target 0.15 (+0.50)
         - danceability 0.71 vs target 0.50 (+0.20)
         - acousticness 0.04 vs target 0.40 (+0.10)

  #3  Storm Runner by Voltline
       [#######-------------] 1.71 / 5.0
       Genre: rock  |  Mood: intense
       Why recommended:
         - energy 0.91 vs target 0.90 (+0.99)
         - valence 0.48 vs target 0.15 (+0.40)
         - danceability 0.66 vs target 0.50 (+0.21)
         - acousticness 0.10 vs target 0.40 (+0.10)

  #4  Night Drive Loop by Neon Echo
       [######--------------] 1.56 / 5.0
       Genre: synthwave  |  Mood: moody
       Why recommended:
         - energy 0.75 vs target 0.90 (+0.85)
         - valence 0.49 vs target 0.15 (+0.40)
         - danceability 0.73 vs target 0.50 (+0.19)
         - acousticness 0.22 vs target 0.40 (+0.12)

  #5  Drop Zone by Axel Wave
       [######--------------] 1.51 / 5.0
       Genre: electronic  |  Mood: intense
       Why recommended:
         - energy 0.95 vs target 0.90 (+0.95)
         - valence 0.62 vs target 0.15 (+0.32)
         - danceability 0.92 vs target 0.50 (+0.14)
         - acousticness 0.03 vs target 0.40 (+0.09)

============================================================
```

**Observation (bias found):** The system is "tricked." #1 Broken Clocks wins on the mood match but its energy (0.45) is half the user's target (0.90) — the song is low-energy and sad, not high-energy and sad. The catalog contains no high-energy sad songs, so the scoring splits its loyalty between a slow sad song and fast angry/intense songs. Neither is a good match.

---

### Edge Case 2 — Rare Genre (Bossa Nova)

```
============================================================
              EDGE 2 - Rare genre (bossa nova)              
              bossa nova / chill / energy 0.35              
============================================================

  #1  Library Rain by Paper Lanterns
       [############--------] 2.95 / 5.0
       Genre: lofi  |  Mood: chill
       Why recommended:
         - mood match (+1.0)
         - energy 0.35 vs target 0.35 (+1.00)
         - valence 0.60 vs target 0.60 (+0.60)
         - danceability 0.58 vs target 0.50 (+0.23)
         - acousticness 0.86 vs target 0.65 (+0.12)

  #2  Midnight Coding by LoRoom
       [###########---------] 2.87 / 5.0
       Genre: lofi  |  Mood: chill
       Why recommended:
         - mood match (+1.0)
         - energy 0.42 vs target 0.35 (+0.93)
         - valence 0.56 vs target 0.60 (+0.58)
         - danceability 0.62 vs target 0.50 (+0.22)
         - acousticness 0.71 vs target 0.65 (+0.14)

  #3  Spacewalk Thoughts by Orbit Bloom
       [###########---------] 2.84 / 5.0
       Genre: ambient  |  Mood: chill
       Why recommended:
         - mood match (+1.0)
         - energy 0.28 vs target 0.35 (+0.93)
         - valence 0.65 vs target 0.60 (+0.57)
         - danceability 0.41 vs target 0.50 (+0.23)
         - acousticness 0.92 vs target 0.65 (+0.11)

  #4  Focus Flow by LoRoom
       [########------------] 1.90 / 5.0
       Genre: lofi  |  Mood: focused
       Why recommended:
         - energy 0.40 vs target 0.35 (+0.95)
         - valence 0.59 vs target 0.60 (+0.59)
         - danceability 0.60 vs target 0.50 (+0.23)
         - acousticness 0.78 vs target 0.65 (+0.13)

  #5  Coffee Shop Stories by Slow Stereo
       [#######-------------] 1.87 / 5.0
       Genre: jazz  |  Mood: relaxed
       Why recommended:
         - energy 0.37 vs target 0.35 (+0.98)
         - valence 0.71 vs target 0.60 (+0.53)
         - danceability 0.54 vs target 0.50 (+0.24)
         - acousticness 0.89 vs target 0.65 (+0.11)

============================================================
```

**Observation (bias found):** The best possible score is 2.95/5.0 — the system silently penalizes the user 2.0 points simply because their genre doesn't exist in the catalog. A user with unusual taste is not served worse because of their preferences; they are served worse because of a data gap.

---

### Edge Case 3 — All Numerics at 0.5 (Perfectly Average)

```
============================================================
      EDGE 3 - All numerics at 0.5 (perfectly average)      
                jazz / relaxed / energy 0.5                 
============================================================

  #1  Coffee Shop Stories by Slow Stereo
       [###################-] 4.68 / 5.0
       Genre: jazz  |  Mood: relaxed
       Why recommended:
         - genre match (+2.0)
         - mood match (+1.0)
         - energy 0.37 vs target 0.50 (+0.87)
         - valence 0.71 vs target 0.50 (+0.47)
         - danceability 0.54 vs target 0.50 (+0.24)
         - acousticness 0.89 vs target 0.50 (+0.09)

  #2  Midnight Coding by LoRoom
       [#######-------------] 1.82 / 5.0
       Genre: lofi  |  Mood: chill
       Why recommended:
         - energy 0.42 vs target 0.50 (+0.92)
         - valence 0.56 vs target 0.50 (+0.56)
         - danceability 0.62 vs target 0.50 (+0.22)
         - acousticness 0.71 vs target 0.50 (+0.12)

  #3  Velvet Dusk by Celeste Noir
       [#######-------------] 1.81 / 5.0
       Genre: classical  |  Mood: melancholic
       Why recommended:
         - energy 0.52 vs target 0.50 (+0.98)
         - valence 0.43 vs target 0.50 (+0.56)
         - danceability 0.28 vs target 0.50 (+0.20)
         - acousticness 0.96 vs target 0.50 (+0.08)

  #4  Broken Clocks by Sable Lane
       [#######-------------] 1.81 / 5.0
       Genre: r&b  |  Mood: sad
       Why recommended:
         - energy 0.45 vs target 0.50 (+0.95)
         - valence 0.32 vs target 0.50 (+0.49)
         - danceability 0.55 vs target 0.50 (+0.24)
         - acousticness 0.62 vs target 0.50 (+0.13)

  #5  Focus Flow by LoRoom
       [#######-------------] 1.78 / 5.0
       Genre: lofi  |  Mood: focused
       Why recommended:
         - energy 0.40 vs target 0.50 (+0.90)
         - valence 0.59 vs target 0.50 (+0.55)
         - danceability 0.60 vs target 0.50 (+0.23)
         - acousticness 0.78 vs target 0.50 (+0.11)

============================================================
```

**Observation (bias found):** #2–#5 all cluster between 1.78–1.82, separated by hundredths. With no numeric differentiation, genre/mood luck determines everything. A user who genuinely has no strong numeric preferences gets extremely similar scores across almost the entire catalog — rankings become nearly arbitrary.

---

### Edge Case 4 — Acoustic Metalhead (Contradictory)

```
============================================================
        EDGE 4 - Acoustic metalhead (contradictory)         
               metal / intense / energy 0.95                
============================================================

  #1  Fury Road by Iron Siege
       [###############-----] 3.67 / 5.0
       Genre: metal  |  Mood: angry
       Why recommended:
         - genre match (+2.0)
         - energy 0.97 vs target 0.95 (+0.98)
         - valence 0.31 vs target 0.20 (+0.53)
         - danceability 0.71 vs target 0.30 (+0.15)
         - acousticness 0.04 vs target 1.00 (+0.01)

  #2  Storm Runner by Voltline
       [##########----------] 2.57 / 5.0
       Genre: rock  |  Mood: intense
       Why recommended:
         - mood match (+1.0)
         - energy 0.91 vs target 0.95 (+0.96)
         - valence 0.48 vs target 0.20 (+0.43)
         - danceability 0.66 vs target 0.30 (+0.16)
         - acousticness 0.10 vs target 1.00 (+0.01)

  #3  Drop Zone by Axel Wave
       [##########----------] 2.45 / 5.0
       Genre: electronic  |  Mood: intense
       Why recommended:
         - mood match (+1.0)
         - energy 0.95 vs target 0.95 (+1.00)
         - valence 0.62 vs target 0.20 (+0.35)
         - danceability 0.92 vs target 0.30 (+0.09)
         - acousticness 0.03 vs target 1.00 (+0.00)

  #4  Gym Hero by Max Pulse
       [#########-----------] 2.35 / 5.0
       Genre: pop  |  Mood: intense
       Why recommended:
         - mood match (+1.0)
         - energy 0.93 vs target 0.95 (+0.98)
         - valence 0.77 vs target 0.20 (+0.26)
         - danceability 0.88 vs target 0.30 (+0.10)
         - acousticness 0.05 vs target 1.00 (+0.01)

  #5  Velvet Dusk by Celeste Noir
       [######--------------] 1.42 / 5.0
       Genre: classical  |  Mood: melancholic
       Why recommended:
         - energy 0.52 vs target 0.95 (+0.57)
         - valence 0.43 vs target 0.20 (+0.46)
         - danceability 0.28 vs target 0.30 (+0.24)
         - acousticness 0.96 vs target 1.00 (+0.14)

============================================================
```

**Observation (bias found):** The acousticness feature is effectively silenced. Fury Road earns only +0.01 on acousticness (0.04 vs target 1.00) yet wins by a large margin. The user's most distinctive preference — wanting a fully acoustic sound — contributes almost nothing to the ranking because the feature weight (0.15) is small and every high-energy song in the catalog is near 0.0 acousticness. The system cannot satisfy this user; it just ignores the impossible preference.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

   ```
2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

### Does the Deep Intense Rock result "feel" right?

**Profile:** `rock / intense / energy 0.92 / valence 0.30 / danceability 0.40 / acousticness 0.08`

**Top result:** Storm Runner by Voltline — 4.81 / 5.0

Intuitively, yes — Storm Runner is rock, it's tagged intense, and it has energy 0.91 (one hundredth below the target). That feels correct. The system agrees with what a human would reach for first.

What does *not* feel right is the ranking below #1:

| Rank | Song | Genre | Intuition verdict |
|---|---|---|---|
| #1 | Storm Runner | rock | Correct — exact genre + mood + energy |
| #2 | Drop Zone | electronic | Feels wrong — electronic is far from rock |
| #3 | Gym Hero | pop | Feels wrong — pop is far from rock |
| #4 | Fury Road | metal | **Should be #2** — metal is rock's closest neighbor |

Fury Road (metal, angry, energy 0.97) is sonically almost identical to what a rock fan wants, yet the system ranks it *dead last* among these four. Why? The binary genre match gives metal zero genre credit even though metal and rock share almost everything — distorted guitars, high energy, aggressive mood. Drop Zone (electronic) earns mood credit (+1.0 for "intense") and beats Fury Road despite being a completely different sonic world.

---

### Why did Storm Runner rank #1? — Inline scoring explanation

The scoring formula in `recommender.py` (lines 52–59) awards points this way:

```
POINTS = {
    "genre":        2.00,   # binary: exact match = 2.0, else 0.0
    "mood":         1.00,   # binary: exact match = 1.0, else 0.0
    "energy":       1.00,   # proximity: 1.0 × (1 − |song − target|)
    "valence":      0.60,
    "danceability": 0.25,
    "acousticness": 0.15,
}   # MAX = 5.0
```

Here is the exact breakdown for Storm Runner vs the rock/intense profile:

```
genre        :  2.000 / 2.00   ← exact match "rock"
mood         :  1.000 / 1.00   ← exact match "intense"
energy       :  0.990 / 1.00   ← 1.0 × (1 − |0.91 − 0.92|) = 0.99
valence      :  0.492 / 0.60   ← 0.6 × (1 − |0.48 − 0.30|) = 0.49
danceability :  0.185 / 0.25   ← 0.25 × (1 − |0.66 − 0.40|) = 0.19
acousticness :  0.147 / 0.15   ← 0.15 × (1 − |0.10 − 0.08|) = 0.15
─────────────────────────────
Total        :  4.814 / 5.00   (96.3% of maximum)
```

The categorical features alone (genre + mood) contribute **3.0 of 4.81 points — 62% of the score.** The numeric features only need to be reasonable, not perfect. Storm Runner wins because it is one of only two songs that match both "rock" AND "intense" simultaneously, and its energy (0.91) is essentially perfect.

Compare to Fury Road (metal, angry), which has *better* numeric proximity overall (37.2% vs 36.3% numeric share) but scores only **1.86 / 5.0** — it earns zero categorical points because genre="metal" ≠ "rock" and mood="angry" ≠ "intense". The genre cliff costs it 2.0 points instantly.

---

### What this reveals about the weights

The genre weight (2.00) accounts for **40% of the maximum score** by itself. This means:
- A song that matches genre but has terrible numerics will almost always beat a song that doesn't match genre but has perfect numerics.
- Adjacent genres (rock/metal, lofi/ambient, pop/indie pop) are treated as completely unrelated — the same penalty as comparing pop to classical.
- The catalog being small (18 songs, 15 genres) amplifies this: most genres appear only once, so a genre miss is hard to recover from.

**The genre weight is not too strong for simple profiles** (the results feel right for High-Energy Pop and Chill Lofi). But for profiles where the user's genre has close neighbors in the catalog — rock vs metal, indie vs indie pop — the binary match creates rankings that feel musically wrong.

---

### Sensitivity Experiment — Double Energy, Halve Genre

**Change made to `recommender.py`:**

```python
# Before
"genre":  2.00,
"energy": 1.00,

# After (experiment)
"genre":  1.00,
"energy": 2.00,
```

MAX_SCORE remains 5.0 because the total is unchanged: 1.00 + 1.00 + 2.00 + 0.60 + 0.25 + 0.15 = 5.0. The bar display (`/ 5.0`) and proximity formula stay valid — energy proximity still outputs [0, 2.0] because `|song − target| ∈ [0,1]` when both values are in [0,1].

**Before vs After — key ranking changes:**

| Profile | Before | After | What changed |
|---|---|---|---|
| Deep Intense Rock — gap #1→#2 | 4.81 → 2.64 (Δ 2.17) | 4.80 → 3.61 (Δ 1.19) | Gap nearly halved; energy-close songs climb |
| Deep Intense Rock — Fury Road rank | **#4** (1.86) | **#4** (2.81) | Improved score but still stuck without categorical credit |
| Chill Lofi #3 | Focus Flow (lofi/focused, 3.74) | **Spacewalk Thoughts** (ambient/chill, 3.79) | Spacewalk's energy 0.28 beats Focus Flow's 0.40 — energy proximity now outweighs genre match |
| Rare Genre — best possible score | 2.95 | **3.95** | Perfect energy match (+2.00) now partially compensates for the missing genre |
| All-0.5 profile — spread of #2–#5 | 1.78–1.82 (Δ 0.04) | 2.68–2.79 (Δ 0.11) | Three times wider spread; more meaningful differentiation |

**Observations:**

1. **The genre cliff gets shorter but doesn't disappear.** Fury Road (metal) scores 2.81 vs Storm Runner's 4.80 — still a 1.99-point gap, mostly because it still earns zero from both categorical features. Halving genre didn't fix adjacent-genre blindness; it only reduced its cost.

2. **A new artifact appeared in Chill Lofi.** Spacewalk Thoughts (ambient/chill) now beats Focus Flow (lofi/focused) at #3. Focus Flow has the genre match (+1.0) but energy 0.40 is further from the target 0.30 than Spacewalk's 0.28. Under the new weights, energy difference of 0.12 × 2.0 = 0.24 points costs more than a genre match gains (+1.0 for Focus Flow, but Focus Flow also earns +1.0 genre vs +1.0 mood for Spacewalk — the actual flip is driven purely by energy proximity). This feels *correct* — if a user wants low-energy chill, the ambient song at 0.28 is a better match than the lofi song at 0.40.

3. **Edge case 2 (rare genre) improves the most.** Library Rain hits a perfect energy sub-score (+2.00) and jumps from 2.95 to 3.95. The user is still penalized for their absent genre, but less severely — the gap between a rare-genre user and a common-genre user narrows from 2.0 points to 1.0 point.

4. **The experiment confirms energy is the right candidate for increased weight.** Its catalog range (0.28–0.97) is the widest of any numeric feature, so it actually discriminates between songs. Doubling it rewards precision in a feature that meaningfully separates the catalog.

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this

---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
- What information about the user does it use
- How does it turn those into a number

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

```
