"""
scraper.py -- rebuilt on nba_api, replacing the abandoned nba_scraper package.

WHY THIS LOOKS DIFFERENT FROM YOUR OLD SCRAPER
-----------------------------------------------
nba_scraper hasn't been maintained since Jan 2021. On top of that, the
endpoints it effectively depended on (PlayByPlayV2, BoxScoreTraditionalV2)
were *just* deprecated by nba_api itself -- NBA.com now returns empty data
for them. This script uses their replacements, PlayByPlayV3 and
BoxScoreTraditionalV3.

V3's schema is much less structured than V2's. V2 broke every play into
clean player1_name / player2_name / player3_name fields. V3 gives you one
personId/playerName per action plus a free-text "description" string, so
jump-ball detection (who tipped it, who recovered it) means parsing a
sentence like:

    "Jump Ball Giddey vs. Sabonis: Tip to Powell"

instead of reading structured fields. That parsing is the single riskiest
part of this script -- see JUMP_BALL_RE below.

The one thing that's actually *simpler* than before: readCSV.py only ever
reads the lineup at the opening tip-off, not lineup changes through the
game. So this script only needs each team's 5 starters (available directly
from BoxScoreTraditionalV3's `position` field), not full substitution
tracking like nba_scraper used to do.

OUTPUT FORMAT
-------------
Writes one CSV per game with the same column names your readCSV.py already
reads, so readCSV.py itself needs NO changes:

    eventmsgtype, home_player_1..5, away_player_1..5,
    home_team_abbrev, away_team_abbrev,
    player1_name, player2_name, player3_name,
    player1_team_abbreviation, player3_team_abbreviation

IMPORTANT -- THIS IS UNTESTED AGAINST LIVE DATA
------------------------------------------------
I don't have network access to hit the real NBA API from here, so I
couldn't run this against an actual game the way I tested the rest of
your project. Before scraping at scale, run scrape_game() on ONE known
game ID and manually check the printed sample rows / resulting CSV to
confirm:
  1. The jump-ball regex actually matches the live description text.
  2. Player names from BoxScoreTraditionalV3 (built from firstName +
     familyName) match the playerName strings PlayByPlayV3 uses -- these
     come from two different endpoints and could disagree on suffixes
     (e.g. "Jr.") or accented characters (e.g. "Jokic" vs "Jokić"). Your
     project already has a replace_accents module for exactly this kind
     of mismatch; this script uses it if present.

Fix anything that looks wrong in _parse_jump_ball() or _normalize_name()
before trusting a full season run.
"""

import csv
import os
import re
import time
import unicodedata

from nba_api.stats.endpoints import (
    boxscoresummaryv2,
    boxscoretraditionalv3,
    playbyplayv3,
)

try:
    import replace_accents as replaceaccents
    _HAS_REPLACE_ACCENTS = True
except ImportError:
    _HAS_REPLACE_ACCENTS = False

REQUEST_DELAY_SECONDS = 1.0  # NBA.com rate-limits aggressively -- don't remove this
MAX_RETRIES = 3

# NBA's jump-ball description has historically read like:
#   "Jump Ball Giddey vs. Sabonis: Tip to Powell"
# but jump balls with no clean recovery (e.g. tie-up -> possession arrow)
# may not match. Unmatched jump balls are skipped and logged, not guessed at.
JUMP_BALL_RE = re.compile(
    r"Jump Ball (?P<p1>.+?) vs\.?\s*(?P<p2>.+?):\s*Tip to (?P<p3>.+)"
)

FIELDNAMES = [
    "eventmsgtype",
    "home_player_1", "home_player_2", "home_player_3", "home_player_4", "home_player_5",
    "away_player_1", "away_player_2", "away_player_3", "away_player_4", "away_player_5",
    "home_team_abbrev", "away_team_abbrev",
    "player1_name", "player2_name", "player3_name",
    "player1_team_abbreviation", "player3_team_abbreviation",
]


def _normalize_name(name):
    """
    Best-effort normalization so names from different endpoints compare
    equal (e.g. accented vs unaccented). Uses your project's own
    replace_accents module if it's importable; otherwise falls back to a
    generic unicode strip.
    """
    if not name:
        return name
    if _HAS_REPLACE_ACCENTS and hasattr(replaceaccents, "replace_accents"):
        return replaceaccents.replace_accents(name)
    normalized = unicodedata.normalize("NFKD", name)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def _fetch_with_retries(endpoint_cls, **kwargs):
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return endpoint_cls(**kwargs)
        except Exception as e:
            last_error = e
            time.sleep(REQUEST_DELAY_SECONDS * attempt)
    raise last_error


