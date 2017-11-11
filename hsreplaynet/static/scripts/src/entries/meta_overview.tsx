import * as React from "react";
import * as ReactDOM from "react-dom";
import CardData from "../CardData";
import UserData from "../UserData";
import Fragments from "../components/Fragments";
import MetaOverview from "../pages/MetaOverview";

UserData.create();
const tab = UserData.hasFeature("meta-tierlist") ? "tierlist" : "archetypes";

const render = (cardData: CardData) => {
	ReactDOM.render(
		<Fragments
			defaults={{
				gameType: "RANKED_STANDARD",
				popularitySortBy: "total",
				popularitySortDirection: "descending",
				rankRange: "ELEVEN_THROUGH_TWENTY",
				region: "ALL",
				sortBy: "popularity",
				sortDirection: "descending",
				tab,
				timeFrame: "LAST_7_DAYS",
			}}
			immutable={!UserData.isPremium() ? ["rankRange", "region", "timeFrame"] : null}
		>
			<MetaOverview
				cardData={cardData}
				region="ALL"
			/>
		</Fragments>,
		document.getElementById("meta-overview-container"),
	);
};

render(null);

new CardData().load(render);
