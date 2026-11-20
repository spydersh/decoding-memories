## A. Classification used (three tiers)
|                                          |    n |   rating |   share5 |   textblob |   first_year |
|:-----------------------------------------|-----:|---------:|---------:|-----------:|-------------:|
| ('Hotel', 'Four Seasons Hotl Kyoto')     |  739 |    4.612 |    0.8   |      0.357 |         2016 |
| ('Hotel', 'Hyatt Regency Kyoto')         | 2521 |    4.509 |    0.658 |      0.304 |         2006 |
| ('Hotel', 'Parkhyatt')                   |  370 |    4.597 |    0.83  |      0.345 |         2019 |
| ('Hybrid', 'Junei Hotel Kyoto')          |  116 |    4.828 |    0.888 |      0.362 |         2022 |
| ('Hybrid', 'Nazuna Kyoto Gosho')         |  165 |    4.927 |    0.939 |      0.371 |         2019 |
| ('Hybrid', 'Nazuna Kyoto Nijojo')        |  173 |    4.873 |    0.936 |      0.382 |         2016 |
| ('Ryokan', 'Kyokoyado Muromachi Yutone') |  181 |    4.967 |    0.967 |      0.37  |         2017 |
| ('Ryokan', 'Nishiyama Ryokan')           |  565 |    4.602 |    0.713 |      0.305 |         2005 |
| ('Ryokan', 'Ryokufuso')                  |  431 |    4.661 |    0.726 |      0.318 |         2008 |
| ('Ryokan', 'Shiraume')                   |  781 |    4.985 |    0.986 |      0.357 |         2008 |

## B. Ryokan (4) vs Hotel (3): ratings and TextBlob sentiment at the PROPERTY level
- Rating: Ryokan 4.804 vs Hotel 4.572; gap +0.231; exact permutation p = 0.171 (35 assignments); Welch on property means t = 2.20
- five: Ryokan 0.848 vs Hotel 0.762; gap +0.086; exact permutation p = 0.429 (35 assignments); Welch on property means t = 0.94
- tb: Ryokan 0.338 vs Hotel 0.335; gap +0.002; exact permutation p = 0.943 (35 assignments); Welch on property means t = 0.10
- Return_Intent: Ryokan 0.308 vs Hotel 0.316; gap -0.008; exact permutation p = 0.943 (35 assignments); Welch on property means t = -0.15
- review-level (for comparison only; ignores clustering): d = 0.365, n = 1958 vs 3630
- hybrid properties (not in the comparison): {'Junei Hotel Kyoto': 4.828, 'Nazuna Kyoto Gosho': 4.927, 'Nazuna Kyoto Nijojo': 4.873}
- mixed model, era-adjusted: Ryokan effect +0.238 stars (SE 0.113); only 7 clusters, so the p-value is optimistic
- leave-one-property-out (property-level gap in mean rating):
  - without Shiraume: +0.171
  - without Parkhyatt: +0.244
  - without Four Seasons Hotl Kyoto: +0.251
  - without Hyatt Regency Kyoto: +0.199
  - without Kyokoyado Muromachi Yutone: +0.177
  - without Nishiyama Ryokan: +0.298
  - without Ryokufuso: +0.279
- excluding 15 likely non-English reviews: gap +0.232, p = 0.171
- reviews <=2019 only (review-level means shown because some properties have very few reviews): Ryokan 4.710 vs Hotel 4.529
- reviews 2023+ only (review-level means shown because some properties have very few reviews): Ryokan 4.965 vs Hotel 4.540

