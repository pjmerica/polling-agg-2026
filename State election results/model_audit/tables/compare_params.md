### Tune-cycle CV (1998-2016 leave-one-cycle-out; the tuner picks the higher AUC)

| Settings | AUC | Brier |
|---|---|---|
| depth1 (shipped before) | 0.9519 | 0.0873 |
| depth2 (picked by the retune) | 0.9522 | 0.0876 |

### Honest eval 2018-2024 (expanding window, all offices)

| Settings | Brier | Log loss | AUC | Races called right |
|---|---|---|---|---|
| depth1 (shipped before) | 0.0634 | 0.2053 | 0.9735 | 0.880 |
| depth2 (picked by the retune) | 0.0635 | 0.2094 | 0.9742 | 0.879 |
| average of the two | 0.0632 | 0.2066 | 0.9740 | 0.880 |

### Per cycle, Brier

| Settings | 2018 | 2020 | 2022 | 2024 |
|---|---|---|---|---|
| depth1 (shipped before) | 0.0567 | 0.0797 | 0.0636 | 0.0559 |
| depth2 (picked by the retune) | 0.0586 | 0.0757 | 0.0644 | 0.0566 |
| average of the two | 0.0574 | 0.0774 | 0.0637 | 0.0560 |

### House, 1-3 polls, leading by 0-5 points

| Settings | Candidates | Mean predicted | Actually won | Brier |
|---|---|---|---|---|
| depth1 (shipped before) | 107 | 0.681 | 0.701 | 0.1669 |
| depth2 (picked by the retune) | 107 | 0.658 | 0.701 | 0.1681 |
| average of the two | 107 | 0.669 | 0.701 | 0.1669 |

### House, 1-3 polls, trailing by 0-5 points

| Settings | Candidates | Mean predicted | Actually won | Brier |
|---|---|---|---|---|
| depth1 (shipped before) | 107 | 0.295 | 0.299 | 0.1632 |
| depth2 (picked by the retune) | 107 | 0.331 | 0.299 | 0.1624 |
| average of the two | 107 | 0.313 | 0.299 | 0.1620 |

### House, 4+ polls, leading by 0-5 points

| Settings | Candidates | Mean predicted | Actually won | Brier |
|---|---|---|---|---|
| depth1 (shipped before) | 103 | 0.648 | 0.670 | 0.2026 |
| depth2 (picked by the retune) | 103 | 0.633 | 0.670 | 0.2019 |
| average of the two | 103 | 0.640 | 0.670 | 0.2016 |

### Senate/Governor, leading by 0-5 points

| Settings | Candidates | Mean predicted | Actually won | Brier |
|---|---|---|---|---|
| depth1 (shipped before) | 44 | 0.667 | 0.750 | 0.2162 |
| depth2 (picked by the retune) | 44 | 0.662 | 0.750 | 0.2069 |
| average of the two | 44 | 0.664 | 0.750 | 0.2107 |

### Democrats leading by 0-5 points, any office

| Settings | Candidates | Mean predicted | Actually won | Brier |
|---|---|---|---|---|
| depth1 (shipped before) | 120 | 0.659 | 0.625 | 0.2156 |
| depth2 (picked by the retune) | 120 | 0.643 | 0.625 | 0.2090 |
| average of the two | 120 | 0.651 | 0.625 | 0.2117 |

### Republicans leading by 0-5 points, any office

| Settings | Candidates | Mean predicted | Actually won | Brier |
|---|---|---|---|---|
| depth1 (shipped before) | 134 | 0.671 | 0.761 | 0.1669 |
| depth2 (picked by the retune) | 134 | 0.653 | 0.761 | 0.1702 |
| average of the two | 134 | 0.662 | 0.761 | 0.1678 |
