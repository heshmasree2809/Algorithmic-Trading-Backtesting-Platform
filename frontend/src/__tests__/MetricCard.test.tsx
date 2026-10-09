import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MetricCard from '../components/MetricCard';

describe('MetricCard', () => {
  it('renders the label and value', () => {
    render(<MetricCard label="Sharpe Ratio" value="1.42" />);
    expect(screen.getByText('Sharpe Ratio')).toBeInTheDocument();
    expect(screen.getByText('1.42')).toBeInTheDocument();
  });

  it('applies the positive style class when positive is true', () => {
    render(<MetricCard label="Return" value="12%" positive />);
    expect(screen.getByText('12%').className).toMatch(/metric-value-positive/);
  });

  it('applies the negative style class when negative is true', () => {
    render(<MetricCard label="Drawdown" value="-8%" negative />);
    expect(screen.getByText('-8%').className).toMatch(/metric-value-negative/);
  });
});
