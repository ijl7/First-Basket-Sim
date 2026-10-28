"""
scraper.py -- rebuilt on nba_api, replacing the abandoned nba_scraper package.
Now tracks live substitutions, so home_player_1..5 / away_player_1..5 reflect
who was ACTUALLY on the floor at each shot -- not just the starting five.

WHY THIS LOOKS DIFFERENT FROM YOUR OLD SCRAPER
-----------------------------------------------
nba_scraper hasn't been maintained since Jan 2021, and on top of that the
endpoints it depended on (PlayByPlayV2, BoxScoreTraditionalV2) were *just*
deprecated -- NBA.com now returns empty data for them. This uses their
replacements, PlayByPlayV3 and BoxScoreTraditionalV3, which have a much
less structured schema: no player1/player2/player3 fields, just one
personId/playerName per action plus a free-text "description" string. So
jump balls and substitutions are read by parsing sentences like:

    "Jump Ball Giddey vs. Sabonis: Tip to Powell"
    "SUB: Mitchell FOR Fox"

instead of clean structured fields. Two things reduce the risk in that
text parsing:
  1. For substitutions specifically, the action's own personId reliably
     identifies the player going OUT (confirmed against a real NBA V3
     sample: a "SUB: Mitchell FOR Fox" row's personId pointed to Fox) --
     so only the incoming player's name has to be fuzzy-matched; the
     outgoing player is resolved exactly by ID, same as shots.
  2. If a substitution can't be resolved cleanly (unparseable text, or
     the "outgoing" player isn't where our tracking expects them to be,
     meaning we've desynced), that team's on-court tracking is marked
     untrustworthy FOR THE REST OF THAT GAME. Rather than keep guessing
     with a possibly-wrong lineup, that team's lineup columns are written
     as blank from that point on, and any of their shots are skipped.
     The other team's rows are unaffected. See _mark_untrusted().

OUTPUT FORMAT
-------------
Writes one CSV per game with the same column names your readCSV.py already
reads, so readCSV.py itself needs NO changes -- and since readCSV.py's own
getFirstBasket()/getAllBaskets() already check lineup membership PER ROW
(it was written assuming nba_scraper's per-row-accurate lineups), feeding
it real per-row lineups here means that existing logic just works:

    eventmsgtype, home_player_1..5, away_player_1..5,
    home_team_abbrev, away_team_abbrev,
    player1_name, player2_name, player3_name,
    player1_team_abbreviation, player3_team_abbreviation

IMPORTANT -- THIS IS UNTESTED AGAINST LIVE DATA
------------------------------------------------
I don't have network access to hit the real NBA API from here. The
substitution-parsing regex and the personId-is-the-outgoing-player
assumption are both based on one confirmed real example, not something
I could verify against dozens of live games. Before scraping at scale:
  1. Run scrape_game() on ONE known game with verbose=True.
  2. Check for "[warn] lineup tracking abandoned" messages -- if a game
     produces one early (e.g. in the 1st quarter), something about that
     game's substitution text doesn't match what's expected here; paste
     me the exact description string and I'll fix the regex/logic.
  3. Spot check a few mid-game rows' home_player_1..5 against what you
     know actually happened in that game (who was on the floor).
"""

import csv
import os
import re
import time
import unicodedata

