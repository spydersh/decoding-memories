# Phase 3: extended analyses (computed; nothing hard-coded)
Reviews: 6042; sentences scored with VADER: 49909. Core comparison: 4 ryokans vs 3 hotels.
With 4 vs 3 properties there are only 35 possible assignments, so the smallest exact p is 1/35 = .029; 'complete separation' (every ryokan beyond every hotel) is the strongest result possible.

## 1. Business KPIs by property (top-box, low-box, net rating score)
|                                          |        n |   mean |   top_box |   low_box |   median_words |   net_score |
|:-----------------------------------------|---------:|-------:|----------:|----------:|---------------:|------------:|
| ('Hotel', 'Four Seasons Hotl Kyoto')     |  739.000 |  4.612 |     0.800 |     0.107 |         80.000 |       0.693 |
| ('Hotel', 'Hyatt Regency Kyoto')         | 2521.000 |  4.509 |     0.658 |     0.099 |         91.000 |       0.559 |
| ('Hotel', 'Parkhyatt')                   |  370.000 |  4.597 |     0.830 |     0.114 |         75.500 |       0.716 |
| ('Hybrid', 'Junei Hotel Kyoto')          |  116.000 |  4.828 |     0.888 |     0.034 |         75.000 |       0.853 |
| ('Hybrid', 'Nazuna Kyoto Gosho')         |  165.000 |  4.927 |     0.939 |     0.006 |         62.000 |       0.933 |
| ('Hybrid', 'Nazuna Kyoto Nijojo')        |  173.000 |  4.873 |     0.936 |     0.029 |         61.000 |       0.908 |
| ('Ryokan', 'Kyokoyado Muromachi Yutone') |  181.000 |  4.967 |     0.967 |     0.000 |         67.000 |       0.967 |
| ('Ryokan', 'Nishiyama Ryokan')           |  565.000 |  4.602 |     0.713 |     0.067 |         74.000 |       0.646 |
| ('Ryokan', 'Ryokufuso')                  |  431.000 |  4.661 |     0.726 |     0.053 |         68.000 |       0.673 |
| ('Ryokan', 'Shiraume')                   |  781.000 |  4.985 |     0.986 |     0.001 |        122.000 |       0.985 |
- Rating: Ryokan 4.804 vs Hotel 4.572 (property means), gap +0.231, exact p = 0.171, separation: overlap
- top: Ryokan 0.848 vs Hotel 0.762 (property means), gap +0.086, exact p = 0.429, separation: overlap
- low: Ryokan 0.030 vs Hotel 0.107 (property means), gap -0.076, exact p = 0.057, separation: complete

## 2. Review length and rating (negativity elaboration)
|   Rating |        n |   median |    mean |
|---------:|---------:|---------:|--------:|
|        1 |   79.000 |  155.000 | 197.772 |
|        2 |  112.000 |  121.500 | 159.973 |
|        3 |  252.000 |  128.500 | 174.825 |
|        4 |  962.000 |  100.500 | 131.332 |
|        5 | 4637.000 |   80.000 | 115.699 |
- Spearman rating vs words: rho = -0.142 (p = 1.5e-28)
- within property, reviews rated <=3 are +46% longer (log-words model, property fixed effects)

## 3. Rating-text congruence (how well lexicon sentiment tracks stars)
- s_mean: Spearman with rating = 0.407; AUC for detecting <=3-star reviews = 0.908
- textblob: Spearman with rating = 0.409; AUC for detecting <=3-star reviews = 0.896
- s_min: Spearman with rating = 0.347; AUC for detecting <=3-star reviews = 0.840
- incongruent cases: 5-star with negative mean sentiment 0.2%; 1-2 star with clearly positive mean sentiment 0.2% of all reviews

