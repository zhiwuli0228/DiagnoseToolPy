import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DashboardPage from '../DashboardPage';

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
};

describe('DashboardPage', () => {
  it('renders dashboard title', () => {
    renderWithRouter(<DashboardPage />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('renders all 3 navigation cards', () => {
    renderWithRouter(<DashboardPage />);
    expect(screen.getByText('Analysis Tasks')).toBeInTheDocument();
    expect(screen.getByText('Casebase')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('cards have correct descriptions', () => {
    renderWithRouter(<DashboardPage />);
    expect(screen.getByText(/scan server directories/i)).toBeInTheDocument();
    expect(screen.getByText(/browse and manage fault cases/i)).toBeInTheDocument();
  });
});
