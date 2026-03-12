import { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Divider,
  Chip,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SecurityIcon from '@mui/icons-material/Security';
import ScannerIcon from '@mui/icons-material/Scanner';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PsychologyIcon from '@mui/icons-material/Psychology';
import FeedbackIcon from '@mui/icons-material/Feedback';
import AssessmentIcon from '@mui/icons-material/Assessment';
import ShieldIcon from '@mui/icons-material/Shield';
import HistoryIcon from '@mui/icons-material/History';
import SettingsIcon from '@mui/icons-material/Settings';

const drawerWidth = 260;

const menuItems = [
  { text: 'Scan', path: '/scan', icon: <ScannerIcon /> },
  { text: 'Dashboard', path: '/dashboard', icon: <DashboardIcon /> },
  { text: 'Learning', path: '/learning', icon: <PsychologyIcon /> },
  { text: 'History', path: '/history', icon: <HistoryIcon /> },
  { text: 'Feedback', path: '/feedback', icon: <FeedbackIcon /> },
  { text: 'Model Status', path: '/model-status', icon: <AssessmentIcon /> },
  { text: 'Settings', path: '/settings', icon: <SettingsIcon /> },
];

export default function Layout({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: '#071a2f' }}>
      {/* Logo Section */}
      <Box sx={{ 
        p: 3,
        background: 'linear-gradient(135deg, #0d47a1 0%, #1565c0 100%)',
        color: 'white'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
          <Box sx={{
            width: 40,
            height: 40,
            borderRadius: 2,
            background: 'rgba(255, 255, 255, 0.2)',
            backdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '2px solid rgba(255, 255, 255, 0.3)'
          }}>
            <ShieldIcon sx={{ fontSize: 24 }} />
          </Box>
          <Box>
            <Typography variant="h6" fontWeight="bold" sx={{ lineHeight: 1.2 }}>
              CloudGuard
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.9 }}>
              AI Security
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Navigation */}
      <Box sx={{ flex: 1, py: 2 }}>
        <Typography 
          variant="overline" 
          sx={{ 
            px: 3, 
            color: 'rgba(255,255,255,0.4)',
            fontWeight: 'bold',
            fontSize: '0.7rem',
            letterSpacing: 1
          }}
        >
          Navigation
        </Typography>
        <List sx={{ px: 2, mt: 1 }}>
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
                <ListItemButton
                  component={Link}
                  to={item.path}
                  sx={{
                    borderRadius: 2,
                    py: 1.5,
                    bgcolor: isActive ? 'rgba(66, 165, 245, 0.15)' : 'transparent',
                    color: isActive ? '#42a5f5' : 'rgba(255,255,255,0.7)',
                    '&:hover': {
                      bgcolor: isActive ? 'rgba(66, 165, 245, 0.2)' : 'rgba(255,255,255,0.05)',
                    },
                    transition: 'all 0.2s',
                    '& .MuiListItemIcon-root': {
                      color: isActive ? '#42a5f5' : 'rgba(255,255,255,0.5)',
                      minWidth: 40
                    }
                  }}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText 
                    primary={item.text}
                    primaryTypographyProps={{
                      fontWeight: isActive ? 'bold' : 'medium',
                      fontSize: '0.95rem'
                    }}
                  />
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>
      </Box>

      {/* Footer */}
      <Box sx={{ p: 3, borderTop: '1px solid', borderColor: 'rgba(255,255,255,0.06)' }}>
        <Box sx={{ 
          p: 2, 
          borderRadius: 2,
          background: 'rgba(102, 187, 106, 0.08)',
          border: '1px solid',
          borderColor: 'rgba(102, 187, 106, 0.25)'
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Box sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              bgcolor: 'success.main',
              animation: 'pulse 2s infinite',
              '@keyframes pulse': {
                '0%, 100%': { opacity: 1 },
                '50%': { opacity: 0.5 }
              }
            }} />
            <Typography variant="caption" fontWeight="bold" color="success.main">
              System Online
            </Typography>
          </Box>
          <Typography variant="caption" color="rgba(255,255,255,0.5)" display="block">
            All services operational
          </Typography>
        </Box>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          bgcolor: '#0a1929',
          borderBottom: '1px solid',
          borderColor: 'rgba(255,255,255,0.08)',
          boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
          backdropFilter: 'blur(20px)',
        }}
      >
        <Toolbar>
          <IconButton
            color="primary"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1 }}>
            <Box sx={{
              px: 2,
              py: 0.5,
              borderRadius: 1,
              background: 'rgba(66, 165, 245, 0.12)',
              border: '1px solid',
              borderColor: 'rgba(66, 165, 245, 0.3)'
            }}>
              <Typography 
                variant="h6" 
                noWrap 
                component="div"
                sx={{
                  fontWeight: 'bold',
                  color: '#42a5f5',
                }}
              >
                Security Scanning Platform
              </Typography>
            </Box>
            <Chip 
              label="v2.5" 
              size="small" 
              sx={{ 
                fontWeight: 'bold',
                bgcolor: 'rgba(102, 187, 106, 0.15)',
                color: '#66bb6a',
                border: '1px solid rgba(102, 187, 106, 0.3)'
              }} 
            />
          </Box>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              border: 'none',
              bgcolor: '#071a2f'
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              border: 'none',
              borderRight: '1px solid',
              borderColor: 'rgba(255,255,255,0.06)',
              bgcolor: '#071a2f'
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 4,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          bgcolor: '#0a1929',
          minHeight: '100vh'
        }}
      >
        <Toolbar />
        {children || <Outlet />}
      </Box>
    </Box>
  );
}
