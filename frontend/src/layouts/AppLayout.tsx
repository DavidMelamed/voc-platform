import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { styled } from '@mui/material/styles';
import { 
  AppBar, 
  Box, 
  Drawer, 
  Toolbar, 
  Typography, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText, 
  Divider, 
  IconButton 
} from '@mui/material';
import { 
  Menu as MenuIcon, 
  Dashboard as DashboardIcon, 
  Source as SourceIcon, 
  Insights as InsightsIcon, 
  AccountTree as GraphIcon, 
  Description as DocumentsIcon, 
  Settings as SettingsIcon,
  Logout as LogoutIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const drawerWidth = 240;

const Main = styled('main', { shouldForwardProp: (prop) => prop !== 'open' })<{
  open?: boolean;
}>(({ theme, open }) => ({
  flexGrow: 1,
  padding: theme.spacing(3),
  transition: theme.transitions.create('margin', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  marginLeft: `-${drawerWidth}px`,
  ...(open && {
    transition: theme.transitions.create('margin', {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
    marginLeft: 0,
  }),
}));

const AppLayout: React.FC = () => {
  const [drawerOpen, setDrawerOpen] = useState(true);
  const navigate = useNavigate();
  const { logout, tenantId, tenantName } = useAuth();

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Data Sources', icon: <SourceIcon />, path: '/data-sources' },
    { text: 'Insights', icon: <InsightsIcon />, path: '/insights' },
    { text: 'Entity Graph', icon: <GraphIcon />, path: '/graph' },
    { text: 'Documents', icon: <DocumentsIcon />, path: '/documents' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  ];

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={toggleDrawer}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Voice-of-Customer Platform
          </Typography>
          <Typography variant="body1" sx={{ mr: 2 }}>
            {tenantName || 'Tenant'} ({tenantId || 'ID'})
          </Typography>
          <IconButton color="inherit" onClick={handleLogout}>
            <LogoutIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="persistent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
        open={drawerOpen}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item, index) => (
              <ListItem button key={item.text} onClick={() => handleNavigation(item.path)}>
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItem>
            ))}
          </List>
          <Divider />
          <List>
            <ListItem button onClick={() => window.open('/grafana/', '_blank')}>
              <ListItemIcon><DashboardIcon /></ListItemIcon>
              <ListItemText primary="Grafana" />
            </ListItem>
            <ListItem button onClick={() => window.open('/langfuse/', '_blank')}>
              <ListItemIcon><InsightsIcon /></ListItemIcon>
              <ListItemText primary="LLM Observability" />
            </ListItem>
            <ListItem button onClick={() => window.open('/jaeger/', '_blank')}>
              <ListItemIcon><GraphIcon /></ListItemIcon>
              <ListItemText primary="Tracing" />
            </ListItem>
          </List>
        </Box>
      </Drawer>
      <Main open={drawerOpen}>
        <Toolbar />
        <Box sx={{ p: 3 }}>
          <Outlet />
        </Box>
      </Main>
    </Box>
  );
};

export default AppLayout;
