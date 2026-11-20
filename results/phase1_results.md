## 1. Audit
- reviews: 6042; properties: 10; date range: 2005-04-13 to 2026-02-03
- missing text: 0; exact duplicate texts: 0
- likely non-English (>30% non-ASCII): 16
- reviews up to 2019: 3856 (64%)

|                                          |    n |   mean |    sd |   share5 |   first_year |
|:-----------------------------------------|-----:|-------:|------:|---------:|-------------:|
| ('Boutique', 'The_Junei_Hotel')          |  116 |  4.828 | 0.564 |    0.888 |         2022 |
| ('Hotel', 'Four_Seasons_Hotel_Kyoto')    |  739 |  4.612 | 0.913 |    0.8   |         2016 |
| ('Hotel', 'Hyatt_Regency_Kyoto')         | 2521 |  4.509 | 0.821 |    0.658 |         2006 |
| ('Hotel', 'Park_Hyatt_Kyoto')            |  370 |  4.597 | 1.013 |    0.83  |         2019 |
| ('Ryokan', 'Kyokoyado_Muromachi_Yutone') |  181 |  4.967 | 0.18  |    0.967 |         2017 |
| ('Ryokan', 'NISHIYAMA_RYOKAN')           |  565 |  4.602 | 0.762 |    0.713 |         2005 |
| ('Ryokan', 'Nazuna_Kyoto_Gosho')         |  165 |  4.927 | 0.323 |    0.939 |         2019 |
| ('Ryokan', 'Nazuna_Kyoto_Nijojo')        |  173 |  4.873 | 0.577 |    0.936 |         2016 |
| ('Ryokan', 'Ryokufuso')                  |  431 |  4.661 | 0.619 |    0.726 |         2008 |
| ('Ryokan', 'Shiraume')                   |  781 |  4.985 | 0.133 |    0.986 |         2008 |

## 2. Review-level comparison (reproduces July Table 5)
- Ryokan 4.816 (n=2296) vs Hotel 4.539 (n=3630); Welch t=15.29; d=0.387

## 3. Property-level inference (property is the unit that matters)
- all 9 properties: gap = +0.263 stars, exact permutation p = 0.060 (84 assignments)
- excluding Nazuna: gap = +0.231 stars, exact permutation p = 0.171 (35 assignments)
- reviews 2023+: gap = +0.373 stars, exact permutation p = 0.012 (84 assignments)
- reviews <=2019: gap = +0.545 stars, exact permutation p = 0.048 (84 assignments)
- mixed model (all 9, era-adjusted): type effect +0.259, SE 0.093 (few clusters: treat the p-value as optimistic)
- mixed model (no Nazuna, era-adjusted): type effect +0.238, SE 0.113 (few clusters: treat the p-value as optimistic)

## 4. Seasonality (peak = Mar-Apr, Oct-Nov by REVIEW month)
|               |   size |   mean |
|:--------------|-------:|-------:|
| ('Hotel', 0)  |   2330 |  4.566 |
| ('Hotel', 1)  |   1300 |  4.49  |
| ('Ryokan', 0) |   1441 |  4.815 |
| ('Ryokan', 1) |    855 |  4.818 |
- hotel peak effect: -0.075 (95% CI -0.125, -0.024)
- ryokan x peak interaction: +0.071 (95% CI -0.010, +0.152)
- VADER baseline (NOT BERT): interaction +0.013 (95% CI -0.017, +0.042)