import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Alert,
  Chip,
  LinearProgress
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { TrainVisualization } from './TrainVisualization';
import { useWebSocket } from '../hooks/useWebSocket';
import { apiService } from '../services/apiService';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

function Dashboard() {
  const [systemMetrics, setSystemMetrics] = useState({
    activeTrains: 0,
    onTimePercentage: 0,
    activeConflicts: 0,
    systemHealth: 'operational'
  });
  const [trains, setTrains] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  const [loading, setLoading] = useState(true);

  const { socket, isConnected } = useWebSocket();

  useEffect(() => {
    loadDashboardData();

    // Set up real-time updates
    if (socket) {
      socket.on('system_status', handleSystemStatus);
      socket.on('train_update', handleTrainUpdate);
      socket.on('conflict_alert', handleConflictAlert);

      return () => {
        socket.off('system_status');
        socket.off('train_update');
        socket.off('conflict_alert');
      };
    }
  }, [socket]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load trains
      const trainsResponse = await apiService.getTrains();
      setTrains(trainsResponse.data || []);

      // Load conflicts
      const conflictsResponse = await apiService.detectConflicts();
      setConflicts(conflictsResponse.data || []);

      // Load performance analytics
      const analyticsResponse = await apiService.getPerformanceAnalytics();
      if (analyticsResponse.data) {
        setSystemMetrics(prev => ({
          ...prev,
          onTimePercentage: analyticsResponse.data.on_time_percentage || 0
        }));
      }

      // Generate sample performance data for charts
      const sampleData = generateSamplePerformanceData();
      setPerformanceData(sampleData);

    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSystemStatus = (data) => {
    setSystemMetrics(prev => ({
      ...prev,
      ...data.data
    }));
  };

  const handleTrainUpdate = (data) => {
    setTrains(prev => 
      prev.map(train => 
        train.id === data.data.train_id 
          ? { ...train, currentPosition: data.data }
          : train
      )
    );
  };

  const handleConflictAlert = (data) => {
    setConflicts(prev => [...prev, data.data]);
  };

  const generateSamplePerformanceData = () => {
    const hours = [];
    for (let i = 23; i >= 0; i--) {
      const hour = new Date();
      hour.setHours(hour.getHours() - i);
      hours.push({
        time: hour.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        onTime: Math.random() * 20 + 80,
        delayed: Math.random() * 15,
        cancelled: Math.random() * 5
      });
    }
    return hours;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'operational': return 'success';
      case 'warning': return 'warning';
      case 'critical': return 'error';
      default: return 'info';
    }
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>
          Loading dashboard...
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Railway Control Dashboard
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip
            label={isConnected ? 'Connected' : 'Disconnected'}
            color={isConnected ? 'success' : 'error'}
            variant="filled"
          />
          <Chip
            label={`System: ${systemMetrics.systemHealth}`}
            color={getStatusColor(systemMetrics.systemHealth)}
            variant="filled"
          />
        </Box>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="textSecondary" gutterBottom>
                Active Trains
              </Typography>
              <Typography variant="h3" component="div" color="primary">
                {systemMetrics.activeTrains || trains.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="textSecondary" gutterBottom>
                On-Time Performance
              </Typography>
              <Typography variant="h3" component="div" color="success.main">
                {Math.round(systemMetrics.onTimePercentage || 87.5)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="textSecondary" gutterBottom>
                Active Conflicts
              </Typography>
              <Typography variant="h3" component="div" color="warning.main">
                {conflicts.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="textSecondary" gutterBottom>
                System Load
              </Typography>
              <Typography variant="h3" component="div" color="info.main">
                76%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts */}
      {conflicts.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="h6">Active Conflicts Detected</Typography>
          {conflicts.slice(0, 3).map((conflict, index) => (
            <Typography key={index} variant="body2">
              • {conflict.message || `Conflict between trains ${conflict.train1_id} and ${conflict.train2_id}`}
            </Typography>
          ))}
        </Alert>
      )}

      {/* Main Content Grid */}
      <Grid container spacing={3}>
        {/* Train Visualization */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Real-Time Train Positions
            </Typography>
            <TrainVisualization trains={trains} />
          </Paper>
        </Grid>

        {/* Performance Chart */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              24-Hour Performance
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData.slice(-12)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="onTime" 
                  stroke="#4caf50" 
                  strokeWidth={2}
                  name="On Time (%)"
                />
                <Line 
                  type="monotone" 
                  dataKey="delayed" 
                  stroke="#ff9800" 
                  strokeWidth={2}
                  name="Delayed (%)"
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Train Status Distribution */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Train Status Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Running', value: 12, fill: '#4caf50' },
                    { name: 'Scheduled', value: 8, fill: '#2196f3' },
                    { name: 'Delayed', value: 3, fill: '#ff9800' },
                    { name: 'Maintenance', value: 2, fill: '#9e9e9e' }
                  ]}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {COLORS.map((color, index) => (
                    <Cell key={`cell-${index}`} fill={color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <Box sx={{ maxHeight: 250, overflow: 'auto' }}>
              {[
                { time: '14:32', event: 'Train T001 departed on schedule', type: 'success' },
                { time: '14:28', event: 'Conflict resolved between T002 and T003', type: 'warning' },
                { time: '14:25', event: 'Optimization completed for next 4 hours', type: 'info' },
                { time: '14:20', event: 'Train T005 arrived 3 minutes early', type: 'success' },
                { time: '14:15', event: 'Signal maintenance scheduled for Track A', type: 'info' }
              ].map((activity, index) => (
                <Box key={index} sx={{ mb: 1, p: 1, borderLeft: 3, borderColor: `${activity.type}.main` }}>
                  <Typography variant="body2" fontWeight="bold">
                    {activity.time}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {activity.event}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard;