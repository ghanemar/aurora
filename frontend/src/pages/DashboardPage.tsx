import React from 'react';
import {
  Box,
  Container,
  Typography,
  AppBar,
  Toolbar,
  Button,
  Paper,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import { ExitToApp as LogoutIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

/**
 * Dashboard Page
 *
 * Placeholder page for MVP Phase 4
 * Will be enhanced in Phase 5a with actual content
 */

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* AppBar */}
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <Typography
            variant="h6"
            component="div"
            sx={{
              flexGrow: 1,
              fontWeight: 700,
              background: 'linear-gradient(135deg, #14b8a6 0%, #2dd4bf 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            GLOBALSTAKE
          </Typography>

          <Typography variant="body2" sx={{ mr: 2 }}>
            {user?.full_name || user?.username}
          </Typography>

          <Button
            color="inherit"
            startIcon={<LogoutIcon />}
            onClick={handleLogout}
            sx={{ textTransform: 'none' }}
          >
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ p: 4, mb: 4, borderRadius: 3 }}>
          <Typography variant="h4" gutterBottom>
            Welcome to Aurora Admin Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Validator Revenue & Partner Commissions Management
          </Typography>
        </Paper>

        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  User Info
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Username: {user?.username}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Email: {user?.email}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Role: {user?.role}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Status
                </Typography>
                <Typography variant="body2" color="success.main">
                  ✓ Authentication system operational
                </Typography>
                <Typography variant="body2" color="success.main">
                  ✓ API connection established
                </Typography>
                <Typography variant="body2" color="success.main">
                  ✓ JWT token valid
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Next Phase
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Issue #23: Dashboard & Validators UI
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Coming in Phase 5a...
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};