## 4. Distinctive vocabulary: property-balanced keyness (Ryokan vs Hotel)
- terms kept after removing property-specific vocabulary: 1877 of 2166
**Most ryokan-distinctive (share of reviews using the term, averaged across properties)**
|                        |   ryokan_rate |   hotel_rate |   log_ratio | separated   |
|:-----------------------|--------------:|-------------:|------------:|:------------|
| dinner breakfast       |         0.093 |        0.003 |       3.258 | R>H all     |
| tatami                 |         0.082 |        0.003 |       3.116 | R>H all     |
| wear                   |         0.037 |        0.001 |       2.882 | R>H all     |
| traditional dinner     |         0.016 |        0.000 |       2.804 | R>H all     |
| experience traditional |         0.025 |        0.001 |       2.784 | R>H all     |
| mats                   |         0.033 |        0.001 |       2.769 | R>H all     |
| tatami mats            |         0.028 |        0.001 |       2.676 | R>H all     |
| yukata                 |         0.047 |        0.003 |       2.616 | R>H all     |
| authentic experience   |         0.019 |        0.001 |       2.344 | R>H all     |
| kaiseki                |         0.131 |        0.012 |       2.327 | R>H all     |
| baths                  |         0.054 |        0.004 |       2.313 | R>H all     |
| fridge                 |         0.013 |        0.001 |       2.221 | R>H all     |
| hot bath               |         0.016 |        0.001 |       2.215 | R>H all     |
| recommend place        |         0.026 |        0.002 |       2.103 | R>H all     |
| tatami room            |         0.013 |        0.001 |       2.088 | R>H all     |
| traditional breakfast  |         0.044 |        0.005 |       1.990 | R>H all     |
| wearing                |         0.015 |        0.001 |       1.927 | R>H all     |
| kimonos                |         0.018 |        0.002 |       1.922 | R>H all     |
| authentic              |         0.061 |        0.009 |       1.863 | R>H all     |
| traditional            |         0.317 |        0.052 |       1.790 | R>H all     |
**Most hotel-distinctive**
|                   |   ryokan_rate |   hotel_rate |   log_ratio | separated   |
|:------------------|--------------:|-------------:|------------:|:------------|
| buffet            |         0.000 |        0.111 |      -4.721 | H>R all     |
| breakfast buffet  |         0.000 |        0.062 |      -4.140 | H>R all     |
| gym               |         0.000 |        0.054 |      -4.011 | H>R all     |
| housekeeping      |         0.000 |        0.043 |      -3.517 | H>R all     |
| concierge         |         0.005 |        0.169 |      -3.424 | H>R all     |
| champagne         |         0.001 |        0.033 |      -3.040 | H>R all     |
| concierge service |         0.000 |        0.016 |      -2.861 | H>R all     |
| buffet breakfast  |         0.000 |        0.015 |      -2.760 | H>R all     |
| concierge staff   |         0.000 |        0.015 |      -2.742 | H>R all     |
| view room         |         0.001 |        0.024 |      -2.740 | H>R all     |
| cocktails         |         0.000 |        0.018 |      -2.662 | H>R all     |
| design            |         0.006 |        0.087 |      -2.578 | H>R all     |
| properties        |         0.002 |        0.029 |      -2.452 | H>R all     |
| cocktail          |         0.000 |        0.010 |      -2.442 | H>R all     |
| bar               |         0.011 |        0.130 |      -2.407 | H>R all     |
| upgraded          |         0.002 |        0.035 |      -2.403 | H>R all     |
| carte             |         0.000 |        0.009 |      -2.268 | H>R all     |
| ritz              |         0.002 |        0.026 |      -2.234 | H>R all     |
| chain             |         0.001 |        0.018 |      -2.206 | H>R all     |
| la carte          |         0.000 |        0.007 |      -2.140 | H>R all     |

## 5. Aspect salience (what guests narrate) and aspect sentiment, by type
| aspect        |   salience_R |   salience_H | sal_sep   |   sentiment_R |   sentiment_H | sent_sep   |   neg_share_R |   neg_share_H | neg_sep   |   salience_hybrid |
|:--------------|-------------:|-------------:|:----------|--------------:|--------------:|:-----------|--------------:|--------------:|:----------|------------------:|
| dining        |        0.753 |        0.635 | overlap   |         0.522 |         0.456 | overlap    |         0.022 |         0.069 | complete  |             0.663 |
| bath          |        0.471 |        0.236 | overlap   |         0.502 |         0.418 | overlap    |         0.030 |         0.108 | overlap   |             0.410 |
| room          |        0.766 |        0.725 | overlap   |         0.495 |         0.466 | overlap    |         0.023 |         0.049 | complete  |             0.753 |
| staff_service |        0.874 |        0.860 | overlap   |         0.626 |         0.501 | complete   |         0.012 |         0.048 | complete  |             0.877 |
| location      |        0.543 |        0.584 | overlap   |         0.433 |         0.385 | overlap    |         0.048 |         0.058 | overlap   |             0.313 |
| value_price   |        0.213 |        0.258 | overlap   |         0.395 |         0.321 | complete   |         0.054 |         0.116 | overlap   |             0.099 |
| culture       |        0.585 |        0.347 | complete  |         0.518 |         0.498 | overlap    |         0.013 |         0.034 | complete  |             0.441 |
- salience = share of reviews mentioning the aspect; sentiment = mean VADER of those sentences; neg_share = share of mentions that are negative. All averaged across properties.

