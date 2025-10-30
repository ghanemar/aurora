import { createTheme } from '@mui/material/styles';

/**
 * Aurora Admin Dashboard Theme
 *
 * Design system matching the visual reference:
 * - Dark navy background (#0a1628)
 * - Teal/cyan accents (#14b8a6, #0d9488)
 * - Clean, modern card-based layout
 * - Professional, minimalist aesthetic
 */

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#14b8a6', // Teal accent (from buttons)
      light: '#2dd4bf',
      dark: '#0d9488',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#3b82f6', // Blue accent
      light: '#60a5fa',
      dark: '#2563eb',
      contrastText: '#ffffff',
    },
    background: {
      default: '#0a1628', // Dark navy (main background)
      paper: '#1e293b', // Slightly lighter for cards
    },
    text: {
      primary: '#f1f5f9', // Light text
      secondary: '#cbd5e1', // Muted text
    },
    divider: 'rgba(255, 255, 255, 0.12)',
    error: {
      main: '#ef4444',
    },
    warning: {
      main: '#f59e0b',
    },
    success: {
      main: '#10b981',
    },
    info: {
      main: '#3b82f6',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
    },
    button: {
      textTransform: 'none', // Don't uppercase buttons
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 12, // Rounded corners for cards
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '10px 24px',
          fontSize: '0.95rem',
          fontWeight: 500,
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(20, 184, 166, 0.3)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          '&:hover': {
            borderColor: 'rgba(20, 184, 166, 0.3)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            '& fieldset': {
              borderColor: 'rgba(255, 255, 255, 0.12)',
            },
            '&:hover fieldset': {
              borderColor: 'rgba(255, 255, 255, 0.24)',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#14b8a6',
            },
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#1e293b',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        },
      },
    },
  },
});
