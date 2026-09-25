import csv
from linecache import getlines
import os
import re
import time
import unicodedata

from nba_api.stats.endpoints import (
    boxscoresummaryv3,
    boxscoretraditionalv3,
    playbyplayv3,
)

# NBA's jump-ball description has historically read like:
#   "Jump Ball Giddey vs. Sabonis: Tip to Powell"
# but jump balls with no clean recovery may not match. Unmatched jump
# balls are skipped and logged, not guessed at.
JUMP_BALL_RE = re.compile(
    r"Jump Ball (?P<p1>.+?) vs\.?\s*(?P<p2>.+?):\s*Tip to (?P<p3>.+)"
)

# Confirmed against a real NBA V3 play-by-play sample:
#   "SUB: Mitchell FOR Fox"  (Mitchell entering, Fox leaving)
SUB_RE = re.compile(r"SUB:\s*(?P<in_name>.+?)\s+FOR\s+(?P<out_name>.+)")

# Strips NBA's own review annotations, e.g. "(CC) Hayes" -> "Hayes"
_ANNOTATION_PREFIX_RE = re.compile(r"^\([A-Z]+\)\s*")

# Splits a disambiguating initial NBA adds when two players share a last
# name, e.g. "L. James" -> ("l", "James"). Group 1 is the initial only.
_INITIAL_PREFIX_RE = re.compile(r"^([A-Za-z])\.\s+(.+)$")

FIELDNAMES = [
    "eventmsgtype",
    "home_player_1", "home_player_2", "home_player_3", "home_player_4", "home_player_5",
    "away_player_1", "away_player_2", "away_player_3", "away_player_4", "away_player_5",
    "home_team_abbrev", "away_team_abbrev",
    "player1_name", "player2_name", "player3_name",
    "player1_team_abbreviation", "player3_team_abbreviation",
]

def getStarters(playerStats, gameSummary):
    homeTeamNum = (int)(gameSummary["homeTeamId"].iloc[0])
    awayTeamNum = (int)(gameSummary["awayTeamId"].iloc[0])
    homePlayers = []
    awayPlayers = []
    for line in playerStats.iloc:
        if line.position != "":
            if (line.teamId == homeTeamNum):
                homePlayers.append(line.firstName + " " + line.familyName)
            elif (line.teamId == awayTeamNum):
                awayPlayers.append(line.firstName + " " + line.familyName)
    return homePlayers, awayPlayers

def changeLineups(homeLineup, awayLineup, line, playerStats, gameSummary):
    homeTeamNum = (int)(gameSummary["homeTeamId"].iloc[0])
    awayTeamNum = (int)(gameSummary["awayTeamId"].iloc[0])
    if (line.teamId == homeTeamNum):
        for player in homeLineup:
            playerLast = player.split(" ")
            print(player)
            if (playerLast[1] == line.playerName):
                homeLineup.remove(player)
                break
    elif (line.teamId == awayTeamNum):
        for player in awayLineup:
            playerLast = player.split(" ")
            print(player)
            if (playerLast[1] == line.playerName):
                awayLineup.remove(player)
                break
    print(homeLineup)
    print(awayLineup)
    return homeLineup, awayLineup

def getRow(action, homeLineup, awayLineup, line, **fields):
    row = {
                "home_player_1": homeLineup[0], "home_player_2": homeLineup[1],
                "home_player_3": homeLineup[2], "home_player_4": homeLineup[3],
                "home_player_5": homeLineup[4],
                "away_player_1": awayLineup[0], "away_player_2": awayLineup[1],
                "away_player_3": awayLineup[2], "away_player_4": awayLineup[3],
                "away_player_5": awayLineup[4],
                "home_team_abbrev": home_abbrev, "away_team_abbrev": away_abbrev,
                "eventmsgtype": action,
                "player1_name": "", "player2_name": "", "player3_name": "",
                "player1_team_abbreviation": "", "player3_team_abbreviation": "",
            }
    row.update(fields)
    return row

