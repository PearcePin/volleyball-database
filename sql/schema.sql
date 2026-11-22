CREATE DATABASE IF NOT EXISTS volleyball_db CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs;
USE volleyball_db;

CREATE TABLE IF NOT EXISTS League (
 league_id INT PRIMARY KEY,
 league_name VARCHAR(100) NOT NULL UNIQUE,
 country VARCHAR(50) NOT NULL
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS Season (
 season_id INT PRIMARY KEY,
 league_id INT NOT NULL,
 source_season_id INT NOT NULL,
 season_name VARCHAR(9) NOT NULL,
 UNIQUE (league_id, source_season_id),
 FOREIGN KEY (league_id) REFERENCES League(league_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Team (
 team_id INT PRIMARY KEY,
 team_name VARCHAR(150) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Player (
 player_id INT PRIMARY KEY,
 identity_key VARCHAR(255) NOT NULL UNIQUE,
 player_name VARCHAR(150) NOT NULL,
 gender VARCHAR(10) NOT NULL,
 birthdate DATE NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Season_Team (
 season_id INT NOT NULL,
 team_id INT NOT NULL,
 season_team_name VARCHAR(150) NOT NULL,
 PRIMARY KEY (season_id, team_id),
 FOREIGN KEY (season_id) REFERENCES Season(season_id),
 FOREIGN KEY (team_id) REFERENCES Team(team_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Player_Team_Season (
 player_id INT NOT NULL,
 team_id INT NOT NULL,
 season_id INT NOT NULL,
 source_player_id INT NULL,
 shirt_number INT NULL,
 position VARCHAR(40) NULL,
 PRIMARY KEY (player_id, team_id, season_id),
 UNIQUE (season_id, team_id, source_player_id),
 FOREIGN KEY (player_id) REFERENCES Player(player_id),
 FOREIGN KEY (season_id, team_id) REFERENCES Season_Team(season_id, team_id),
 CHECK (source_player_id IS NULL OR source_player_id > 0),
 CHECK (shirt_number IS NULL OR shirt_number > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `Match` (
 match_id INT PRIMARY KEY,
 season_id INT NOT NULL,
 source_match_id INT NOT NULL,
 home_team_id INT NOT NULL,
 away_team_id INT NOT NULL,
 match_date DATETIME NOT NULL,
 competition_stage VARCHAR(30) NOT NULL,
 home_sets_won INT NOT NULL,
 away_sets_won INT NOT NULL,
 UNIQUE (season_id, source_match_id),
 UNIQUE (match_id, season_id),
 FOREIGN KEY (season_id, home_team_id) REFERENCES Season_Team(season_id, team_id),
 FOREIGN KEY (season_id, away_team_id) REFERENCES Season_Team(season_id, team_id),
 CHECK (home_team_id <> away_team_id),
 CHECK ((home_sets_won = 3 AND away_sets_won BETWEEN 0 AND 2)
     OR (away_sets_won = 3 AND home_sets_won BETWEEN 0 AND 2))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Match_Set (
 match_id INT NOT NULL,
 set_number INT NOT NULL,
 home_points INT NOT NULL,
 away_points INT NOT NULL,
 PRIMARY KEY (match_id, set_number),
 FOREIGN KEY (match_id) REFERENCES `Match`(match_id),
 CHECK (set_number BETWEEN 1 AND 5),
 CHECK (home_points >= 0 AND away_points >= 0 AND home_points <> away_points)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Player_Match_Stats (
 match_id INT NOT NULL,
 player_id INT NOT NULL,
 team_id INT NOT NULL,
 season_id INT NOT NULL,
 total_points INT NULL,
 attacks INT NULL,
 attack_points INT NULL,
 blocks INT NULL,
 aces INT NULL,
 serve_errors INT NULL,
 serves INT NULL,
 PRIMARY KEY (match_id, player_id, team_id),
 FOREIGN KEY (match_id, season_id) REFERENCES `Match`(match_id, season_id),
 FOREIGN KEY (player_id, team_id, season_id)
   REFERENCES Player_Team_Season(player_id, team_id, season_id),
 CHECK (total_points >= 0),
 CHECK (attacks >= 0 AND attack_points >= 0 AND attack_points <= attacks),
 CHECK (blocks >= 0 AND aces >= 0 AND serve_errors >= 0 AND serves >= 0)
) ENGINE=InnoDB;
