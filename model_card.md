# 🎧 Model Card: Music Recommender Simulation

---

## 1. Model Name

**VibeMatch 1.0**

---

## 2. Goal / Task

VibeMatch looks at a user's taste preferences and picks the songs from a small catalog
that are the closest match. It does not learn over time. It does not remember past
sessions. It just takes your preferences, scores every song once, and hands you the
top results. Think of it as a very opinionated friend who has heard all 18 songs and
ranks them for you based on rules you set in advance.

---

## 3. Algorithm Summary

Every song gets a score out of 10. The score is built from seven ingredients:

- **Genre** — does the song's genre match what you asked for? If yes, +1.5 points.
  If no, zero. No partial credit.
- **Mood** — same idea. Does the mood label match? Yes = +1.5, no = 0.
- **Energy** — how close is the song's energy level to your target?
  A perfect match earns the full 3.5 points. The further away it is, the fewer points
  it earns. This is the most heavily weighted feature.
- **Valence** — how close is the song's positivity/happiness level to your target?
  Worth up to 1.5 points.
- **Acousticness** — how close is the song's acoustic texture to what you prefer?
  Worth up to 1.0 points.
- **Tempo** — how close is the BPM to your target tempo? Worth up to 0.5 points.
- **Danceability** — how close is the rhythm feel to your target? Worth up to 0.5 points.

All seven scores are added together. Songs are then sorted from highest to lowest.
The top 5 results are your recommendations.

---

## 4. Data

The catalog has 18 songs. The original starter dataset had 10 songs — 8 more were
added to improve genre diversity. Songs span 15 genres including pop, lofi, rock,
metal, classical, jazz, soul, hip-hop, folk, r&b, edm, ambient, synthwave, latin,
and indie pop. Moods covered include happy, chill, intense, relaxed, focused, moody,
hype, melancholic, romantic, angry, nostalgic, euphoric, sad, and uplifting.

Each song has 7 numeric features (energy, tempo, valence, danceability, acousticness,
and two categorical labels (genre, mood). There are no lyrics, no artist popularity
scores, and no listen counts. The dataset was hand-crafted for this project — it does
not represent any real platform's catalog or user behavior. Western popular music
genres dominate. Classical and jazz are represented by one song each. Non-Western
genres are almost entirely absent.

---

## 5. Strengths

The system works best when the user's preferred genre is well-represented in the
catalog. A lofi listener gets genuinely good results — the three lofi songs all rank
near the top, sorted correctly by how closely each one matches the numeric preferences.

The system is fully transparent. Every recommendation comes with a breakdown showing
exactly how many points each feature contributed. You can see at a glance why a song
ranked where it did, which is something most real music apps do not offer.

The system handles missing genres gracefully. When tested with a k-pop preference
(a genre not in the catalog), it still surfaced reasonable results by falling back on
mood and numeric proximity. The top two results were bright, high-energy songs that a
k-pop listener would plausibly enjoy.

The scoring is fast and simple. Because it is just arithmetic — no machine learning,
no training data — it runs instantly on any machine and is easy to modify.

---

## 6. Limitations and Bias

**The single-song genre trap is the most critical bias in the system.**
13 of the 15 genres have exactly one song. When a user picks one of those genres,
that one song almost always wins no matter what — even if it sounds nothing like what
the user actually wants. A folk fan who wants intense, high-energy music still gets
Porch and Fireflies, a slow nostalgic song, because it is the only folk song available.
Lofi listeners are served three times better than everyone else simply because lofi has
three catalog entries.

**The energy gap is measured symmetrically, but music is not symmetric.**
The formula treats being "too slow" and "too fast" as equally bad. In practice, a
workout user who gets a slow sad song is far more disappointed than one who gets a
song that is slightly too fast. The scoring cannot capture that difference.

**Mood is all-or-nothing with no sense of closeness.**
"Sad" and "melancholic" score the same as "sad" and "hype" — both return zero points.
But those two are clearly more similar than the second pair. The system has no way to
express that some moods are neighbors and others are opposites.

**Mid-energy songs crowd the results for unrelated profiles.**
Songs with energy around 0.4–0.6 are never far from any user's target, so they slip
into the top 5 for profiles they have no real connection to. When tested with a fully
neutral user profile, the top 5 results were clustered within 0.24 points of each
other — essentially a tie the system resolved arbitrarily.

---

## 7. Evaluation

Seven user profiles were tested. Three were designed to match the catalog well:
a High-Energy Pop listener, a Chill Lofi listener, and a Deep Intense Rock listener.
Four were adversarial — designed to find weaknesses: a Sad Banger (high energy + sad
mood), a Ghost Genre user (k-pop, not in catalog), an All Neutral user (no preferences
at all), and an Acoustic but Intense user (wanted acoustic texture AND high energy).

The clean profiles worked as expected. Lofi got lofi. Rock got rock. The scores were
high and the ranking felt right.

The Acoustic but Intense profile broke the system. Porch and Fireflies — a gentle folk
song — ranked first for someone who wanted intense, aggressive music. The genre bonus
overruled every other signal. After shifting the weights (genre from 3.0 down to 1.5,
energy from 2.0 up to 3.5), Storm Runner correctly took the top spot. That one weight
change fixed the most counterintuitive result in the entire evaluation.

Gym Hero kept appearing in the top 3 for a Happy Pop user even though it is labeled
"intense" not "happy." The reason: it matches genre and nearly matches energy, earning
nearly 5 out of 5 possible points on those two features. The missing mood points were
not enough to push it out. In plain terms — the system knows Gym Hero sounds like pop
and has the right energy, so it keeps recommending it. It just cannot tell that "intense"
and "happy" feel completely different to a real person.

The all-neutral profile showed that without real preferences, the system is essentially
guessing. All 18 songs scored within a quarter point of each other.

---

## 8. Intended Use and Non-Intended Use

**Intended use:**
This system is built for a classroom exercise. Its purpose is to demonstrate how a
content-based recommender works — how features become numbers, how numbers become
scores, and how scores become a ranked list. It is a learning tool, not a product.

**Not intended for:**
- Real users making real music decisions
- Any catalog larger than a few dozen songs without adding more features
- Personalization over time — it has no memory and does not learn
- Replacing human curation or taste judgment
- Any context where genre or cultural representation matters, since the dataset
  is small, Western-leaning, and hand-crafted

---

## 9. Ideas for Improvement

**1. Replace the genre binary with a genre similarity score.**
Instead of match/no-match, create a small table of genre distances — lofi and ambient
are close, lofi and metal are far. A song one genre away from the user's preference
would earn partial points instead of zero. This would eliminate the single-song genre
trap and make cross-genre discovery possible.

**2. Add mood groupings.**
Cluster similar moods together (sad/melancholic/moody as one group, intense/angry/hype
as another). A song in the same cluster as the user's preferred mood earns half points
instead of zero. This would make the mood feature useful for more than exact-label users.

**3. Enforce diversity in the top k results.**
The current system can return 5 songs from the same genre if they all score similarly.
A diversity rule — no more than 2 songs from the same genre in the top 5 — would force
the system to show users music they might not have considered, which is closer to how
real recommenders try to balance exploitation (give you what you like) with exploration
(show you something new).