## 6. Asymmetric impact (three-factor theory, penalty-reward contrast)
Rating ~ positive and negative mentions of each aspect + log length + property fixed effects (OLS, HC3).
Reward = effect of a positive mention; penalty = effect of a negative mention. Test: reward - |penalty| = 0.

**Ryokan** (n = 1958, adj R2 = 0.295)
| aspect        |   reward |   p_reward |   penalty |   p_penalty |   n_pos |   n_neg | factor                                   |
|:--------------|---------:|-----------:|----------:|------------:|--------:|--------:|:-----------------------------------------|
| dining        |    0.008 |      0.773 |    -0.500 |       0.002 |    1324 |      32 | basic (penalty > reward)                 |
| bath          |    0.054 |      0.023 |    -0.119 |       0.486 |     731 |      23 | performance (symmetric) [few negatives]  |
| room          |    0.013 |      0.561 |    -0.689 |       0.001 |    1287 |      37 | basic (penalty > reward)                 |
| staff_service |    0.176 |      0.000 |    -0.754 |       0.003 |    1633 |      24 | basic (penalty > reward) [few negatives] |
| location      |    0.003 |      0.910 |     0.033 |       0.731 |     905 |      44 | performance (symmetric)                  |
| value_price   |   -0.123 |      0.000 |    -0.680 |       0.004 |     375 |      30 | basic (penalty > reward)                 |
| culture       |    0.077 |      0.000 |     0.062 |       0.734 |     961 |      16 | performance (symmetric) [few negatives]  |

**Hotel** (n = 3630, adj R2 = 0.274)
| aspect        |   reward |   p_reward |   penalty |   p_penalty |   n_pos |   n_neg | factor                   |
|:--------------|---------:|-----------:|----------:|------------:|--------:|--------:|:-------------------------|
| dining        |    0.173 |      0.000 |    -0.383 |       0.000 |    2007 |     174 | basic (penalty > reward) |
| bath          |    0.142 |      0.000 |    -0.270 |       0.038 |     606 |      74 | performance (symmetric)  |
| room          |    0.076 |      0.012 |    -0.720 |       0.000 |    2359 |     163 | basic (penalty > reward) |
| staff_service |    0.270 |      0.000 |    -0.751 |       0.000 |    2779 |     133 | basic (penalty > reward) |
| location      |    0.087 |      0.001 |    -0.216 |       0.012 |    1745 |     152 | performance (symmetric)  |
| value_price   |   -0.106 |      0.003 |    -0.402 |       0.000 |     756 |     121 | basic (penalty > reward) |
| culture       |    0.198 |      0.000 |     0.042 |       0.789 |     930 |      42 | performance (symmetric)  |

**Pooled core** (n = 5588, adj R2 = 0.289)
| aspect        |   reward |   p_reward |   penalty |   p_penalty |   n_pos |   n_neg | factor                   |
|:--------------|---------:|-----------:|----------:|------------:|--------:|--------:|:-------------------------|
| dining        |    0.125 |      0.000 |    -0.424 |       0.000 |    3331 |     206 | basic (penalty > reward) |
| bath          |    0.102 |      0.000 |    -0.236 |       0.029 |    1337 |      97 | performance (symmetric)  |
| room          |    0.058 |      0.006 |    -0.726 |       0.000 |    3646 |     200 | basic (penalty > reward) |
| staff_service |    0.242 |      0.000 |    -0.772 |       0.000 |    4412 |     157 | basic (penalty > reward) |
| location      |    0.058 |      0.002 |    -0.173 |       0.014 |    2650 |     196 | performance (symmetric)  |
| value_price   |   -0.103 |      0.000 |    -0.466 |       0.000 |    1131 |     151 | basic (penalty > reward) |
| culture       |    0.145 |      0.000 |     0.049 |       0.689 |    1891 |      58 | performance (symmetric)  |

## 7. Importance-performance analysis (impact-range importance; Martilla & James quadrants)

**Ryokan**
| aspect        |   importance |   performance | quadrant              |
|:--------------|-------------:|--------------:|:----------------------|
| staff_service |        0.930 |         0.938 | Keep up the good work |
| room          |        0.702 |         0.873 | Keep up the good work |
| value_price   |        0.680 |         0.798 | Concentrate here      |
| dining        |        0.508 |         0.888 | Keep up the good work |
| bath          |        0.173 |         0.830 | Low priority          |
| culture       |        0.077 |         0.861 | Possible overkill     |
| location      |        0.003 |         0.804 | Low priority          |

