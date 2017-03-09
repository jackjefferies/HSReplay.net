import * as React from "react";
import {
	VictoryAxis, VictoryArea, VictoryChart, VictoryContainer, VictoryLabel,
	VictoryLine, VictoryVoronoiTooltip, VictoryTooltip
} from "victory";
import {RenderData} from "../../interfaces";
import {getChartMetaData, toTimeSeries, toDynamicFixed, sliceZeros} from "../../helpers";
import WinLossGradient from "./gradients/WinLossGradient";
import moment from "moment";

interface WinrateLineChartProps extends React.ClassAttributes<WinrateLineChart> {
	renderData: RenderData;
	title?: string;
	widthRatio?: number;
}

export default class WinrateLineChart extends React.Component<WinrateLineChartProps, any> {
	render(): JSX.Element {
		const width = 150 * (this.props.widthRatio || 3);
		let content = null;

		if(this.props.renderData === "loading") {
			content = <VictoryLabel text={"Loading..."} style={{fontSize: 14}} textAnchor="middle" verticalAnchor="middle" x={width/2} y={75}/>
		}
		else if (this.props.renderData === "error") {
			content = <VictoryLabel text={"Please check back later"} style={{fontSize: 14}} textAnchor="middle" verticalAnchor="middle" x={width/2} y={75}/>
		}
		else if (this.props.renderData) {
			const series = toTimeSeries(this.props.renderData.series.find(x => x.name === "winrates_over_time") || this.props.renderData.series[0]);
			const metadata = getChartMetaData(series.data, 50, true, 10);

			const tooltip = (
				<VictoryTooltip
					cornerRadius={0}
					pointerLength={0}
					padding={1}
					dx={d => d.x > metadata.xCenter ? -40 : 40}
					dy={-12}
					flyoutStyle={{
						stroke: "gray",
						fill: "rgba(255, 255, 255, 0.85)"
					}}
				/>
			);
			
			const minAbove50 = metadata.yMinMax[0].y > 50;
			const maxBelow50 = metadata.yMinMax[1].y < 50;
			const isMinTick = (tick: number) => tick === metadata.yDomain[0];
			const isMaxTick = (tick: number) => tick === metadata.yDomain[1];

			const yTicks = [50];
			metadata.yDomain.forEach(value => yTicks.indexOf(value) === -1 && yTicks.push(value));

			content = [
				<defs>
					<WinLossGradient id="winrate-by-time-gradient" metadata={metadata} />
				</defs>,
				<VictoryChart
					height={150}
					width={width}
					containerComponent={<VictoryContainer title={""}/>}
					domainPadding={{x: 0, y: 10}}
					padding={{left: 40, top: 30, right: 20, bottom: 30}}
					domain={{x: metadata.xDomain, y: metadata.yDomain}}
					>
					<VictoryAxis
						scale="time"
						tickValues={metadata.seasonTicks}
						tickFormat={tick => moment(tick).add(1, "day").format("MMMM")}
						style={{axisLabel: {fontSize: 8}, tickLabels: {fontSize: 8}, grid: {stroke: "gray"}, axis: {visibility: "hidden"}}}
					/>
					<VictoryAxis
						dependentAxis
						axisLabelComponent={<VictoryLabel dx={10} />}
						tickValues={[50].concat(metadata.yDomain)}
						tickFormat={tick => {
							if (tick === 50) {
								return "50%";
							}
							if (minAbove50 && isMinTick(tick)) {
								return "";
							}
							if (maxBelow50 && isMaxTick(tick)) {
								return ""
							}
							return metadata.toFixed(tick) + "%"
						}}
						style={{
							axisLabel: {fontSize: 8},
							tickLabels: {fontSize: 8},
							grid: {stroke: tick => tick === 50 ? "gray" : (minAbove50 && isMinTick(tick) || maxBelow50 && isMaxTick(tick) ? "transparent" : "lightgray")},
							axis: {visibility: "hidden"}
						}}
					/>
					<VictoryArea
						data={series.data.map((p) => {return {x: p.x, y: p.y, _y0: 50}})}
						style={{data: {fill: "url(#winrate-by-time-gradient)"}}}
						interpolation="monotoneX"
					/>
					<VictoryLine
						data={series.data}
						interpolation="monotoneX"
						style={{data: {strokeWidth: 1}}}
					/>
					<VictoryVoronoiTooltip
						data={series.data}
						labels={d => moment(d.x).format("YYYY-MM-DD") + "\n" + sliceZeros(toDynamicFixed(d.y, 2)) + "%"}
						labelComponent={tooltip}
						style={{
							labels: {fontSize: 6, padding: 5}
						}}
					/>
				</VictoryChart>
			];
		}

		return (
			<svg viewBox={"0 0 " + width + " 150"}>
				{content}
				<VictoryLabel text={this.props.title || "Winrate - over time"} style={{fontSize: 10}} textAnchor="start" verticalAnchor="start" x={0} y={10}/>
			</svg>
		);
	}
}
