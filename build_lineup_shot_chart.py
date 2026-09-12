"""
build_lineup_shot_chart.py -- precomputes TRUE per-lineup shot pools.

This is the piece your three existing chart files never captured.
tipWinChart.json and firstBasketChart.txt store per-PLAYER aggregate
stats -- a player's shots/makes across every lineup they've ever been
part of. That's not the same thing as "every shot taken while this
exact 5-man lineup was on the floor together," which is what your
original readCSV.py computed on-demand (via getFirstBasket() /
getAllBaskets() / getShooter()) by re-scanning raw per-game CSVs for a
chosen lineup.

Run this AFTER scraping games with the substitution-tracking
scraper.py -- it depends on home_player_1..5 / away_player_1..5 being
the ACTUAL on-court five at each shot (not just the starting lineup),
which is what that scraper now produces.

USAGE
-----
Point SEASON_FOLDERS at wherever your scraped CSVs live (same folders
your scraper.py's DATA_DIR wrote to), then run:

    python build_lineup_shot_chart.py

This writes lineupShotChart.json in the current directory. Copy that
file into the web app's data/ folder alongside tipWinChart.json,
firstBasketChart.txt, and lineupChart.txt -- same workflow as those.

OUTPUT FORMAT
-------------
    {
      "Player A|Player B|Player C|Player D|Player E": {
        "Player A": {"makes": 12, "misses": 30},
        "Player B": {"makes": 8, "misses": 15},
        ...
      },
      ...
    }

Keys are the 5 player names, alphabetically sorted and joined with
"|", so the same 5-man combination always maps to one entry
regardless of which "slot" (home_player_1 vs home_player_3, etc.)
each name happened to land in on a given row.
"""

import csv
import glob
import json
import os
import replace_accents as replaceaccents

# Every folder your scraper wrote season CSVs into. Add more as you
# scrape additional seasons.
SEASON_FOLDERS = ["2021", "2022", "2023", "2024", "2025"]


def _lineup_key(names):
    """Canonical, order-independent key for a 5-man lineup."""
    newNames = [replaceaccents.replace_accents_characters(name) for name in names]
    return "|".join(sorted(newNames))


def _iter_game_csvs(folders):
    for folder in folders:
        if not os.path.isdir(folder):
            print(f"[warn] folder not found, skipping: {folder}")
            continue
        for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
            yield path


def build_chart(folders=SEASON_FOLDERS, verbose=True):
    chart = {}  # lineup_key -> {player_name: {"makes": int, "misses": int}}
    games_processed = 0
    rows_used = 0
    rows_skipped_blank_lineup = 0
    rows_skipped_inconsistent = 0

    for path in _iter_game_csvs(folders):
        games_processed += 1
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("eventmsgtype") not in ("1", "2"):
                    continue  # only made/missed shots feed this chart

                shooter = row.get("player1_name", "")
                shooter_team = row.get("player1_team_abbreviation", "")
                if not shooter or not shooter_team:
                    rows_skipped_inconsistent += 1
                    continue

                if shooter_team == row.get("home_team_abbrev"):
                    lineup = [row.get(f"home_player_{i}", "") for i in range(1, 6)]
                elif shooter_team == row.get("away_team_abbrev"):
                    lineup = [row.get(f"away_player_{i}", "") for i in range(1, 6)]
                else:
                    rows_skipped_inconsistent += 1
                    continue

                # Blank slots mean the scraper had abandoned lineup tracking
                # for this side at this point in the game (see scraper.py's
                # _LineupTracker) -- can't attribute this shot to any
                # specific lineup, so skip it rather than guess.
                if any(not name for name in lineup):
                    rows_skipped_blank_lineup += 1
                    continue

                if shooter not in lineup:
                    # Shouldn't happen with the current scraper, but stay
                    # defensive: don't silently record a shot under a
                    # lineup that doesn't actually include the shooter.
                    rows_skipped_inconsistent += 1
                    continue

                key = _lineup_key(lineup)
                entry = chart.setdefault(key, {})
                shooterName = replaceaccents.replace_accents_characters(shooter)
                player_entry = entry.setdefault(shooterName, {"makes": 0, "misses": 0})
                if row["eventmsgtype"] == "1":
                    player_entry["makes"] += 1
                else:
                    player_entry["misses"] += 1
                rows_used += 1
    if verbose:
        print(f"Processed {games_processed} game CSV(s).")
        print(f"Used {rows_used} shot rows across {len(chart)} unique lineups.")
        if rows_skipped_blank_lineup:
            print(
                f"Skipped {rows_skipped_blank_lineup} shot(s) with an incomplete/blank "
                f"lineup (tracking was abandoned for that side at that point in the game)."
            )
        if rows_skipped_inconsistent:
            print(f"Skipped {rows_skipped_inconsistent} shot(s) with inconsistent/missing data.")
        
    return chart


if __name__ == "__main__":
    chart = build_chart()
    out_path = "lineupShotChart.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chart, f, indent=2, ensure_ascii=False)
    print(f"Wrote {out_path}")
