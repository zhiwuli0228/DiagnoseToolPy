import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

/**
 * @deprecated Use DiagnosisStudioPage instead (conversational diagnosis with user context)
 * This page is kept for backward compatibility and redirects to DiagnosisStudioPage
 */
function AIDiagnosisPage() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Only redirect if this page is actually being displayed (not hidden via display:none)
    // Check if the current location is exactly /diagnosis (not prefixed)
    if (location.pathname === '/diagnosis' || location.pathname.startsWith('/diagnosis/')) {
      navigate('/diagnosis-studio');
    }
  }, [navigate, location.pathname]);

  return null;
}

export default AIDiagnosisPage;