from nba_api.stats.endpoints import (
    boxscoresummaryv3,
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

# NBA embeds the assisting player's name only as free text inside a shot
# description's parenthetical, e.g. "Ivey 26' 3PT Jump Shot (16 PTS)
# (Duren 3 AST)" -- there's no separate assistPersonId field to read.
_ASSIST_RE = re.compile(r"\(([^()]+?)\s+\d+\s+AST\)")

# Splits the disambiguating first-name prefix NBA adds when two players
# share a last name. Usually a single initial ("L. James" -> ("l", "James")),
# but when two players on the SAME roster share both last name AND first
# initial, NBA uses a longer prefix instead -- confirmed real example:
# OKC's Jalen Williams and Jaylin Williams -- NBA writes Jaylin as
# "Jay. Williams". Group 1 is the prefix (one or more letters); matching
# it against a candidate's first name is a startswith() check.
_INITIAL_PREFIX_RE = re.compile(r"^([A-Za-z]+)\.\s+(.+)$")

# PlayByPlayV3's `clock` field, e.g. "PT09M12.00S" -> 552.0 seconds remaining.
_CLOCK_RE = re.compile(r"^PT(\d+)M([\d.]+)S$")


def _parse_clock_seconds(clock):
    """
    Parses a V3 clock string ("PT09M12.00S") into total seconds remaining
    in the period, or None if it isn't in that format. Callers must treat
    None as "can't order by clock" rather than guessing a value.
    """
    if clock is None:
        return None
    match = _CLOCK_RE.match(str(clock).strip())
    if not match:
        return None
    try:
        return int(match.group(1)) * 60 + float(match.group(2))
    except ValueError:
        return None

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


def _build_first_name_resolver(rows):
    """
    Builds a first-name -> [(full_name, side), ...] map. Some players
    are referred to by their given name rather than family name in
    NBA's substitution text (confirmed real example: Trail Blazers'
    Hansen Yang appears as "Hansen", not "Yang") -- this is a fallback
    for exactly that, tried only after the family-name resolver fails.
    """
    resolver = {}
    for full_name, side, first_name, _family_name in rows:
        first_name_key = _normalize_name(str(first_name)).lower().strip()
        resolver.setdefault(first_name_key, []).append((full_name, side))
    return resolver


def _build_fuzzy_resolver(rows):
    """
    Builds a last-name -> [(full_name, side, first_name_normalized), ...]
    map from box-score rows. A last name maps to a LIST because two
    players can share one (NBA disambiguates with a first-name prefix in
    its own text, e.g. "L. James" or "Jay. Williams" -- see
    _resolve_name). The FULL normalized first name is stored (not just
    an initial) so multi-letter prefixes can be checked with startswith().
    """
    resolver = {}
    for full_name, side, first_name, family_name in rows:
        first_name_normalized = _normalize_name(str(first_name)).strip().lower()
        last_name_key = _normalize_name(str(family_name)).lower().strip()
        resolver.setdefault(last_name_key, []).append((full_name, side, first_name_normalized))
    return resolver


def get_game_rosters(game_id):
    """
    Returns (home_abbrev, away_abbrev, home_starters[5], away_starters[5],
    roster_name_resolver, roster_first_name_resolver, id_resolver).

    Starters are identified via BoxScoreTraditionalV3's `position` field
    (non-empty = started). Player names are built as "firstName familyName"
    since V3's PlayerStats dataset has no single full-name field.

    id_resolver maps personId (int) -> (full_name, side) for EVERY player
    in the box score. Shot events -- and the OUTGOING player in a
    substitution -- carry an exact personId in PlayByPlayV3, so they're
    resolved via this map, never by matching name strings (which breaks
    the moment two players on a roster share a last name).

    roster_name_resolver is a fuzzy (last-name -> candidates) map built
    from the FULL roster (starters + bench), used to resolve the
    INCOMING player in a substitution and to resolve jump-ball
    participants (opening tip AND any overtime jump balls -- validated
    against who's actually tracked on the floor at that point, since a
    fuzzy match alone doesn't guarantee it's the right person if two
    players share a last name).

    roster_first_name_resolver maps first-name -> [(full_name, side), ...]
    for the full roster, tried as a fallback when roster_name_resolver
    finds no last-name match at all. Confirmed real need: NBA's own
    substitution text sometimes uses a player's given name instead of
    family name (Trail Blazers' Hansen Yang appears as "Hansen", not
    "Yang").
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
    # rows, so cross-check with BoxScoreSummaryV3's game header for that.
    # (BoxScoreSummaryV2 is broken for games on/after 4/10/2025 -- confirmed
    # empty-response failures on 2024-25 playoff games; V3's game_summary
    # dataset uses camelCase field names, confirmed against real data:
    # homeTeamId/awayTeamId, not V2's HOME_TEAM_ID/VISITOR_TEAM_ID.)
    summary = _fetch_with_retries(boxscoresummaryv3.BoxScoreSummaryV3, game_id=game_id)
    game_summary_df = summary.game_summary.get_data_frame()
    home_team_id = int(game_summary_df["homeTeamId"].iloc[0])
    away_team_id = int(game_summary_df["awayTeamId"].iloc[0])

    id_resolver = {}
    roster_rows = []
    for _, prow in player_df.iterrows():
        side = "home" if prow["teamId"] == home_team_id else "away"
        full_name = prow["full_name"]
        id_resolver[int(prow["personId"])] = (full_name, side)
        roster_rows.append((full_name, side, prow["firstName"], prow["familyName"]))

    roster_name_resolver = _build_fuzzy_resolver(roster_rows)
    roster_first_name_resolver = _build_first_name_resolver(roster_rows)

    return (
        abbrevs[home_team_id],
        abbrevs[away_team_id],
        lineups[home_team_id],
        lineups[away_team_id],
        roster_name_resolver,
        roster_first_name_resolver,
        id_resolver,
    )


def _resolve_name(raw_name, resolver, known_full_names=None, first_name_resolver=None,
                   restrict_to_side=None, verbose=False):
    """
    Resolves a name that might already be a full name, a plain last
    name, an initial-disambiguated last name (e.g. "L. James"), or one
    with a review annotation (e.g. "(CC) Hayes") into (full_name, side)
    via `resolver` (last-name -> [(full_name, side, first_name_normalized), ...]).

    known_full_names, if given, is an iterable of (full_name, side)
    pairs tried as an exact-match fast path first.

    restrict_to_side, if given ("home" or "away"), filters candidates
    to that side BEFORE checking for ambiguity. This is safe (not a
    guess) whenever the caller already knows which side this name must
    belong to from other, certain evidence -- e.g. a substitution's
    outgoing player is resolved exactly by personId, and a substitution
    is always within one team, so the incoming player must share that
    side. Confirmed real need: two different players named "Love"
    (Kevin Love, Jazz; Caleb Love, Blazers) made a same-game
    cross-roster last-name collision that an initial alone didn't
    disambiguate -- knowing which team the substitution belongs to
    resolves it cleanly without guessing.

    first_name_resolver, if given, is tried as a fallback when the
    last-name lookup fails outright (0 candidates) -- some players are
    referred to by their given name in NBA's text instead of their
    family name (confirmed real example: "Hansen" for Hansen Yang).
    Not tried when the last-name lookup was merely ambiguous (2+
    candidates), since that's a different, already-informative failure.

    Returns (None, None) if it can't be resolved unambiguously --
    callers should skip rather than guess when that happens. When that
    happens and verbose is set, prints exactly what the resolver did
    and didn't find, to distinguish "name not in roster at all" from
    "genuinely ambiguous, multiple real candidates" -- these need
    different fixes and shouldn't be guessed at without seeing which.
    """
    cleaned = _ANNOTATION_PREFIX_RE.sub("", raw_name.strip())
    normalized = _normalize_name(cleaned).strip()

    if known_full_names:
        for full_name, side in known_full_names:
            if _normalize_name(full_name) == normalized:
                return full_name, side

    initial = None
    initial_match = _INITIAL_PREFIX_RE.match(normalized)
    if initial_match:
        initial = initial_match.group(1).lower()
        normalized = initial_match.group(2).strip()

    candidates = resolver.get(normalized.lower())
    if candidates:
        if restrict_to_side is not None:
            side_matches = [c for c in candidates if c[1] == restrict_to_side]
            if len(side_matches) == 1:
                full_name, side, _ = side_matches[0]
                return full_name, side
            if side_matches:
                candidates = side_matches  # still ambiguous, but narrowed; fall through
        if len(candidates) == 1:
            full_name, side, _ = candidates[0]
            return full_name, side
        if initial is not None:
            # startswith(), not ==: handles both a single initial ("l" ->
            # "lebron") and NBA's longer prefixes ("jay" -> "jaylin",
            # but NOT "jalen"). A bare "j" still matches both and stays
            # ambiguous -> skipped, never guessed.
            matches = [c for c in candidates if c[2].startswith(initial)]
            if len(matches) == 1:
                full_name, side, _ = matches[0]
                return full_name, side
        if verbose:
            print(
                f"    [debug] resolve {raw_name!r}: ambiguous last-name match, "
                f"candidates={candidates!r}, initial given={initial!r}, "
                f"restrict_to_side={restrict_to_side!r} -- refusing to guess"
            )
        return None, None

    # No last-name match at all -- try first name (e.g. "Hansen" for Hansen Yang).
    if first_name_resolver is not None:
        fn_candidates = first_name_resolver.get(normalized.lower())
        if restrict_to_side is not None and fn_candidates:
            fn_side_matches = [c for c in fn_candidates if c[1] == restrict_to_side]
            if len(fn_side_matches) == 1:
                return fn_side_matches[0]
            if fn_side_matches:
                fn_candidates = fn_side_matches
        if fn_candidates and len(fn_candidates) == 1:
            return fn_candidates[0]
        if fn_candidates and verbose:
            print(
                f"    [debug] resolve {raw_name!r}: ambiguous first-name match, "
                f"candidates={fn_candidates!r} -- refusing to guess"
            )

    if verbose:
        print(f"    [debug] resolve {raw_name!r}: no last-name OR first-name match found at all")
    return None, None


def _parse_jump_ball(description, roster_name_resolver, roster_first_name_resolver, tracker, verbose=False):
    """
    Parses a jump-ball description into (p1_name, p2_name, winner_name,
    p1_team, winner_team), all resolved to full names. Returns None if
    the text doesn't match or any name can't be resolved.

    Resolves against the FULL roster (not just starters) and validates
    each resolved player is currently in tracker.on_court -- this
    matters because jump balls aren't only the opening tip; overtime
    periods start with a fresh jump ball too, between whoever's
    actually on the floor at that point (which can be entirely
    different from the original 5 starters after 4+ quarters of
    substitutions). Requiring on-court membership also guards against
    a same-last-name mismatch: if resolution lands on a real player
    who isn't tracked as on the floor, that's treated as unresolved
    rather than trusted.

    p1 and p2 are always on OPPOSING teams -- a jump ball is contested
    between one player from each side, never two teammates. So whichever
    of the two resolves unambiguously first is used to restrict the
    other's resolution to the opposite team. This is symmetric -- it
    doesn't matter whether the ambiguous name is written first or
    second in the text ("A vs. B" and "B vs. A" both occur), since
    which name resolves cleanly on the first pass is what determines
    the restriction, not position in the string. Confirmed real need:
    "Jump Ball Sengun vs. Green: Tip to Thompson" (Sengun home, Rockets)
    AND, in a later game, "Jump Ball Green vs. Sengun: Tip to Thompson"
    (Sengun away this time) -- "Green" was ambiguous across three real
    players in both, and only cross-checking against whichever of the
    two names is unambiguous resolves it regardless of which side of
    "vs." it lands on. Winner (p3) isn't restricted this way since the
    tip can go to either jumper's own teammate.
    """
    match = JUMP_BALL_RE.search(description)
    if not match:
        return None

    def resolve_and_verify(raw_name, restrict_to_side=None):
        known = [(n, "home") for n in tracker.on_court["home"]] + [(n, "away") for n in tracker.on_court["away"]]
        if restrict_to_side is not None:
            known = [(n, s) for n, s in known if s == restrict_to_side]
        full_name, side = _resolve_name(
            raw_name, roster_name_resolver, known_full_names=known,
            first_name_resolver=roster_first_name_resolver,
            restrict_to_side=restrict_to_side, verbose=verbose,
        )
        if full_name is None:
            return None, None
        if not tracker.trusted[side] or full_name not in tracker.on_court[side]:
            if verbose:
                print(f"    [debug] jump ball: {raw_name!r} resolved to {full_name!r} but not currently on court for {side}")
            return None, None
        return full_name, side

    opposite = {"home": "away", "away": "home"}

    p1_full, p1_team = resolve_and_verify(match.group("p1"))
    p2_full, p2_team = resolve_and_verify(match.group("p2"))

    if p1_full is None and p2_full is not None:
        p1_full, p1_team = resolve_and_verify(match.group("p1"), restrict_to_side=opposite.get(p2_team))
    elif p2_full is None and p1_full is not None:
        p2_full, p2_team = resolve_and_verify(match.group("p2"), restrict_to_side=opposite.get(p1_team))

    winner_full, winner_team = resolve_and_verify(match.group("p3"))

    if None in (p1_full, p2_full, winner_full, p1_team, winner_team):
        return None
    return p1_full, p2_full, winner_full, p1_team, winner_team


class _LineupTracker:
    """
    Tracks each team's current on-court five, live, as substitutions
    happen through the game. Starts from the opening starters; each
    substitution swaps the outgoing player's slot for the incoming one.

    If a substitution can't be resolved, or the outgoing player isn't
    where tracking expects them to be (a desync), that team is marked
    untrusted for the REST of the game: its lineup columns are blanked
    (never a stale/wrong guess) and its shots are skipped from then on.
    """

    def __init__(self, home_abbrev, away_abbrev, home_starters, away_starters):
        self.abbrev = {"home": home_abbrev, "away": away_abbrev}
        self.on_court = {"home": list(home_starters), "away": list(away_starters)}
        self.trusted = {"home": True, "away": True}
        self.untrusted_logged = {"home": False, "away": False}

    def side_for_abbrev(self, abbrev):
        if abbrev == self.abbrev["home"]:
            return "home"
        if abbrev == self.abbrev["away"]:
            return "away"
        return None

    def current_lineup(self, side):
        """Returns the 5 names to write for `side`, or 5 blanks if untrusted."""
        if not self.trusted[side]:
            return ["", "", "", "", ""]
        return list(self.on_court[side])

    def mark_untrusted(self, side, reason, verbose):
        if side is None:
            self.trusted["home"] = False
            self.trusted["away"] = False
            sides = ["home", "away"]
        else:
            self.trusted[side] = False
            sides = [side]
        for s in sides:
            if verbose and not self.untrusted_logged[s]:
                print(f"  [warn] {s} lineup tracking abandoned for rest of game: {reason}")
            self.untrusted_logged[s] = True

    def _current_court_fallback(self, side, out_name_text, roster_name_resolver):
        """
        Fallback for when the personId-resolved outgoing player isn't
        actually on the floor (as just happened: NBA's own data attached
        the wrong personId to a "Williams" substitution, when TWO
        Williamses were on the roster and the wrong one's ID got used).

        Checks whether exactly one player CURRENTLY on court for `side`
        shares the last name given in the substitution's own text.
        Returns that player's full name, or None if zero or multiple
        current on-court players match -- still never guesses between
        genuine ambiguity, just widens what counts as "found" to reality
        on the floor instead of trusting a personId that's disagreeing
        with everything else we've tracked so far.
        """
        cleaned = _ANNOTATION_PREFIX_RE.sub("", out_name_text.strip())
        normalized = _normalize_name(cleaned).strip()
        initial = None
        initial_match = _INITIAL_PREFIX_RE.match(normalized)
        if initial_match:
            initial = initial_match.group(1).lower()
            normalized = initial_match.group(2).strip()

        candidates = roster_name_resolver.get(normalized.lower())
        if not candidates:
            return None
        on_court_names = set(self.on_court[side])
        matches = [c for c in candidates if c[0] in on_court_names]
        if initial is not None:
            narrowed = [c for c in matches if c[2].startswith(initial)]
            if narrowed:
                matches = narrowed
        if len(matches) == 1:
            return matches[0][0]
        return None

    def apply_substitution_row(self, action, id_resolver, roster_name_resolver,
                                roster_first_name_resolver, verbose):
        description = str(action.get("description", ""))
        team_tricode = action.get("teamTricode", "")
        claimed_side = self.side_for_abbrev(team_tricode)

        match = SUB_RE.search(description)
        if not match:
            self.mark_untrusted(claimed_side, f"unparsed substitution text {description!r}", verbose)
            return

        out_person_id = action.get("personId")
        out_hit = id_resolver.get(int(out_person_id)) if out_person_id is not None else None
        if out_hit is None:
            self.mark_untrusted(
                claimed_side, f"outgoing player personId {out_person_id!r} not in box score", verbose
            )
            return
        out_full, out_side = out_hit

        in_full, in_side = _resolve_name(
            match.group("in_name"), roster_name_resolver,
            first_name_resolver=roster_first_name_resolver,
            restrict_to_side=out_side, verbose=verbose,
        )
        if in_full is None:
            self.mark_untrusted(
                out_side,
                f"couldn't resolve incoming player {match.group('in_name')!r} "
                f"(full text: {description!r})",
                verbose,
            )
            return

        if in_side != out_side:
            # A substitution is always within one team -- if the incoming
            # and outgoing players resolved to different sides, something
            # is wrong (bad resolution, or a genuinely malformed row).
            # Don't apply it; treat it the same as any other desync.
            self.mark_untrusted(
                out_side,
                f"incoming/outgoing side mismatch (in={in_side}, out={out_side}) in {description!r}",
                verbose,
            )
            return

        side = out_side  # trust the exact personId-derived side over parsed text
        if not self.trusted[side]:
            return  # already abandoned tracking for this side this game

        if verbose:
            print(f"  [debug] sub on {side}: IN={in_full!r} OUT={out_full!r} before={self.on_court[side]!r}")

        try:
            slot = self.on_court[side].index(out_full)
        except ValueError:
            fallback_full = self._current_court_fallback(side, match.group("out_name"), roster_name_resolver)
            if fallback_full is None:
                self.mark_untrusted(
                    side,
                    f"expected {out_full!r} on court to sub out, but tracked lineup was "
                    f"{self.on_court[side]} ({description!r})",
                    verbose,
                )
                return
            if verbose:
                print(
                    f"  [debug] sub on {side}: personId pointed to {out_full!r} (not on court) -- "
                    f"falling back to on-court name match {fallback_full!r}"
                )
            out_full = fallback_full
            slot = self.on_court[side].index(out_full)

        self.on_court[side][slot] = in_full
        if verbose:
            print(f"  [debug] sub on {side}: after={self.on_court[side]!r}")


def _reconstruct_period_start(tracker, period_actions, id_resolver, roster_name_resolver,
                               roster_first_name_resolver, home_abbrev, away_abbrev, verbose):
    """
    NBA's play-by-play only logs mid-quarter substitutions -- whoever
    starts periods 2+ is never announced, it's only implied by who
    shows up in that period's actions. Reconstructs each side's TRUE
    period-opening five before any rows for this period get written.

    Classification happens in two STAGES, each player decided ONCE at
    their first mention within that stage, never revisited:

      STAGE 1 -- substitutions ONLY, in order, ignoring every other
      action type entirely. For each substitution: the OUTGOING player
      (resolved exactly by personId), if this is their first mention
      in this stage, is classified ORIGINAL -- subbing out proves they
      were already on the floor. The INCOMING player, if this is their
      first mention in this stage, is classified LATER ENTRANT.
      Deliberately restricted to substitution-vs-substitution ordering
      only, because that ordering has held up in every case seen so
      far -- it's specifically substitution-vs-non-substitution
      ordering that's been unreliable (confirmed real case: a
      substitute's own rebound was returned before the substitution
      event that brought them in). Working only from the substitution
      sequence sidesteps that entirely.

      STAGE 2 -- every other action type, for whoever STAGE 1 never
      mentioned in either direction (never subbed in, never subbed out,
      this whole period): their first appearance in any logged action
      classifies them ORIGINAL. This is safe precisely because there's
      no substitution event for them to conflict with -- if you're
      active all period and never got subbed either way, you must have
      started there. Stage 2 itself runs in two passes: PASS A uses
      only an action's own personId (an exact id_resolver match --
      shooter, rebounder, etc.); PASS B is backup-only, run entirely
      after PASS A completes, and covers on-court evidence that only
      ever appears as free text with no personId to match -- a jump
      ball's two participants and tip recipient, and a shot's assisting
      player. Keeping these as a strictly later pass (not interleaved
      per-action with PASS A) matters: a fuzzy-resolved backup name
      from an earlier action must never claim one of a side's 5 slots
      ahead of a solid personId match that shows up later in the same
      period -- see the pass B comment below for why.

    Because each player is decided once at first mention and later
    re-appearances are no-ops, this also correctly handles a genuinely
    original player who subs out and back in one or more times within
    the same period: their first STAGE 1 mention (being subbed out)
    fixes them as ORIGINAL, and any later re-entry doesn't undo it.

    Once a side reaches 5 confirmed originals, it stops accepting any
    further ones for the rest of the period.

    Sets tracker.on_court[side]/tracker.trusted[side] directly. If a
    side never reaches exactly 5 proven players across the whole
    period (would require a player with zero logged actions of any
    kind for an entire quarter -- vanishingly rare), that side is
    marked untrusted for THIS period only; the next period gets an
    independent, fresh reconstruction attempt.
    """
    classification = {"home": {}, "away": {}}  # player_name -> "original" | "later"
    discovered = {"home": set(), "away": set()}

    def classify(player, side, as_what):
        """No-op if this player already has a classification for this
        period -- their FIRST mention (within whichever stage) is the
        only one that counts."""
        if player in classification[side]:
            return
        classification[side][player] = as_what
        if as_what == "original":
            if len(discovered[side]) < 5:
                discovered[side].add(player)
                if verbose:
                    print(f"    [debug] discovery: {player!r} ({side}) classified ORIGINAL")
            elif verbose:
                print(f"    [debug] discovery: {side} already has 5 confirmed -- ignoring {player!r}")
        elif verbose:
            print(f"    [debug] discovery: {player!r} ({side}) classified LATER ENTRANT")

    # STAGE 1: substitutions only, in their own order -- deliberately
    # ignores every interleaved non-substitution action.
    for action in period_actions:
        if str(action.get("actionType", "")) != "Substitution":
            continue
        description = str(action.get("description", ""))
        match = SUB_RE.search(description)
        if not match:
            continue

        out_person_id = action.get("personId")
        out_hit = id_resolver.get(int(out_person_id)) if out_person_id is not None else None

        in_full, in_side = _resolve_name(
            match.group("in_name"), roster_name_resolver,
            first_name_resolver=roster_first_name_resolver,
            restrict_to_side=(out_hit[1] if out_hit is not None else None),
            verbose=verbose,
        )

        if verbose:
            out_desc = out_hit[0] if out_hit is not None else f"<unresolved id {out_person_id!r}>"
            print(
                f"    [debug] discovery sub: {description!r}  "
                f"OUT(by id)={out_desc!r}  IN(by text)={in_full!r}"
            )

        if out_hit is not None:
            classify(out_hit[0], out_hit[1], "original")
        if in_full is not None and in_side is not None:
            classify(in_full, in_side, "later")

    # STAGE 2 -- PASS A: every other action type, for whoever STAGE 1
    # never mentioned in either direction, using ONLY the action's own
    # personId -- exact id_resolver matches, the reliable evidence.
    # This pass runs to completion, over every action, before ANY
    # backup evidence (pass B below) is looked at.
    shooter_side_by_action = {}
    for i, action in enumerate(period_actions):
        if str(action.get("actionType", "")) == "Substitution":
            continue
        person_id = action.get("personId")
        hit = id_resolver.get(int(person_id)) if person_id is not None else None
        if hit is not None:
            full_name, side = hit
            shooter_side_by_action[i] = side
            classify(full_name, side, "original")

    # STAGE 2 -- PASS B: BACKUP evidence only, used only to fill
    # whatever a side is still missing after pass A's reliable personId
    # evidence has been fully applied -- never processed early enough
    # to take a slot a later, solid personId hit should have gotten.
    # (classify()'s per-side cap at 5 already stops a full side from
    # accepting more, but that alone isn't enough: if this evidence
    # were read in the same left-to-right pass as personId hits, a
    # fuzzy-resolved name from an EARLIER action could fill a slot that
    # a real personId match from a LATER action should have claimed.
    # Running this as its own, later pass over the whole period removes
    # that ordering risk entirely -- pass A always gets first claim on
    # every one of a side's 5 slots.)
    #
    # Two kinds of on-court evidence only ever appear as free text, with
    # no personId to resolve exactly:
    #   1. A jump ball's two participants AND the tip recipient
    #      ("Jump Ball A vs. B: Tip to C"). Confirmed real case: Kornet
    #      won a period-opening tip but was never separately confirmed
    #      on the floor, so his side fell one player short and was
    #      abandoned even though winning the tip proves he was there.
    #      Resolved the same way _parse_jump_ball resolves p1/p2 --
    #      they're always on opposing teams, so whichever name resolves
    #      unambiguously first restricts the other -- except here
    #      on-court membership can't be required as a check, since
    #      on-court membership is exactly what this stage is building.
    #   2. A shot's assisting player ("(Name N AST)"). Confirmed real
    #      case: Alvarado's only appearance in a period was via an
    #      assist, so without parsing it out he was never counted as
    #      evidence. An assist is always credited to a TEAMMATE of the
    #      shooter, so once the shooter's own side is known from their
    #      resolved personId (from pass A, above), the assist name is
    #      safely restricted to that same side -- that follows from
    #      what an assist is, not a guess.
    if any(len(discovered[side]) < 5 for side in ("home", "away")):
        for i, action in enumerate(period_actions):
            if str(action.get("actionType", "")) == "Substitution":
                continue
            if discovered["home"] and discovered["away"] and len(discovered["home"]) == 5 and len(discovered["away"]) == 5:
                break

            action_type = str(action.get("actionType", ""))
            description = str(action.get("description", ""))

            if action_type == "Jump Ball":
                jb_match = JUMP_BALL_RE.search(description)
                if jb_match:
                    raw_p1, raw_p2, raw_p3 = jb_match.group("p1"), jb_match.group("p2"), jb_match.group("p3")
                    p1_full, p1_side = _resolve_name(
                        raw_p1, roster_name_resolver,
                        first_name_resolver=roster_first_name_resolver, verbose=verbose,
                    )
                    p2_full, p2_side = _resolve_name(
                        raw_p2, roster_name_resolver,
                        first_name_resolver=roster_first_name_resolver, verbose=verbose,
                    )
                    opposite = {"home": "away", "away": "home"}
                    if p1_full is None and p2_full is not None:
                        p1_full, p1_side = _resolve_name(
                            raw_p1, roster_name_resolver,
                            first_name_resolver=roster_first_name_resolver,
                            restrict_to_side=opposite.get(p2_side), verbose=verbose,
                        )
                    elif p2_full is None and p1_full is not None:
                        p2_full, p2_side = _resolve_name(
                            raw_p2, roster_name_resolver,
                            first_name_resolver=roster_first_name_resolver,
                            restrict_to_side=opposite.get(p1_side), verbose=verbose,
                        )
                    p3_full, p3_side = _resolve_name(
                        raw_p3, roster_name_resolver,
                        first_name_resolver=roster_first_name_resolver, verbose=verbose,
                    )
                    for full_name, side in ((p1_full, p1_side), (p2_full, p2_side), (p3_full, p3_side)):
                        if full_name is not None and side is not None:
                            classify(full_name, side, "original")

            assist_match = _ASSIST_RE.search(description)
            shooter_side = shooter_side_by_action.get(i)
            if assist_match and shooter_side is not None:
                assist_full, assist_side = _resolve_name(
                    assist_match.group(1), roster_name_resolver,
                    first_name_resolver=roster_first_name_resolver,
                    restrict_to_side=shooter_side, verbose=verbose,
                )
                if assist_full is not None:
                    classify(assist_full, assist_side, "original")

    for side in ("home", "away"):
        found = discovered[side]
        if len(found) == 5:
            tracker.on_court[side] = list(found)
            tracker.trusted[side] = True
            tracker.untrusted_logged[side] = False
            if verbose:
                print(f"  [debug] period-start reconstructed for {side}: {tracker.on_court[side]}")
        else:
            tracker.mark_untrusted(
                side,
                f"could only confirm {len(found)}/5 players on court at period start: {sorted(found)}",
                verbose,
            )


def _group_by_period(pbp_df, verbose=False):
    """Splits an already period+actionNumber-sorted play-by-play
    DataFrame into (period_number, [action, action, ...]) groups,
    preserving order. Warns (rather than silently mis-grouping) if a
    period value reappears non-contiguously -- that would mean the
    upstream sort didn't actually make same-period rows contiguous,
    e.g. if actionNumber turned out not to be reliably orderable."""
    groups = []
    seen_periods = set()
    current_period, current_actions = None, []
    for _, action in pbp_df.iterrows():
        period = action.get("period")
        if period != current_period:
            if current_actions:
                groups.append((current_period, current_actions))
            if period in seen_periods and verbose:
                print(
                    f"  [warn] period {period!r} reappeared non-contiguously -- "
                    f"rows may be out of order; period-start reconstruction for "
                    f"this period may be unreliable"
                )
            seen_periods.add(period)
            current_period, current_actions = period, []
        current_actions.append(action)
    if current_actions:
        groups.append((current_period, current_actions))
    return groups


def scrape_game(game_id, data_dir=".", verbose=False):
    """
    Scrapes one game and writes <data_dir>/<game_id>.csv in the column
    format readCSV.py expects, with LIVE on-court lineups per shot --
    tracked via in-period substitutions, AND with each period 2+'s
    opening five reconstructed from evidence (see
    _reconstruct_period_start), since NBA doesn't log between-period
    substitutions at all. Returns the output file path.
    """
    game_id_str = str(game_id).zfill(10)
    fileName = str(game_id)

    (
        home_abbrev, away_abbrev, home_starters, away_starters,
        roster_name_resolver, roster_first_name_resolver, id_resolver,
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
        #
        # actionNumber is ALSO not reliably chronological within a period
        # (confirmed real case, NYK@DET Q2: "SUB: Hart FOR Anunoby" at
        # 9:12 had actionNumber 283, but "SUB: Anunoby FOR Alvarado" at
        # 7:31 had 249 -- backwards; some blocks look replayed out of
        # order). So within a period, sort by game clock DESCENDING (more
        # time remaining = earlier), with actionNumber only as the
        # tiebreaker for rows sharing an identical clock reading. If any
        # clock can't be parsed, fall back to the old period/actionNumber
        # sort rather than sorting on partial information.
        clock_seconds = pbp_df["clock"].map(_parse_clock_seconds) if "clock" in pbp_df.columns else None
        if clock_seconds is not None and clock_seconds.notna().all():
            pbp_df = pbp_df.assign(_clock_seconds=clock_seconds.astype(float))
            pbp_df = pbp_df.sort_values(
                ["period", "_clock_seconds", "actionNumber"],
                ascending=[True, False, True],
                kind="mergesort",
            ).drop(columns="_clock_seconds").reset_index(drop=True)
        else:
            if verbose:
                print("  [warn] missing/unparseable clock values -- sorting by period/actionNumber only")
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
                    parsed = _parse_jump_ball(
                        description, roster_name_resolver, roster_first_name_resolver, tracker, verbose
                    )
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
    START_GAME_ID = 22600132 #AND 22500001 458 521 637 955 22501029 42400223
    END_GAME_ID = 22600150
    DATA_DIR = "2026"

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
