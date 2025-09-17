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
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Fab
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  LocationOn,
  Speed,
  Info
} from '@mui/icons-material';
import { apiService } from '../services/apiService';

function TrainManagement() {
  const [trains, setTrains] = useState([]);
  const [open, setOpen] = useState(false);
  const [editingTrain, setEditingTrain] = useState(null);
  const [formData, setFormData] = useState({
    number: '',
    name: '',
    train_type: 'passenger',
    priority: 'medium',
    max_speed_kmh: 120,
    length_meters: 200,
    capacity_passengers: 0,
    weight_tons: 100,
    operator: ''
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTrains();
  }, []);

  const loadTrains = async () => {
    try {
      const response = await apiService.getTrains();
      setTrains(response.data || []);
    } catch (error) {
      console.error('Error loading trains:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpen = (train = null) => {
    if (train) {
      setEditingTrain(train);
      setFormData({ ...train });
    } else {
      setEditingTrain(null);
      setFormData({
        number: '',
        name: '',
        train_type: 'passenger',
        priority: 'medium',
        max_speed_kmh: 120,
        length_meters: 200,
        capacity_passengers: 0,
        weight_tons: 100,
        operator: ''
      });
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setEditingTrain(null);
  };

  const handleSave = async () => {
    try {
      if (editingTrain) {
        await apiService.updateTrain(editingTrain.id, formData);
      } else {
        await apiService.createTrain(formData);
      }
      handleClose();
      loadTrains();
    } catch (error) {
      console.error('Error saving train:', error);
    }
  };

  const handleDelete = async (trainId) => {
    if (window.confirm('Are you sure you want to delete this train?')) {
      try {
        await apiService.deleteTrain(trainId);
        loadTrains();
      } catch (error) {
        console.error('Error deleting train:', error);
      }
    }
  };

  const getStatusColor = (isActive) => {
    return isActive ? 'success' : 'default';
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'default';
      default: return 'default';
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'passenger': return '#4caf50';
      case 'freight': return '#ff9800';
      case 'express': return '#2196f3';
      case 'local': return '#9c27b0';
      default: return '#666';
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Train Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpen()}
        >
          Add New Train
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Train Number</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Priority</TableCell>
              <TableCell>Max Speed</TableCell>
              <TableCell>Capacity</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {trains.map((train) => (
              <TableRow key={train.id}>
                <TableCell>
                  <Typography variant="body2" fontWeight="bold">
                    {train.number}
                  </Typography>
                </TableCell>
                <TableCell>{train.name}</TableCell>
                <TableCell>
                  <Chip
                    label={train.train_type}
                    size="small"
                    sx={{ 
                      backgroundColor: getTypeColor(train.train_type),
                      color: 'white'
                    }}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={train.priority}
                    size="small"
                    color={getPriorityColor(train.priority)}
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Speed fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                    {train.max_speed_kmh} km/h
                  </Box>
                </TableCell>
                <TableCell>
                  {train.train_type === 'passenger' 
                    ? `${train.capacity_passengers} passengers`
                    : `${train.weight_tons} tons`
                  }
                </TableCell>
                <TableCell>
                  <Chip
                    label={train.is_active ? 'Active' : 'Inactive'}
                    size="small"
                    color={getStatusColor(train.is_active)}
                  />
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => handleOpen(train)}
                    color="primary"
                  >
                    <Edit />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDelete(train.id)}
                    color="error"
                  >
                    <Delete />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="info"
                  >
                    <Info />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add/Edit Dialog */}
      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingTrain ? 'Edit Train' : 'Add New Train'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: 'repeat(2, 1fr)', mt: 1 }}>
            <TextField
              label="Train Number"
              value={formData.number}
              onChange={(e) => setFormData({ ...formData, number: e.target.value })}
              required
            />
            <TextField
              label="Train Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
            
            <FormControl>
              <InputLabel>Train Type</InputLabel>
              <Select
                value={formData.train_type}
                onChange={(e) => setFormData({ ...formData, train_type: e.target.value })}
                label="Train Type"
              >
                <MenuItem value="passenger">Passenger</MenuItem>
                <MenuItem value="freight">Freight</MenuItem>
                <MenuItem value="express">Express</MenuItem>
                <MenuItem value="local">Local</MenuItem>
              </Select>
            </FormControl>

            <FormControl>
              <InputLabel>Priority</InputLabel>
              <Select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                label="Priority"
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="critical">Critical</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Max Speed (km/h)"
              type="number"
              value={formData.max_speed_kmh}
              onChange={(e) => setFormData({ ...formData, max_speed_kmh: parseInt(e.target.value) })}
            />
            
            <TextField
              label="Length (meters)"
              type="number"
              value={formData.length_meters}
              onChange={(e) => setFormData({ ...formData, length_meters: parseFloat(e.target.value) })}
            />

            {formData.train_type === 'passenger' ? (
              <TextField
                label="Passenger Capacity"
                type="number"
                value={formData.capacity_passengers}
                onChange={(e) => setFormData({ ...formData, capacity_passengers: parseInt(e.target.value) })}
              />
            ) : (
              <TextField
                label="Weight (tons)"
                type="number"
                value={formData.weight_tons}
                onChange={(e) => setFormData({ ...formData, weight_tons: parseFloat(e.target.value) })}
              />
            )}

            <TextField
              label="Operator"
              value={formData.operator}
              onChange={(e) => setFormData({ ...formData, operator: e.target.value })}
              sx={{ gridColumn: 'span 2' }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSave} variant="contained">
            {editingTrain ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default TrainManagement;