import * as React from "react";
import {
	VictoryAxis, VictoryArea, VictoryChart, VictoryContainer, VictoryLabel,
	VictoryLine, VictoryVoronoiTooltip, VictoryTooltip
} from "victory";
import {ChartSeries} from "../../interfaces";
import {getChartMetaData} from "../../helpers";

interface WinrateByTurnLineChartProps {
	series: ChartSeries;
	widthRatio?: number;
}

export default class WinrateByTurnLineChart extends React.Component<WinrateByTurnLineChartProps, any> {
	render(): JSX.Element {
		const width = 150 * (this.props.widthRatio || 3);
		let content = null;

		//TODO: use this.props.series instead of this.mockSeries
		if (this.mockSeries) {
			const metaData = getChartMetaData(this.mockSeries.data);

			const tooltip = <VictoryTooltip
				cornerRadius={0}
				pointerLength={0}
				padding={1}
				dx={d => d.x > metaData.xCenter ? -40 : 40}
				dy={-12}
				flyoutStyle={{
					stroke: "gray",
					fill: "rgba(255, 255, 255, 0.85)"
				}}
			/>;

			content = [
				<defs>
					<linearGradient id="turn-played-gradient" x1="50%" y1="100%" x2="50%" y2="0%">
						<stop stopColor="rgba(255, 255, 255, 0)" offset={0}/>
						<stop stopColor="rgba(0, 128, 255, 0.6)" offset={1}/>
					</linearGradient>
				</defs>,
				<VictoryChart
					height={150}
					width={width}
					containerComponent={<VictoryContainer title={""}/>}
					domain={{x: metaData.xDomain, y: [0, metaData.yDomain[1]]}}
					domainPadding={{x: 0, y: 10}}
					padding={{left: 40, top: 30, right: 20, bottom: 30}}
					>
					<VictoryAxis
						tickFormat={tick => "Turn " + tick}
						style={{axisLabel: {fontSize: 8}, tickLabels: {fontSize: 8}, grid: {stroke: "gray"}, axis: {visibility: "hidden"}}}
					/>
					<VictoryAxis
						dependentAxis
						axisLabelComponent={<VictoryLabel dx={10} />}
						tickValues={[metaData.yCenter]}
						tickFormat={tick => tick + " %"}
						style={{axisLabel: {fontSize: 8} ,tickLabels: {fontSize: 8}, grid: {stroke: d => d === metaData.yCenter ? "gray" : "transparent"}, axis: {visibility: "hidden"}}}
					/>
					<VictoryArea
						data={this.mockSeries.data.map(p => {return {x: p.x, y: p.y, y0: 0}})}
						style={{data: {fill: "url(#turn-played-gradient)"}}}
						interpolation="step"
					/>
					<VictoryLine
						data={this.mockSeries.data}
						interpolation="step"
						style={{data: {strokeWidth: 1}}}
					/>
					<VictoryVoronoiTooltip
						data={this.mockSeries.data.map(d => {return {x: d.x, y: metaData.yCenter, yValue: d.y}})}
						labels={d => "Turn " + d.x + "\n" + d.yValue + "%"}
						labelComponent={tooltip}
						style={{
							labels: {fontSize: 6, padding: 5}
						}}
					/>
				</VictoryChart>
			];
		}
		else {
			content = <VictoryLabel text={"Loading..."} style={{fontSize: 14}} textAnchor="middle" verticalAnchor="middle" x={width/2} y={75}/>
		}

		return (
			<svg viewBox={"0 0 " + width + " 150"}>
				{content}
				<VictoryLabel text={"Turn played %"} style={{fontSize: 10}} textAnchor="start" verticalAnchor="start" x={0} y={10}/>
			</svg>
		);
	}

	readonly mockSeries = {
		data: [
			{x: 5, y: 50},
			{x: 6, y: 6},
			{x: 7, y: 24},
			{x: 8, y: 13},
			{x: 9, y: 22},
			{x: 10, y: 10},
			{x: 11, y: 8},
			{x: 12, y: 7},
			{x: 13, y: 2},
			{x: 14, y: 5},
			{x: 15, y: 5},
			{x: 16, y: 5},
		],
		name: ""
	}
}
