"""
diagnose_boxscore.py -- run this on your machine (has live NBA API access)
and paste me the full printed output. It doesn't scrape or write anything,
just shows exactly what BoxScoreTraditionalV3 actually returns for one
game, so I can see real column values instead of guessing at them.

Usage:
    python diagnose_boxscore.py
"""
import pandas as pd
from nba_api.stats.endpoints import boxscoretraditionalv3, boxscoresummaryv2, playbyplayv3

GAME_ID = "0022500789"  # the OKC vs MIL game from your screenshot

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

print(f"=== BoxScoreTraditionalV3(game_id={GAME_ID!r}) ===\n")
box = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=GAME_ID)
pbp = playbyplayv3.PlayByPlayV3(game_id=GAME_ID)
print(pbp.play_by_play.get_data_frame())
print("Attributes available on the response object:")
print([a for a in dir(box) if not a.startswith("_")])
print()

player_df = box.player_stats.get_data_frame()
print(f"player_stats shape: {player_df.shape}")
print(f"player_stats columns: {list(player_df.columns)}\n")

cols_to_show = [c for c in ["teamId", "teamTricode", "personId", "firstName",
                             "familyName", "position", "comment", "minutes"]
                if c in player_df.columns]
print("Full player_stats table (relevant columns):")
print(player_df[cols_to_show].to_string())
print()

print("Row count per teamId:")
print(player_df["teamId"].value_counts())
print()

print("=== BoxScoreSummaryV2(game_id={!r}) ===".format(GAME_ID))
summary = boxscoresummaryv2.BoxScoreSummaryV2(game_id=GAME_ID)
game_summary_df = summary.game_summary.get_data_frame()
print(game_summary_df[["HOME_TEAM_ID", "VISITOR_TEAM_ID"]].to_string())
