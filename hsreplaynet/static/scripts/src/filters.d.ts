/**
 * RedshiftFilterEnums
 */

export const enum TimeRange {
	CURRENT_SEASON = "CURRENT_SEASON",
	LAST_1_DAY = "LAST_1_DAY",
	LAST_3_DAYS = "LAST_3_DAYS",
	LAST_7_DAYS = "LAST_7_DAYS",
	LAST_14_DAYS = "LAST_14_DAYS",
	LAST_30_DAYS = "LAST_30_DAYS",
	LAST_60_DAYS = "LAST_60_DAYS",
	PREVIOUS_SEASON = "PREVIOUS_SEASON",
	TWO_SEASONS_AGO = "TWO_SEASON_AGO",
	THREE_SEASONS_AGO = "THREE_SEASON_AGO",
	ALL_TIME = "ALL_TIME",
	ARENA_EVENT = "ARENA_EVENT",
	CURRENT_EXPANSION = "CURRENT_EXPANSION",
	CURRENT_PATCH = "CURRENT_PATCH",
}

export const enum RankRange {
	TOP_1000_LEGEND = "TOP_1000_LEGEND",
	LEGEND_ONLY = "LEGEND_ONLY",
	LEGEND_THROUGH_FIVE = "LEGEND_THROUGH_FIVE",
	LEGEND_THROUGH_TEN = "LEGEND_THROUGH_TEN",
	LEGEND_THROUGH_TWENTY = "LEGEND_THROUGH_TWENTY",
	ALL = "ALL",
}

export const enum PlayerExperience {
	ALL = "ALL",
	TEN_GAMES = "TEN_GAMES",
	TWENTY_GAMES = "TWENTY_GAMES",
	TWENTYFIVE_GAMES = "TWENTYFIVE_GAMES",
	FIFTY_GAMES = "FIFTY_GAMES",
}

export const enum PilotPerformance {
	ALL = "ALL",
	TOP_50TH_PERCENTILE = "TOP_50TH_PERCENTILE",
	TOP_20TH_PERCENTILE = "TOP_20TH_PERCENTILE",
}

export const enum PlayerInitiative {
	ALL = "ALL",
	FIRST = "FIRST",
	COIN = "COIN",
}
