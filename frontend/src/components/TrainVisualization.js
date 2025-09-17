import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { Box, Typography } from '@mui/material';

export function TrainVisualization({ trains = [] }) {
  const svgRef = useRef();

  useEffect(() => {
    if (!trains.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear previous content

    const width = 800;
    const height = 400;
    const margin = { top: 20, right: 20, bottom: 40, left: 40 };

    // Create scales
    const xScale = d3.scaleLinear()
      .domain([0, 100]) // Assuming 100km max track length
      .range([margin.left, width - margin.right]);

    const yScale = d3.scaleBand()
      .domain(['Track A', 'Track B', 'Track C']) // Sample tracks
      .range([margin.top, height - margin.bottom])
      .padding(0.3);

    // Draw track lines
    const trackData = [
      { name: 'Track A', y: yScale('Track A') + yScale.bandwidth() / 2 },
      { name: 'Track B', y: yScale('Track B') + yScale.bandwidth() / 2 },
      { name: 'Track C', y: yScale('Track C') + yScale.bandwidth() / 2 }
    ];

    // Draw tracks
    svg.selectAll('.track-line')
      .data(trackData)
      .enter()
      .append('line')
      .attr('class', 'track-line')
      .attr('x1', margin.left)
      .attr('x2', width - margin.right)
      .attr('y1', d => d.y)
      .attr('y2', d => d.y)
      .attr('stroke', '#ccc')
      .attr('stroke-width', 8)
      .attr('stroke-linecap', 'round');

    // Draw stations
    const stations = [
      { name: 'Station A', x: xScale(0) },
      { name: 'Station B', x: xScale(50) },
      { name: 'Station C', x: xScale(100) }
    ];

    stations.forEach(station => {
      trackData.forEach(track => {
        svg.append('circle')
          .attr('cx', station.x)
          .attr('cy', track.y)
          .attr('r', 6)
          .attr('fill', '#2196f3')
          .attr('stroke', 'white')
          .attr('stroke-width', 2);
      });

      // Station labels
      svg.append('text')
        .attr('x', station.x)
        .attr('y', height - 10)
        .attr('text-anchor', 'middle')
        .attr('font-size', '12px')
        .attr('fill', '#666')
        .text(station.name);
    });

    // Draw trains
    const trainData = trains.map((train, index) => ({
      ...train,
      x: xScale(Math.random() * 100), // Random position for demo
      y: trackData[index % trackData.length].y,
      track: trackData[index % trackData.length].name
    }));

    const trainGroups = svg.selectAll('.train-group')
      .data(trainData)
      .enter()
      .append('g')
      .attr('class', 'train-group');

    // Train icons
    trainGroups.append('rect')
      .attr('x', d => d.x - 15)
      .attr('y', d => d.y - 8)
      .attr('width', 30)
      .attr('height', 16)
      .attr('rx', 4)
      .attr('fill', d => getTrainColor(d.train_type))
      .attr('stroke', 'white')
      .attr('stroke-width', 2);

    // Train labels
    trainGroups.append('text')
      .attr('x', d => d.x)
      .attr('y', d => d.y - 15)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('font-weight', 'bold')
      .attr('fill', '#333')
      .text(d => d.number || `T${d.id}`);

    // Speed indicators
    trainGroups.append('text')
      .attr('x', d => d.x)
      .attr('y', d => d.y + 25)
      .attr('text-anchor', 'middle')
      .attr('font-size', '9px')
      .attr('fill', '#666')
      .text(d => `${Math.round(Math.random() * 120)}km/h`);

    // Add legend
    const legend = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${width - 150}, 20)`);

    const legendData = [
      { type: 'passenger', color: '#4caf50', label: 'Passenger' },
      { type: 'freight', color: '#ff9800', label: 'Freight' },
      { type: 'express', color: '#2196f3', label: 'Express' }
    ];

    const legendItems = legend.selectAll('.legend-item')
      .data(legendData)
      .enter()
      .append('g')
      .attr('class', 'legend-item')
      .attr('transform', (d, i) => `translate(0, ${i * 20})`);

    legendItems.append('rect')
      .attr('width', 12)
      .attr('height', 12)
      .attr('fill', d => d.color);

    legendItems.append('text')
      .attr('x', 18)
      .attr('y', 9)
      .attr('font-size', '12px')
      .attr('fill', '#333')
      .text(d => d.label);

    // Add axes
    const xAxis = d3.axisBottom(xScale)
      .tickFormat(d => `${d}km`);

    svg.append('g')
      .attr('transform', `translate(0, ${height - margin.bottom})`)
      .call(xAxis);

    const yAxis = d3.axisLeft(yScale);

    svg.append('g')
      .attr('transform', `translate(${margin.left}, 0)`)
      .call(yAxis);

  }, [trains]);

  const getTrainColor = (trainType) => {
    switch (trainType) {
      case 'passenger': return '#4caf50';
      case 'freight': return '#ff9800';
      case 'express': return '#2196f3';
      case 'local': return '#9c27b0';
      default: return '#666';
    }
  };

  return (
    <Box>
      {trains.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="text.secondary">
            No train data available. Loading real-time positions...
          </Typography>
        </Box>
      ) : (
        <svg
          ref={svgRef}
          width="100%"
          height="400"
          viewBox="0 0 800 400"
          style={{ border: '1px solid #e0e0e0', borderRadius: '8px' }}
        />
      )}
    </Box>
  );
}