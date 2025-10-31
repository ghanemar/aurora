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
  Skeleton,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  ExitToApp as LogoutIcon,
  AccountBalance as ChainIcon,
  People as PartnerIcon,
  Description as AgreementIcon,
  TrendingUp as CommissionIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useDashboardData } from '../hooks/useDashboardData';

/**
 * Dashboard Page
 *
 * Features:
 * - Display configured chains from chains.yaml
 * - Show count of validators per chain
 * - Show count of partners
 * - Show count of active agreements
 * - Display recent commission calculations
 * - Loading skeletons
 * - Error state handling
 */

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { data, isLoading, isError, error } = useDashboardData();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
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

          <Button
            variant="outlined"
            onClick={() => navigate('/validators')}
            sx={{ mr: 2, textTransform: 'none' }}
          >
            Validators
          </Button>

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
        {/* Header */}
        <Paper sx={{ p: 4, mb: 4, borderRadius: 3 }}>
          <Typography variant="h4" gutterBottom>
            Admin Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Validator Revenue & Partner Commissions Management
          </Typography>
        </Paper>

        {/* Error State */}
        {isError && (
          <Alert severity="error" sx={{ mb: 4 }}>
            Failed to load dashboard data: {(error as Error)?.message || 'Unknown error'}
          </Alert>
        )}

        {/* Stats Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {/* Total Validators */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <ChainIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Validators</Typography>
                </Box>
                {isLoading ? (
                  <Skeleton variant="text" width={60} height={40} />
                ) : (
                  <Typography variant="h3" color="primary">
                    {data?.total_validators || 0}
                  </Typography>
                )}
                <Typography variant="body2" color="text.secondary">
                  Total validators
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Total Partners */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <PartnerIcon color="secondary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Partners</Typography>
                </Box>
                {isLoading ? (
                  <Skeleton variant="text" width={60} height={40} />
                ) : (
                  <Typography variant="h3" color="secondary">
                    {data?.total_partners || 0}
                  </Typography>
                )}
                <Typography variant="body2" color="text.secondary">
                  Active partners
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Active Agreements */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <AgreementIcon color="info" sx={{ mr: 1 }} />
                  <Typography variant="h6">Agreements</Typography>
                </Box>
                {isLoading ? (
                  <Skeleton variant="text" width={60} height={40} />
                ) : (
                  <Typography variant="h3" color="info.main">
                    {data?.total_active_agreements || 0}
                  </Typography>
                )}
                <Typography variant="body2" color="text.secondary">
                  Active agreements
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Recent Commissions */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CommissionIcon color="success" sx={{ mr: 1 }} />
                  <Typography variant="h6">Commissions</Typography>
                </Box>
                {isLoading ? (
                  <Skeleton variant="text" width={60} height={40} />
                ) : (
                  <Typography variant="h3" color="success.main">
                    {data?.recent_commissions?.length || 0}
                  </Typography>
                )}
                <Typography variant="body2" color="text.secondary">
                  Recent calculations
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          {/* Chains Overview */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Configured Chains
                </Typography>
                {isLoading ? (
                  <Box>
                    <Skeleton variant="text" />
                    <Skeleton variant="text" />
                    <Skeleton variant="text" />
                  </Box>
                ) : data?.chains && data.chains.length > 0 ? (
                  <List>
                    {data.chains.map((chain, index) => (
                      <React.Fragment key={chain.chain_id}>
                        <ListItem sx={{ px: 0 }}>
                          <ListItemText
                            primary={
                              <Box
                                sx={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center',
                                }}
                              >
                                <Typography variant="body1">{chain.name}</Typography>
                                <Chip
                                  label={`${chain.validators_count} validators`}
                                  size="small"
                                  color="primary"
                                  variant="outlined"
                                />
                              </Box>
                            }
                            secondary={chain.chain_id}
                          />
                        </ListItem>
                        {index < data.chains.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No chains configured
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Recent Commissions */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Commission Calculations
                </Typography>
                {isLoading ? (
                  <Box>
                    <Skeleton variant="text" />
                    <Skeleton variant="text" />
                    <Skeleton variant="text" />
                  </Box>
                ) : data?.recent_commissions && data.recent_commissions.length > 0 ? (
                  <List>
                    {data.recent_commissions.map((commission, index) => (
                      <React.Fragment key={commission.commission_id}>
                        <ListItem sx={{ px: 0 }}>
                          <ListItemText
                            primary={
                              <Typography variant="body2" noWrap>
                                Validator: {commission.validator_key.slice(0, 12)}...
                              </Typography>
                            }
                            secondary={
                              <Box>
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                  component="span"
                                >
                                  Amount: {commission.commission_amount_native}
                                </Typography>
                                <br />
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                  component="span"
                                >
                                  {formatDate(commission.computed_at)}
                                </Typography>
                              </Box>
                            }
                          />
                        </ListItem>
                        {index < data.recent_commissions.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No recent commissions
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};
