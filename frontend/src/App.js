import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CssBaseline,
  Container
} from '@mui/material';
import {
  Dashboard,
  Train,
  Timeline,
  Settings,
  Assessment,
  Warning
} from '@mui/icons-material';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Dashboard from './components/Dashboard';
import TrainManagement from './components/TrainManagement';
import ScheduleView from './components/ScheduleView';
import SimulationInterface from './components/SimulationInterface';
import { WebSocketProvider } from './hooks/useWebSocket';
import './App.css';

const drawerWidth = 240;

function App() {
  const [selectedMenu, setSelectedMenu] = useState('dashboard');

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <Dashboard />, component: Dashboard },
    { id: 'trains', label: 'Train Management', icon: <Train />, component: TrainManagement },
    { id: 'schedules', label: 'Schedules', icon: <Timeline />, component: ScheduleView },
    { id: 'simulation', label: 'Simulation', icon: <Assessment />, component: SimulationInterface },
  ];

  const renderContent = () => {
    const activeItem = menuItems.find(item => item.id === selectedMenu);
    const Component = activeItem ? activeItem.component : Dashboard;
    return <Component />;
  };

  return (
    <WebSocketProvider>
      <Router>
        <Box sx={{ display: 'flex' }}>
          <CssBaseline />
          
          {/* App Bar */}
          <AppBar
            position="fixed"
            sx={{
              width: `calc(100% - ${drawerWidth}px)`,
              ml: `${drawerWidth}px`,
              backgroundColor: '#1976d2'
            }}
          >
            <Toolbar>
              <Typography variant="h6" noWrap component="div">
                🚆 AI Train Traffic Control System
              </Typography>
              <Box sx={{ flexGrow: 1 }} />
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                Real-time Railway Operations Management
              </Typography>
            </Toolbar>
          </AppBar>

          {/* Side Navigation */}
          <Drawer
            sx={{
              width: drawerWidth,
              flexShrink: 0,
              '& .MuiDrawer-paper': {
                width: drawerWidth,
                boxSizing: 'border-box',
                backgroundColor: '#f8f9fa'
              },
            }}
            variant="permanent"
            anchor="left"
          >
            <Toolbar />
            <Box sx={{ overflow: 'auto', paddingTop: 2 }}>
              <List>
                {menuItems.map((item) => (
                  <ListItem
                    button
                    key={item.id}
                    onClick={() => setSelectedMenu(item.id)}
                    selected={selectedMenu === item.id}
                    sx={{
                      margin: '0 8px',
                      borderRadius: '8px',
                      '&.Mui-selected': {
                        backgroundColor: '#e3f2fd',
                        '&:hover': {
                          backgroundColor: '#e3f2fd',
                        },
                      },
                    }}
                  >
                    <ListItemIcon sx={{ color: selectedMenu === item.id ? '#1976d2' : 'inherit' }}>
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText 
                      primary={item.label}
                      sx={{ color: selectedMenu === item.id ? '#1976d2' : 'inherit' }}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          </Drawer>

          {/* Main Content */}
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              bgcolor: '#f5f5f5',
              p: 3,
              minHeight: '100vh'
            }}
          >
            <Toolbar />
            <Container maxWidth="xl">
              {renderContent()}
            </Container>
          </Box>
        </Box>

        {/* Toast Notifications */}
        <ToastContainer
          position="top-right"
          autoClose={5000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
        />
      </Router>
    </WebSocketProvider>
  );
}

export default App;