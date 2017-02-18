import * as React from "react";
import DeckTile from "./DeckTile";
import Pager from "./Pager";
import {DeckObj} from "../interfaces";

interface DeckListState {
	page: number;
}

interface DeckListProps extends React.ClassAttributes<DeckList> {
	decks: DeckObj[];
	pageSize: number;
	hideTopPager?: boolean;
}

export default class DeckList extends React.Component<DeckListProps, DeckListState> {
	constructor(props: DeckListProps, state: DeckListState) {
		super(props, state);
		this.state = {
			page: 0,
		}
	}

	componentWillReceiveProps(nextProps: DeckListProps) {
		if (nextProps.decks !== this.props.decks
			|| nextProps.pageSize !== this.props.pageSize) {
			this.setState({page: 0});
		}
	}

	render(): JSX.Element {
		const pageOffset = this.state.page * this.props.pageSize;
		const nextPageOffset = pageOffset + this.props.pageSize;
		const deckCount = this.props.decks.length;

		const deckTiles = [];
		const visibleDecks = this.props.decks.slice(pageOffset, nextPageOffset)
		visibleDecks.forEach(deck => {
			deckTiles.push(
				<DeckTile
					cards={deck.cards}
					deckId={deck.deckId}
					playerClass={deck.playerClass}
					numGames={deck.numGames}
					winrate={deck.winrate}
				/>
			);
		});
		
		let next = null;
		if (deckCount > nextPageOffset) {
			next = () => this.setState({page: this.state.page + 1});
		}

		let prev = null;
		if (this.state.page > 0) {
			prev = () => this.setState({page: this.state.page - 1});
		}
		
		const min = pageOffset + 1;
		const max = Math.min(pageOffset + this.props.pageSize, deckCount);
		const pager = (
			<div className="paging pull-right">
				<span>{min + " - " + max + " out of  " + deckCount}</span>
				<Pager previous={prev} next={next} />
			</div>
		);
		return (
			<div className="deck-list">
				{!this.props.hideTopPager && pager}
				<div className="clearfix" />
				<div className="row header-row">
					<div className="col-lg-2 col-md-2">
						Deck
					</div>
					<div className="col-lg-1 col-md-1">
						Winrate
					</div>
					<div className="col-lg-1 col-md-1">
						Mana
					</div>
					<div className="col-lg-8 col-md-8">
						Cards
					</div>
				</div>
				<ul>
					{deckTiles}
				</ul>
				{pager}
			</div>
		);
	}
}
