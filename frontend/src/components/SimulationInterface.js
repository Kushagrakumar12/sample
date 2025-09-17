import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Button,
  Card,
  CardContent,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Alert,
  LinearProgress,
  Chip
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Refresh,
  Save,
  Assessment
} from '@mui/icons-material';

function SimulationInterface() {
  const [isRunning, setIsRunning] = useState(false);
  const [scenario, setScenario] = useState({
    name: 'Default Scenario',
    duration: 4,
    disruptions: [],
    weatherConditions: 'normal',
    trafficLevel: 'medium'
  });
  const [results, setResults] = useState(null);
  const [progress, setProgress] = useState(0);

  const handleRunSimulation = async () => {
    setIsRunning(true);
    setProgress(0);
    setResults(null);

    // Simulate progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsRunning(false);
          
          // Generate mock results
          setResults({
            totalTrains: 25,
            onTimePerformance: 89.2,
            averageDelay: 4.3,
            conflictsDetected: 3,
            conflictsResolved: 3,
            fuelSaved: 12.5,
            passengerSatisfaction: 4.2,
            recommendations: [
              'Increase buffer time on Track A during peak hours',
              'Consider adding express service on high-demand route',
              'Optimize signal timing at Junction 3'
            ]
          });
          
          return 100;
        }
        return prev + Math.random() * 10;
      });
    }, 500);
  };

  const handleStopSimulation = () => {
    setIsRunning(false);
    setProgress(0);
  };

  const scenarios = [
    { name: 'Normal Operations', description: 'Standard traffic conditions' },
    { name: 'Peak Hour Rush', description: 'Heavy traffic during rush hour' },
    { name: 'Weather Disruption', description: 'Severe weather conditions' },
    { name: 'Signal Failure', description: 'Major signal system failure' },
    { name: 'Track Maintenance', description: 'Scheduled maintenance windows' }
  ];

  const disruptions = [
    { type: 'delay', label: 'Train Delay', severity: 'medium' },
    { type: 'breakdown', label: 'Equipment Failure', severity: 'high' },
    { type: 'weather', label: 'Weather Alert', severity: 'low' },
    { type: 'maintenance', label: 'Track Maintenance', severity: 'medium' }
  ];

  return (
    <Box>
      <Typography variant="h4" component="h1" fontWeight="bold" sx={{ mb: 3 }}>
        Simulation Interface
      </Typography>

      <Grid container spacing={3}>
        {/* Scenario Configuration */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Scenario Configuration
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                label="Scenario Name"
                value={scenario.name}
                onChange={(e) => setScenario({ ...scenario, name: e.target.value })}
                fullWidth
              />

              <FormControl fullWidth>
                <InputLabel>Predefined Scenarios</InputLabel>
                <Select
                  value=""
                  label="Predefined Scenarios"
                  onChange={(e) => {
                    const selected = scenarios.find(s => s.name === e.target.value);
                    if (selected) {
                      setScenario({ ...scenario, name: selected.name });
                    }
                  }}
                >
                  {scenarios.map((s) => (
                    <MenuItem key={s.name} value={s.name}>
                      {s.name} - {s.description}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Box>
                <Typography gutterBottom>
                  Simulation Duration: {scenario.duration} hours
                </Typography>
                <Slider
                  value={scenario.duration}
                  onChange={(e, value) => setScenario({ ...scenario, duration: value })}
                  min={1}
                  max={24}
                  step={1}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>

              <FormControl fullWidth>
                <InputLabel>Weather Conditions</InputLabel>
                <Select
                  value={scenario.weatherConditions}
                  onChange={(e) => setScenario({ ...scenario, weatherConditions: e.target.value })}
                  label="Weather Conditions"
                >
                  <MenuItem value="clear">Clear</MenuItem>
                  <MenuItem value="normal">Normal</MenuItem>
                  <MenuItem value="rain">Light Rain</MenuItem>
                  <MenuItem value="heavy_rain">Heavy Rain</MenuItem>
                  <MenuItem value="snow">Snow</MenuItem>
                  <MenuItem value="fog">Fog</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth>
                <InputLabel>Traffic Level</InputLabel>
                <Select
                  value={scenario.trafficLevel}
                  onChange={(e) => setScenario({ ...scenario, trafficLevel: e.target.value })}
                  label="Traffic Level"
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="peak">Peak</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </Paper>
        </Grid>

        {/* Disruption Modeling */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Disruption Modeling
            </Typography>

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Add disruptions to test system resilience
              </Typography>
              
              {disruptions.map((disruption) => (
                <Card key={disruption.type} sx={{ mb: 1, p: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="body2" fontWeight="bold">
                        {disruption.label}
                      </Typography>
                      <Chip 
                        label={disruption.severity} 
                        size="small" 
                        color={
                          disruption.severity === 'high' ? 'error' :
                          disruption.severity === 'medium' ? 'warning' : 'info'
                        }
                      />
                    </Box>
                    <Button size="small" variant="outlined">
                      Add
                    </Button>
                  </Box>
                </Card>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Simulation Controls */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Simulation Controls
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Button
                variant="contained"
                startIcon={<PlayArrow />}
                onClick={handleRunSimulation}
                disabled={isRunning}
              >
                Run Simulation
              </Button>
              
              <Button
                variant="outlined"
                startIcon={<Stop />}
                onClick={handleStopSimulation}
                disabled={!isRunning}
              >
                Stop
              </Button>
              
              <Button
                variant="outlined"
                startIcon={<Refresh />}
                onClick={() => setResults(null)}
              >
                Reset
              </Button>
              
              <Button
                variant="outlined"
                startIcon={<Save />}
                disabled={!results}
              >
                Save Results
              </Button>
            </Box>

            {isRunning && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Simulation Progress: {Math.round(progress)}%
                </Typography>
                <LinearProgress variant="determinate" value={progress} />
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Results */}
        {results && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Simulation Results
              </Typography>

              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6} md={3}>
                  <Card>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography color="textSecondary" gutterBottom>
                        Total Trains
                      </Typography>
                      <Typography variant="h4" component="div">
                        {results.totalTrains}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={6} md={3}>
                  <Card>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography color="textSecondary" gutterBottom>
                        On-Time Performance
                      </Typography>
                      <Typography variant="h4" component="div" color="success.main">
                        {results.onTimePerformance}%
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={6} md={3}>
                  <Card>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography color="textSecondary" gutterBottom>
                        Average Delay
                      </Typography>
                      <Typography variant="h4" component="div" color="warning.main">
                        {results.averageDelay}min
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={6} md={3}>
                  <Card>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography color="textSecondary" gutterBottom>
                        Conflicts Resolved
                      </Typography>
                      <Typography variant="h4" component="div" color="info.main">
                        {results.conflictsResolved}/{results.conflictsDetected}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                  AI Recommendations
                </Typography>
                {results.recommendations.map((rec, index) => (
                  <Typography key={index} variant="body2">
                    • {rec}
                  </Typography>
                ))}
              </Alert>

              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button variant="contained" startIcon={<Assessment />}>
                  Detailed Analysis
                </Button>
                <Button variant="outlined">
                  Compare Scenarios
                </Button>
                <Button variant="outlined">
                  Export Report
                </Button>
              </Box>
            </Paper>
          </Grid>
        )}
      </Grid>
    </Box>
  );
}

export default SimulationInterface;