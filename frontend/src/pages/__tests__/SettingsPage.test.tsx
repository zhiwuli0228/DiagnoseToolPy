import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SettingsPage from '../SettingsPage';

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
};

describe('SettingsPage', () => {
  it('renders settings title', () => {
    renderWithRouter(<SettingsPage />);
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders app name and version', () => {
    renderWithRouter(<SettingsPage />);
    expect(screen.getByText('DiagnoseToolPy')).toBeInTheDocument();
    expect(screen.getByText('0.1.0')).toBeInTheDocument();
  });

  it('renders empty state for input roots', () => {
    renderWithRouter(<SettingsPage />);
    expect(screen.getByText(/no input roots configured/i)).toBeInTheDocument();
  });
});