## C. Topic model rebuilt (lemmatised, names removed, k chosen by coherence)
- property-specific terms removed: 344 (e.g. acceptable, action, adequate, adjacent, airport, albeit, alex, alternative, american, aren, asian, attraction, attractive, average, avoid, baian, bakery, bamboo, bar, bartender, basement, bell, benefit, bistro, black, bottle, brasserie, bread, bridge, bright)
|   k |   c_v coherence |
|----:|----------------:|
|   4 |           0.442 |
|   5 |           0.465 |
|   6 |           0.468 |
|   8 |           0.471 |
- highest coherence 0.471; smallest k within 0.01 of it: k = 5 (chosen for parsimony; check interpretability)
- topic 0: great, helpful, service, recommend, breakfast, location, excellent, friendly, nice, clean, food, experience
- topic 1: walk, location, area, locate, garden, great, nice, city, quiet, excellent, breakfast, service
- topic 2: experience, make, amaze, beautiful, best, dinner, service, wonderful, time, place, feel, trip
- topic 3: bath, breakfast, traditional, tea, night, dinner, bed, bathroom, day, small, experience, floor
- topic 4: service, time, night, breakfast, day, check, make, like, book, say, price, ask
- stability: mean best-match Jaccard of top-10 words across 4 reseeded runs = 0.55
- property leakage (normalised mutual information, dominant topic vs property): July topics = 0.263; rebuilt topics = 0.124
- mean topic share by tier (rows = topics):
|    |   Hotel |   Hybrid |   Ryokan |
|:---|--------:|---------:|---------:|
| t0 |   0.241 |    0.28  |    0.235 |
| t1 |   0.199 |    0.09  |    0.103 |
| t2 |   0.18  |    0.328 |    0.323 |
| t3 |   0.088 |    0.223 |    0.249 |
| t4 |   0.292 |    0.079 |    0.091 |

## D. Aspect association: does the Ryokan effect shrink once topic content is controlled?
- Ryokan effect without topics: +0.238; with topic shares: -0.055; attenuation = 123%
- topic coefficients (reference = topic 0): t1: -0.29, t2: +0.16, t3: -0.41, t4: -1.66

## E. Seasonality: type x peak interaction with equivalence margins (margin = 0.2 SD of the outcome)
- Rating: hotel peak effect -0.075 (95% CI -0.126, -0.024); interaction +0.080 (90% CI +0.007, +0.153) vs margin +/-0.155 -> equivalent (90% CI inside margin)
- tb: hotel peak effect -0.007 (95% CI -0.018, +0.004); interaction +0.012 (90% CI -0.004, +0.027) vs margin +/-0.032 -> equivalent (90% CI inside margin)
- peak = Apr+Nov, Rating: hotel peak effect -0.102 (95% CI -0.165, -0.039); interaction +0.097 (90% CI +0.008, +0.185) vs margin +/-0.155 -> difference
- 2023+ only, Rating: hotel peak effect -0.144 (95% CI -0.250, -0.038); interaction +0.146 (90% CI +0.011, +0.281) vs margin +/-0.163 -> difference
- 2023+ only, tb: hotel peak effect -0.013 (95% CI -0.036, +0.009); interaction +0.013 (90% CI -0.016, +0.042) vs margin +/-0.034 -> inconclusive
|               |   size |   mean |
|:--------------|-------:|-------:|
| ('Hotel', 0)  |   2330 |  4.566 |
| ('Hotel', 1)  |   1300 |  4.49  |
| ('Ryokan', 0) |   1234 |  4.797 |
| ('Ryokan', 1) |    724 |  4.809 |
- note: month = REVIEW posting month. A stay-date field is needed for a clean seasonality test.

## F. Explicit-mention proxies (keyword based, to be validated on a hand-checked sample)
- July flags: Memorable 20.8%, Return_Intent 31.6% (the Memorable flag counts the word 'special'; Return_Intent counts any 'again')
- strict flags: explicit memory words 7.5%, explicit return intent 14.3%
- mem_strict: Ryokan 0.096 vs Hotel 0.072; property-level gap +0.024, permutation p = 0.914
- ret_strict: Ryokan 0.158 vs Hotel 0.130; property-level gap +0.028, permutation p = 0.343