def get_starting_lineups(game_id):
    """
    Returns (home_abbrev, away_abbrev, home_starters[5], away_starters[5],
    starter_name_resolver, id_resolver).

    Starters are identified via BoxScoreTraditionalV3's `position` field
    (non-empty = started). Player names are built as "firstName familyName"
    since V3's PlayerStats dataset has no single full-name field.

    id_resolver maps personId (int) -> (full_name, side) for EVERY player
    in the box score (starters and bench). Shot events carry an exact
    personId in PlayByPlayV3, so shooter identity is resolved via this
    map -- never by matching name strings, which breaks the moment two
    players on the same roster share a last name (e.g. OKC's Kenrich
    Williams and Jaylin Williams).

    starter_name_resolver maps a normalized LAST NAME ONLY -> (full_name,
    side), built from starters ONLY, or -> None if that last name is
    ambiguous between the two starters on the floor for the tip. This is
    only used for jump balls, since PlayByPlayV3's jump-ball description
    text gives last names, not personIds, for the two jumpers and the
    recipient (e.g. "Jump Ball Holmgren vs. Sims: Tip to Wallace"). It's
    scoped to starters only (rather than the full roster) because
    readCSV.py only ever reads the opening tip-off, which is always
    between starters -- narrowing the scope this way avoids exactly the
    kind of bench/starter last-name collision described above.
    """
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

    # Exact resolver: personId -> (full_name, side), for every player.
    id_resolver = {}
    for _, prow in player_df.iterrows():
        side = "home" if prow["teamId"] == home_team_id else "away"
        id_resolver[int(prow["personId"])] = (prow["full_name"], side)

    # Fuzzy resolver: last-name -> (full_name, side), STARTERS ONLY, used
    # only for jump-ball text parsing. None marks an ambiguous last name.
    starter_name_resolver = {}
    ambiguous = set()
    for team_id in team_ids:
        side = "home" if team_id == home_team_id else "away"
        team_rows = player_df[player_df["teamId"] == team_id]
        starters = team_rows[team_rows["position"].fillna("") != ""]
        for _, prow in starters.iterrows():
            full_name = prow["full_name"]
            last_name_key = _normalize_name(str(prow["familyName"])).lower().strip()
            if last_name_key in starter_name_resolver and starter_name_resolver[last_name_key] not in (
                None, (full_name, side)
            ):
                ambiguous.add(last_name_key)
            starter_name_resolver[last_name_key] = (full_name, side)
    for key in ambiguous:
        starter_name_resolver[key] = None

    return (
        abbrevs[home_team_id],
        abbrevs[away_team_id],
        lineups[home_team_id],
        lineups[away_team_id],
        starter_name_resolver,
        id_resolver,
    )


def _resolve_name(raw_name, resolver, home_starters, away_starters):
    """
    Resolves a name that might be a full name already or might be a
    last-name-only mention (as jump-ball descriptions give) into the
    canonical full name used elsewhere in this game's CSV, plus which
    side ("home"/"away") it belongs to.

    Used ONLY for jump-ball text parsing (`resolver` here should be the
    starters-only resolver) -- shot events are resolved exactly via
    personId instead, see `id_resolver` in scrape_game().

    Returns (full_name, side) or (None, None) if it can't be resolved --
    callers should skip rather than guess when that happens.
    """
    normalized = _normalize_name(raw_name).strip()

    # Already a known full name (e.g. shot events might give this).
    for side, starters in (("home", home_starters), ("away", away_starters)):
        if normalized in [_normalize_name(n) for n in starters]:
            return normalized, side

    # Otherwise treat it as a last name and look it up.
    hit = resolver.get(normalized.lower())
    if hit is None:
        return None, None
    return hit


def _parse_jump_ball(description, resolver, home_starters, away_starters):
    """
    Parses a jump-ball description string into (p1_name, p2_name,
    winner_name, p1_team, winner_team), with all three names resolved to
    full names via `resolver`. Returns None if the description doesn't
    match the expected pattern, or any name can't be resolved -- callers
    should skip the row rather than guess.
    """
    match = JUMP_BALL_RE.search(description)
    if not match:
        return None

    p1_full, p1_team = _resolve_name(match.group("p1"), resolver, home_starters, away_starters)
    p2_full, _ = _resolve_name(match.group("p2"), resolver, home_starters, away_starters)
    winner_full, winner_team = _resolve_name(match.group("p3"), resolver, home_starters, away_starters)

    if None in (p1_full, p2_full, winner_full, p1_team, winner_team):
        return None

    return p1_full, p2_full, winner_full, p1_team, winner_team