**Hotel**
| aspect        |   importance |   performance | quadrant              |
|:--------------|-------------:|--------------:|:----------------------|
| staff_service |        1.020 |         0.886 | Keep up the good work |
| room          |        0.796 |         0.848 | Keep up the good work |
| dining        |        0.556 |         0.825 | Keep up the good work |
| bath          |        0.412 |         0.767 | Low priority          |
| value_price   |        0.402 |         0.711 | Low priority          |
| location      |        0.303 |         0.751 | Low priority          |
| culture       |        0.198 |         0.805 | Possible overkill     |

## 8. Peak-end test: do the most intense and the final sentences explain the rating beyond the average?
- M1 mean only: adj R2 = 0.299
- M2 peak-end only: adj R2 = 0.218
- M3 mean + min + max + first + last: adj R2 = 0.305
  - s_mean: +0.381 stars per SD (95% CI +0.334, +0.428)
  - s_min: -0.018 stars per SD (95% CI -0.049, +0.014)
  - s_max: +0.066 stars per SD (95% CI +0.031, +0.101)
  - s_first: -0.020 stars per SD (95% CI -0.043, +0.003)
  - s_last: -0.027 stars per SD (95% CI -0.050, -0.005)
- n = 5335 reviews with >= 3 sentences. Note: 'last' = end of the written narrative, not of the stay.

## 9. Behavioural and memory proxies (explicit return intent, recommendation, memory words)
|   Rating |   ('ret', 'Hotel') |   ('ret', 'Ryokan') |   ('rec', 'Hotel') |   ('rec', 'Ryokan') |   ('mem', 'Hotel') |   ('mem', 'Ryokan') |
|---------:|-------------------:|--------------------:|-------------------:|--------------------:|-------------------:|--------------------:|
|        1 |              0.044 |               0.000 |              0.088 |               0.111 |              0.029 |               0.000 |
|        2 |              0.053 |               0.000 |              0.064 |               0.000 |              0.000 |               0.000 |
|        3 |              0.081 |               0.000 |              0.120 |               0.024 |              0.019 |               0.000 |
|        4 |              0.095 |               0.060 |              0.168 |               0.255 |              0.011 |               0.017 |
|        5 |              0.135 |               0.169 |              0.233 |               0.314 |              0.058 |               0.144 |
- ret: Ryokan 0.150 vs Hotel 0.121, gap +0.030, exact p = 0.286, separation: overlap
- rec: Ryokan 0.302 vs Hotel 0.203, gap +0.099, exact p = 0.029, separation: complete
- mem: Ryokan 0.096 vs Hotel 0.072, gap +0.024, exact p = 0.914, separation: overlap

**Which aspects are associated with each proxy beyond the star rating?** (logit, odds ratios; controls: rating, log length, property)
|                   | return_intent_OR   | recommend_OR   | memory_words_OR   |
|:------------------|:-------------------|:---------------|:------------------|
| pos_dining        | 1.04               | 1.21*          | 0.85              |
| neg_dining        | 1.07               | 0.80           | 0.35              |
| pos_bath          | 1.17               | 1.05           | 0.80              |
| neg_bath          | 0.71               | 0.54*          | 0.85              |
| pos_room          | 1.08               | 0.87           | 0.64*             |
| neg_room          | 0.93               | 0.82           | 0.62              |
| pos_staff_service | 1.10               | 1.37*          | 1.51*             |
| neg_staff_service | 0.78               | 1.14           | 2.18              |
| pos_location      | 1.02               | 1.07           | 0.73*             |
| neg_location      | 1.04               | 0.81           | 0.58              |
| pos_value_price   | 0.74*              | 0.97           | 0.76              |
| neg_value_price   | 0.80               | 1.13           | 0.86              |
| pos_culture       | 0.86               | 1.12           | 1.14              |
| neg_culture       | 1.14               | 1.00           | 0.57              |
- * p < .05. OR > 1 = the aspect mention raises the odds of the proxy at the same star rating.

## 10. Dissatisfaction early-warning model (text -> rating <= 3)
- 5-fold cross-validated AUC (text model): 0.959
- baseline AUC (VADER mean sentiment only): 0.908
- leave-one-property-out AUC (generalises to an unseen property): 0.942
- strongest dissatisfaction signals: poor, disappointed, disappointing, basic, average, small, price, worst, better, said, bad, didn, paid, unfortunately, room, rooms small, disappointment, told, like, asked, expensive, dirty, overpriced, limited, new

## 11. Long-run trend by type (rating ~ year x type + property fixed effects)
- Hotel: +0.014 stars per decade (95% CI -0.061, +0.089)
- Ryokan: +0.244 stars per decade (95% CI +0.194, +0.294)

Done. Review-level features saved to phase3_review_features.csv.