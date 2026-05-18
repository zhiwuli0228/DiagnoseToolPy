import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import CasebasePage from '../CasebasePage';

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
};

describe('CasebasePage', () => {
  it('renders under development message', () => {
    renderWithRouter(<CasebasePage />);
    expect(screen.getByText(/under development/i)).toBeInTheDocument();
  });
});