def scrape_game(game_id, data_dir=".", verbose=False):
    """
    Scrapes one game and writes <data_dir>/<game_id>.csv in the column
    format readCSV.py expects. Returns the output file path.
    """
    game_id_str = str(game_id).zfill(10)
    fileName=str(game_id)

    home_abbrev, away_abbrev, home_starters, away_starters, starter_name_resolver, id_resolver = (
        get_starting_lineups(game_id_str)
    )
    time.sleep(REQUEST_DELAY_SECONDS)

    pbp = _fetch_with_retries(playbyplayv3.PlayByPlayV3, game_id=game_id_str)
    pbp_df = pbp.play_by_play.get_data_frame()

    os.makedirs(data_dir, exist_ok=True)
    out_path = os.path.join(data_dir, f"{fileName}.csv")

    base_row = {
        "home_player_1": home_starters[0], "home_player_2": home_starters[1],
        "home_player_3": home_starters[2], "home_player_4": home_starters[3],
        "home_player_5": home_starters[4],
        "away_player_1": away_starters[0], "away_player_2": away_starters[1],
        "away_player_3": away_starters[2], "away_player_4": away_starters[3],
        "away_player_5": away_starters[4],
        "home_team_abbrev": home_abbrev, "away_team_abbrev": away_abbrev,
    }

    rows_written = 0
    skipped_jump_balls = 0
    skipped_shots = 0

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

        for _, action in pbp_df.iterrows():
            action_type = str(action.get("actionType", ""))
            description = str(action.get("description", ""))

            if action_type == "Jump Ball":
                parsed = _parse_jump_ball(description, starter_name_resolver, home_starters, away_starters)
                if parsed is None:
                    skipped_jump_balls += 1
                    if verbose:
                        print(f"  [warn] Unparsed jump ball: {description!r}")
                    continue
                p1_name, p2_name, winner_name, p1_team, winner_team = parsed
                row = dict(base_row)
                row.update({
                    "eventmsgtype": "10",
                    "player1_name": p1_name,
                    "player2_name": p2_name,
                    "player3_name": winner_name,
                    "player1_team_abbreviation": home_abbrev if p1_team == "home" else away_abbrev,
                    "player3_team_abbreviation": home_abbrev if winner_team == "home" else away_abbrev,
                })
                writer.writerow(row)
                rows_written += 1

            elif action_type in ("Made Shot", "Missed Shot"):
                # Exact lookup by personId -- never guessed from a name
                # string, which breaks the moment two players on a roster
                # share a last name (e.g. OKC's two Williamses).
                person_id = action.get("personId")
                hit = id_resolver.get(int(person_id)) if person_id is not None else None
                if hit is None:
                    skipped_shots += 1
                    if verbose:
                        raw_player_name = action.get("playerName", "")
                        print(f"  [warn] Unresolved shooter personId {person_id!r} ({raw_player_name!r})")
                    continue
                shooter_name, shooter_side = hit
                row = dict(base_row)
                row.update({
                    "eventmsgtype": "1" if action_type == "Made Shot" else "2",
                    "player1_name": shooter_name,
                    "player1_team_abbreviation": home_abbrev if shooter_side == "home" else away_abbrev,
                })
                writer.writerow(row)
                rows_written += 1

    if rows_written == 0:
        print(f"  [warn] Game {game_id_str}: 0 usable rows written -- check manually.")
    if skipped_jump_balls:
        print(f"  [warn] Game {game_id_str}: skipped {skipped_jump_balls} unparsed jump ball(s).")
    if skipped_shots:
        print(f"  [warn] Game {game_id_str}: skipped {skipped_shots} shot(s) with unresolved shooter name(s).")

    return out_path


if __name__ == "__main__":
    # Same range/shape as your old scraper.py -- adjust as needed.
    START_GAME_ID = 22501201
    END_GAME_ID = 22501208
    DATA_DIR = "2025"

    # Carry over your old known-bad game ID lists here as you rediscover them.
    KNOWN_BAD_GAME_IDS = set()

    game_id = START_GAME_ID
    while game_id < END_GAME_ID:
        if game_id in KNOWN_BAD_GAME_IDS:
            game_id += 1
            continue
        try:
            path = scrape_game(game_id, data_dir=DATA_DIR, verbose=True)
            print(f"Game {game_id}: wrote {path}")
        except Exception as e:
            print(f"Game {game_id} not added. ({e})")
        time.sleep(REQUEST_DELAY_SECONDS)
        game_id += 1
