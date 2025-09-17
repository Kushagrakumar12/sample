import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  Grid,
  Card,
  CardContent
} from '@mui/material';
import {
  Schedule,
  CheckCircle,
  Warning,
  Cancel,
  PlayArrow
} from '@mui/icons-material';
import { apiService } from '../services/apiService';

function ScheduleView() {
  const [schedules, setSchedules] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSchedules();
    loadAnalytics();
  }, []);

  const loadSchedules = async () => {
    try {
      const response = await apiService.getSchedules();
      setSchedules(response.data || []);
    } catch (error) {
      console.error('Error loading schedules:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await apiService.getPerformanceAnalytics();
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'running':
        return <PlayArrow color="info" />;
      case 'delayed':
        return <Warning color="warning" />;
      case 'cancelled':
        return <Cancel color="error" />;
      default:
        return <Schedule color="action" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'info';
      case 'delayed':
        return 'warning';
      case 'cancelled':
        return 'error';
      case 'scheduled':
        return 'primary';
      default:
        return 'default';
    }
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const getDelayColor = (delayMinutes) => {
    if (delayMinutes <= 0) return 'success';
    if (delayMinutes <= 5) return 'warning';
    return 'error';
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" fontWeight="bold" sx={{ mb: 3 }}>
        Schedule Management
      </Typography>

      {/* Analytics Cards */}
      {analytics && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Total Trips
                </Typography>
                <Typography variant="h4" component="div" color="primary">
                  {analytics.total_trips}
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
                <Typography variant="h4" component="div" color="success.main">
                  {analytics.on_time_percentage}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Average Delay
                </Typography>
                <Typography variant="h4" component="div" color="warning.main">
                  {analytics.average_delay_minutes}min
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Worst Delay
                </Typography>
                <Typography variant="h4" component="div" color="error.main">
                  {analytics.worst_delay_minutes}min
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Controls */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <Button variant="contained" onClick={loadSchedules}>
          Refresh Schedules
        </Button>
        <Button variant="outlined">
          Optimize All
        </Button>
        <Button variant="outlined">
          Export Data
        </Button>
      </Box>

      {/* Schedules Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Status</TableCell>
              <TableCell>Train</TableCell>
              <TableCell>Route</TableCell>
              <TableCell>Scheduled Departure</TableCell>
              <TableCell>Scheduled Arrival</TableCell>
              <TableCell>Actual Times</TableCell>
              <TableCell>Delay</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {schedules.map((schedule) => (
              <TableRow key={schedule.id}>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getStatusIcon(schedule.status)}
                    <Chip
                      label={schedule.status}
                      size="small"
                      color={getStatusColor(schedule.status)}
                    />
                  </Box>
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2" fontWeight="bold">
                    Train {schedule.train_id}
                  </Typography>
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2">
                    Track {schedule.track_id}
                  </Typography>
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2">
                    {formatDateTime(schedule.scheduled_departure)}
                  </Typography>
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2">
                    {formatDateTime(schedule.scheduled_arrival)}
                  </Typography>
                </TableCell>
                
                <TableCell>
                  <Box>
                    {schedule.actual_departure && (
                      <Typography variant="caption" display="block">
                        Dep: {formatDateTime(schedule.actual_departure)}
                      </Typography>
                    )}
                    {schedule.actual_arrival && (
                      <Typography variant="caption" display="block">
                        Arr: {formatDateTime(schedule.actual_arrival)}
                      </Typography>
                    )}
                    {!schedule.actual_departure && !schedule.actual_arrival && (
                      <Typography variant="caption" color="text.secondary">
                        Pending
                      </Typography>
                    )}
                  </Box>
                </TableCell>
                
                <TableCell>
                  {schedule.delay_minutes !== 0 && (
                    <Chip
                      label={`${schedule.delay_minutes > 0 ? '+' : ''}${schedule.delay_minutes}min`}
                      size="small"
                      color={getDelayColor(schedule.delay_minutes)}
                      variant={schedule.delay_minutes <= 0 ? "outlined" : "filled"}
                    />
                  )}
                </TableCell>
                
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {schedule.status === 'scheduled' && (
                      <Button size="small" variant="outlined">
                        Modify
                      </Button>
                    )}
                    {schedule.status === 'running' && (
                      <Button size="small" variant="outlined" color="warning">
                        Track
                      </Button>
                    )}
                    <Button size="small" variant="text">
                      Details
                    </Button>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {schedules.length === 0 && !loading && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="text.secondary">
            No schedules found. Create some train schedules to get started.
          </Typography>
        </Box>
      )}
    </Box>
  );
}

export default ScheduleView;