gameId = 42400102
dataDir = "2024 PLAY"
gameIdStr = str(gameId).zfill(10)
pbp = playbyplayv3.PlayByPlayV3(gameIdStr)
boxScore = boxscoretraditionalv3.BoxScoreTraditionalV3(gameId)
summary = boxscoresummaryv3.BoxScoreSummaryV3(gameId)
lines = pbp.play_by_play.get_data_frame()
lines = lines.copy()
playerStats = boxScore.player_stats.get_data_frame()
playerStats = playerStats.copy()
gameSummary = summary.game_summary.get_data_frame()
gameSummary = gameSummary.copy()

os.makedirs(dataDir, exist_ok=True)
out_path = os.path.join(dataDir, f"{gameId}.csv")
with open(out_path, "w", newline="", encoding="utf-8") as f:
    csvFile = csv.DictWriter(f, fieldnames=FIELDNAMES)
    csvFile.writeheader()
    homeLineup, awayLineup = getStarters(playerStats, gameSummary)
    for line in lines.loc:
        actionType = line.actionType
        print(line)
        if (line.actionType == "Substitution"):
            homeLineup, awayLineup = changeLineups(homeLineup, awayLineup, line, playerStats, gameSummary)
        elif (line.actionType == "Jump Ball"):
            row = getRow(10, homeLineup, awayLineup, line, csvFile)
            #csvFile.writerow(row)
        elif (line.actionType == "Missed Shot"):
            shooter = line.playerName
            row = getRow(2, homeLineup, awayLineup, shooter, player1_name = shooter)
            #csvFile.writerow(row)
        elif (line.actionType == "Made Shot"):
            row = getRow(1, homeLineup, awayLineup, line, csvFile)
            #csvFile.writerow(row)



"""""
def get_game_rosters(game_id):
    
    Returns (home_abbrev, away_abbrev, home_starters[5], away_starters[5],
    starter_name_resolver, roster_name_resolver, roster_first_name_resolver,
    id_resolver).

    Starters are identified via BoxScoreTraditionalV3's `position` field
    (non-empty = started). Player names are built as "firstName familyName"
    since V3's PlayerStats dataset has no single full-name field.

    id_resolver maps personId (int) -> (full_name, side) for EVERY player
    in the box score. Shot events -- and the OUTGOING player in a
    substitution -- carry an exact personId in PlayByPlayV3, so they're
    resolved via this map, never by matching name strings (which breaks
    the moment two players on a roster share a last name).

    starter_name_resolver is a fuzzy (last-name -> candidates) map built
    from STARTERS ONLY, used for jump-ball text parsing (which only ever
    matters at the opening tip -- readCSV.py doesn't read later jump
    balls anyway).

    roster_name_resolver is the same shape but built from the FULL roster
    (starters + bench), used to resolve the INCOMING player in a
    substitution, since bench players entering the game are the whole
    point of a substitution.

    roster_first_name_resolver maps first-name -> [(full_name, side), ...]
    for the full roster, tried as a fallback when roster_name_resolver
    finds no last-name match at all. Confirmed real need: NBA's own
    substitution text sometimes uses a player's given name instead of
    family name (Trail Blazers' Hansen Yang appears as "Hansen", not
    "Yang").
    box = _fetch_with_retries(boxscoretraditionalv3.BoxScoreTraditionalV3, game_id=game_id)
    player_df = box.player_stats.get_data_frame()
    player_df = player_df.copy()
    player_df["full_name"] = (
        player_df["firstName"].fillna("") + " " + player_df["familyName"].fillna("")
    ).str.strip()

    team_ids = player_df["teamId"].unique().tolist()
    if len(team_ids) != 2:
        raise ValueError(f"Expected 2 teams, found {len(team_ids)} for game {game_id}")

    lineups, abbrevs = {}, {}
    for team_id in team_ids:
        team_rows = player_df[player_df["teamId"] == team_id]
        starters = team_rows[team_rows["position"].fillna("") != ""]
        starter_names = starters["full_name"].tolist()
        if len(starter_names) != 5:
            raise ValueError(
                f"Expected 5 starters, found {len(starter_names)} for team {team_id} "
                f"in game {game_id} -- check `position` field values for this game."
            )
        lineups[team_id] = starter_names
        abbrevs[team_id] = team_rows["teamTricode"].iloc[0]

    # BoxScoreTraditionalV3 doesn't cleanly flag home vs. away on player
    # rows, so cross-check with BoxScoreSummaryV2's game header for that.
    summary = _fetch_with_retries(boxscoresummaryv2.BoxScoreSummaryV2, game_id=game_id)
    game_summary_df = summary.game_summary.get_data_frame()
    home_team_id = int(game_summary_df["HOME_TEAM_ID"].iloc[0])
    away_team_id = int(game_summary_df["VISITOR_TEAM_ID"].iloc[0])

    id_resolver = {}
    starter_rows, roster_rows = [], []
    for _, prow in player_df.iterrows():
        side = "home" if prow["teamId"] == home_team_id else "away"
        full_name = prow["full_name"]
        id_resolver[int(prow["personId"])] = (full_name, side)
        roster_rows.append((full_name, side, prow["firstName"], prow["familyName"]))
        if str(prow["position"] or "") != "":
            starter_rows.append((full_name, side, prow["firstName"], prow["familyName"]))

    starter_name_resolver = _build_fuzzy_resolver(starter_rows)
    roster_name_resolver = _build_fuzzy_resolver(roster_rows)
    roster_first_name_resolver = _build_first_name_resolver(roster_rows)

    return (
        abbrevs[home_team_id],
        abbrevs[away_team_id],
        lineups[home_team_id],
        lineups[away_team_id],
        starter_name_resolver,
        roster_name_resolver,
        roster_first_name_resolver,
        id_resolver,
    )


def scrape_game(game_id, data_dir=".", verbose=False):
    Scrapes one game and writes <data_dir>/<game_id>.csv in the column
    format readCSV.py expects, with LIVE on-court lineups per shot --
    tracked via in-period substitutions, AND with each period 2+'s
    opening five reconstructed from evidence (see
    _reconstruct_period_start), since NBA doesn't log between-period
    substitutions at all. Returns the output file path.
    game_id_str = str(game_id).zfill(10)
    fileName = str(game_id)

    (
        home_abbrev, away_abbrev, home_starters, away_starters,
        starter_name_resolver, roster_name_resolver, roster_first_name_resolver, id_resolver,
    ) = get_game_rosters(game_id_str)
    if verbose:
        print(f"  [debug] home_abbrev={home_abbrev!r} home_starters={home_starters!r}")
        print(f"  [debug] away_abbrev={away_abbrev!r} away_starters={away_starters!r}")
    time.sleep(REQUEST_DELAY_SECONDS)

    pbp = _fetch_with_retries(playbyplayv3.PlayByPlayV3, game_id=game_id_str)
    pbp_df = pbp.play_by_play.get_data_frame()
    if "period" in pbp_df.columns and "actionNumber" in pbp_df.columns:
        # Sort by period FIRST, actionNumber second. actionNumber alone
        # isn't safe to sort by if it's numbered per-period rather than
        # globally across the game (which it appears to be) -- sorting
        # by actionNumber alone can interleave rows from different
        # periods, since nothing then forces same-period rows to stay
        # contiguous. That in turn breaks _group_by_period, which relies
        # on identical `period` values being contiguous after sorting.
        pbp_df = pbp_df.sort_values(["period", "actionNumber"]).reset_index(drop=True)
    elif "actionNumber" in pbp_df.columns:
        pbp_df = pbp_df.sort_values("actionNumber").reset_index(drop=True)
        if verbose:
            print("  [warn] no period column to sort by first -- sorting by actionNumber alone")
    elif verbose:
        print("  [warn] no actionNumber column to sort by -- trusting row order as-is")

    os.makedirs(data_dir, exist_ok=True)
    out_path = os.path.join(data_dir, f"{fileName}.csv")

    tracker = _LineupTracker(home_abbrev, away_abbrev, home_starters, away_starters)

    rows_written = 0
    skipped_jump_balls = 0
    skipped_shots_unresolved = 0
    skipped_shots_untrusted = 0

    def build_row(eventmsgtype, **fields):
        home_lineup = tracker.current_lineup("home")
        away_lineup = tracker.current_lineup("away")
        row = {
            "home_player_1": home_lineup[0], "home_player_2": home_lineup[1],
            "home_player_3": home_lineup[2], "home_player_4": home_lineup[3],
            "home_player_5": home_lineup[4],
            "away_player_1": away_lineup[0], "away_player_2": away_lineup[1],
            "away_player_3": away_lineup[2], "away_player_4": away_lineup[3],
            "away_player_5": away_lineup[4],
            "home_team_abbrev": home_abbrev, "away_team_abbrev": away_abbrev,
            "eventmsgtype": eventmsgtype,
            "player1_name": "", "player2_name": "", "player3_name": "",
            "player1_team_abbreviation": "", "player3_team_abbreviation": "",
        }
        row.update(fields)
        return row

    periods = _group_by_period(pbp_df, verbose)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

        for period_index, (period_num, period_actions) in enumerate(periods):
            if period_index == 0:
                pass  # period 1 already seeded with real box-score starters
            else:
                if verbose:
                    print(f"  [debug] -- reconstructing period {period_num} start --")
                _reconstruct_period_start(
                    tracker, period_actions, id_resolver, roster_name_resolver,
                    roster_first_name_resolver, home_abbrev, away_abbrev, verbose,
                )

            for action in period_actions:
                action_type = str(action.get("actionType", ""))
                description = str(action.get("description", ""))

                if action_type == "Substitution":
                    tracker.apply_substitution_row(
                        action, id_resolver, roster_name_resolver,
                        roster_first_name_resolver, verbose,
                    )
                    continue

                if action_type == "Jump Ball":
                    parsed = _parse_jump_ball(description, starter_name_resolver, home_starters, away_starters)
                    if parsed is None:
                        skipped_jump_balls += 1
                        if verbose:
                            print(f"  [warn] Unparsed jump ball: {description!r}")
                        continue
                    p1_name, p2_name, winner_name, p1_team, winner_team = parsed
                    row = build_row(
                        "10",
                        player1_name=p1_name, player2_name=p2_name, player3_name=winner_name,
                        player1_team_abbreviation=home_abbrev if p1_team == "home" else away_abbrev,
                        player3_team_abbreviation=home_abbrev if winner_team == "home" else away_abbrev,
                    )
                    writer.writerow(row)
                    rows_written += 1

                elif action_type in ("Made Shot", "Missed Shot"):
                    person_id = action.get("personId")
                    hit = id_resolver.get(int(person_id)) if person_id is not None else None
                    if hit is None:
                        skipped_shots_unresolved += 1
                        if verbose:
                            raw_player_name = action.get("playerName", "")
                            print(f"  [warn] Unresolved shooter personId {person_id!r} ({raw_player_name!r})")
                        continue
                    shooter_name, shooter_side = hit

                    if not tracker.trusted[shooter_side]:
                        skipped_shots_untrusted += 1
                        continue

                    row = build_row(
                        "1" if action_type == "Made Shot" else "2",
                        player1_name=shooter_name,
                        player1_team_abbreviation=home_abbrev if shooter_side == "home" else away_abbrev,
                    )
                    writer.writerow(row)
                    rows_written += 1

    if rows_written == 0:
        print(f"  [warn] Game {game_id_str}: 0 usable rows written -- check manually.")
    if skipped_jump_balls:
        print(f"  [warn] Game {game_id_str}: skipped {skipped_jump_balls} unparsed jump ball(s).")
    if skipped_shots_unresolved:
        print(f"  [warn] Game {game_id_str}: skipped {skipped_shots_unresolved} shot(s) with unresolved shooter id(s).")
    if skipped_shots_untrusted:
        print(f"  [warn] Game {game_id_str}: skipped {skipped_shots_untrusted} shot(s) after lineup tracking was abandoned.")

    return out_path


if __name__ == "__main__":
    # Same range/shape as your old scraper.py -- adjust as needed.
    START_GAME_ID = 42400101
    END_GAME_ID = 42400108
    DATA_DIR = "2024 PLAY"

    # Carry over your old known-bad game ID lists here as you rediscover them.
    KNOWN_BAD_GAME_IDS = set()

    game_id = START_GAME_ID
    while game_id < END_GAME_ID:
        if game_id in KNOWN_BAD_GAME_IDS:
            game_id += 1
            continue
        try:
            path = scrape_game(game_id, data_dir=DATA_DIR, verbose=False)
            print(f"Game {game_id}: wrote {path}")
        except Exception as e:
            print(f"Game {game_id} not added. ({e})")
        time.sleep(REQUEST_DELAY_SECONDS)
        game_id += 1
"""