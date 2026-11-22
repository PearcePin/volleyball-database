# Volleyball database E-R diagram

Crow's Foot notation: `||` means exactly one, `o{` means zero or many, and `|{` means one or many. Associative tables implement many-to-many relationships. There is no natural one-to-one relationship in this application, so none is invented.

Open [er_diagram.svg](er_diagram.svg) or [er_diagram.png](er_diagram.png) for the rendered diagram.

```mermaid
erDiagram
 League ||--o{ Season : contains
 Season ||--o{ Season_Team : includes
 Team ||--o{ Season_Team : participates
 Player ||--o{ Player_Team_Season : has
 Season_Team ||--o{ Player_Team_Season : registers
 Season_Team ||--o{ Match : home
 Season_Team ||--o{ Match : away
 Match ||--|{ Match_Set : contains
 Match ||--o{ Player_Match_Stats : records
 Player_Team_Season ||--o{ Player_Match_Stats : contributes
 League {
  int league_id PK
  varchar league_name UK
  varchar country
 }
 Season {
  int season_id PK
  int league_id FK
  int source_season_id
  varchar season_name
 }
 Team {
  int team_id PK
  varchar team_name
 }
 Player {
  int player_id PK
  varchar identity_key UK
  varchar player_name
  varchar gender
  date birthdate
 }
 Season_Team {
  int season_id PK,FK
  int team_id PK,FK
  varchar season_team_name
 }
 Player_Team_Season {
  int player_id PK,FK
  int team_id PK,FK
  int season_id PK,FK
  int source_player_id
  int shirt_number
  varchar position
 }
 Match {
  int match_id PK
  int season_id FK
  int source_match_id
  int home_team_id FK
  int away_team_id FK
  datetime match_date
  varchar competition_stage
  int home_sets_won
  int away_sets_won
 }
 Match_Set {
  int match_id PK,FK
  int set_number PK
  int home_points
  int away_points
 }
 Player_Match_Stats {
  int match_id PK,FK
  int player_id PK,FK
  int team_id PK,FK
  int season_id FK
  int total_points
  int attacks
  int attack_points
  int blocks
  int aces
  int serve_errors
  int serves
 }
```

`Match` maps to SQL table `` `Match` ``. Two role-specific composite foreign keys connect `Match(season_id, home_team_id)` and `Match(season_id, away_team_id)` to `Season_Team`. Stats use composite foreign keys `(match_id, season_id)` and `(player_id, team_id, season_id)`. These are not separate single-column foreign keys.

The database stores source observations without an invented one-to-one relationship. Every imported match has 3–5 sets, verified by `validate_data.py`. A foreign key alone cannot enforce the minimum number of child rows.
