import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AppLayout from '../AppLayout';

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('AppLayout', () => {
  it('renders app title', () => {
    renderWithRouter(<AppLayout />);
    expect(screen.getByText('DiagnoseToolPy')).toBeInTheDocument();
  });

  it('renders all 5 menu items', () => {
    renderWithRouter(<AppLayout />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Analysis Tasks')).toBeInTheDocument();
    expect(screen.getByText('Casebase')).toBeInTheDocument();
    expect(screen.getByText('AI Diagnosis')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });
});
