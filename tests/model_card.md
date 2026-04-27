# Model Card: Music Recommender Simulation

---

## 1. Model Name
**VibeFinder 1.0**

---

## 2. Goal / Task
Suggest the top 5 songs from a small catalog that best match what a user wants to hear right now. The user tells the system their preferred genre, mood, and a few numeric targets (energy, valence, danceability, acousticness). The system scores every song and returns the closest matches with an explanation.

---

## 3. Data Used
- 18 songs total, 15 different genres, 12 different moods
- Each song has 6 features: genre, mood, energy, valence, danceability, acousticness
- Lofi is the most represented genre (3 songs); pop has 2; every other genre has exactly 1
- Missing entirely: Latin, K-pop, country subgenres, and almost any sad or melancholic music
- Because most genres appear only once, a genre mismatch usually means zero songs of that style are available

---

## 4. Algorithm Summary
Every song starts at 0 points and earns points by matching the user's preferences:

- **Genre match** adds 1 point (the biggest single factor)
- **Mood match** adds 1 point
- **Energy** adds up to 2 points — the closer the song's energy is to the user's target, the more points it earns
- **Valence** adds up to 0.6 points the same way
- **Danceability** adds up to 0.25 points
- **Acousticness** adds up to 0.15 points

The maximum possible score is 5.0. All 18 songs are scored, sorted highest to lowest, and the top 5 are returned with a breakdown showing which features helped each song rank.

---

## 5. Observed Behavior / Biases

**Genre matching is all-or-nothing.** If a song's genre doesn't match exactly, it loses the full genre point — no partial credit. This means a metal song scores worse than an electronic song for a rock fan, even though metal and rock sound nearly identical. The electronic song just happened to share the same mood tag. Users get locked into their exact genre label and miss the closest sonic neighbors.

**A missing genre silently caps your score.** If the user's preferred genre isn't in the catalog at all (like bossa nova), the best possible score drops to 3.95 out of 5.0. The system never tells the user this — it just quietly returns worse results.

**Conflicting preferences produce bad matches with no warning.** A user who wants high energy (0.90) and a sad mood gets poor results because no song in the catalog is both high-energy and sad. The system picks the least-bad option and presents it with the same confidence as a good match.

---

## 6. Evaluation Process

Ran 7 user profiles against the system:

**3 normal profiles** — High-Energy Pop, Chill Lofi, Deep Intense Rock. These represent common, well-defined listener types. Results for pop and lofi felt right immediately. The rock profile revealed the adjacent-genre bug: an electronic song ranked above a metal song, which no human listener would accept.

**4 adversarial profiles** — designed to find edge cases:
- *Conflicting preferences* (sad mood + high energy): system split its loyalty and satisfied neither preference
- *Rare genre* (bossa nova): confirmed the silent score cap at 3.95/5.0
- *All-neutral numerics* (every target set to 0.50): #2 through #5 were almost tied, making the ranking nearly random
- *Acoustic metalhead* (metal + acousticness 1.0): the acousticness target contributed only +0.01 to the winner and was functionally ignored

Also ran a weight-shift experiment: doubled the energy weight (1.0 → 2.0) and halved the genre weight (2.0 → 1.0). MAX_SCORE stayed at 5.0. Cross-genre songs became more competitive but the genre cliff didn't disappear — it just got shorter.

---

## 7. Intended Use and Non-Intended Use

**Intended use:**
- Classroom demonstration of how a rule-based recommender works
- Learning how weights and features affect rankings
- Exploring bias and fairness in a low-stakes setting

**Not intended for:**
- Real music discovery — the catalog is too small (18 songs) to be useful
- Any production environment or real users
- Genres, moods, or listening contexts not represented in songs.csv
- Making decisions about what music "people like" in the real world

---

## 8. Ideas for Improvement
- **Replace binary genre matching with a similarity score.** Rock and metal should share ~80% credit; pop and classical almost none. This would fix the biggest source of bad rankings.
- **Grow the catalog.** With only one song per genre, a single mismatch eliminates an entire style. Even 5 songs per genre would make the system much more useful.
- **Add a conflict detector.** When a user's preferences contradict each other (high energy + sad mood, or acoustic + metal), the system should say so instead of quietly returning a bad match.

---

## 9. Personal Reflection

**Biggest learning moment:** The genre cliff. I assumed the weights would produce gradual differences between songs, but halving the genre weight still left a nearly 2-point gap between a rock song and a metal song for a rock fan. The math is simple — it's just subtraction — but the effect on real users would be significant and easy to miss without testing.

**Using AI tools:** They were useful for generating adversarial profiles I wouldn't have thought to write myself, like the "acoustic metalhead" case. I had to double-check the weight-shift math manually because the agent updated a comment but I needed to verify MAX_SCORE still summed to 5.0 before trusting the output.

**What surprised me:** A system this simple — six features, fixed weights, no learning — still produces results that feel reasonable most of the time. Pop fans and lofi fans both got sensible top-5 lists. That's what makes bias hard to spot: the system looks like it's working until you test an edge case.

**What I'd try next:** I'd add a genre similarity table so rock and metal share partial credit instead of being treated as opposites. That one change would fix the most noticeable failure in the current system without touching anything else.
