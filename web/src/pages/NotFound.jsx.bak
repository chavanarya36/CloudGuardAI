import { Box, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import SearchOffIcon from '@mui/icons-material/SearchOff';

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        textAlign: 'center',
        gap: 3,
      }}
    >
      <SearchOffIcon sx={{ fontSize: 80, color: 'text.disabled' }} />
      <Typography variant="h3" fontWeight="bold" color="text.primary">
        404
      </Typography>
      <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 420 }}>
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </Typography>
      <Button
        variant="contained"
        size="large"
        onClick={() => navigate('/')}
        sx={{ borderRadius: 2, mt: 1 }}
      >
        Back to Home
      </Button>
    </Box>
  );
}
