import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ResponsiveWrapper, { ResponsiveGrid, MobileCard, MobileButton } from '../../../components/ui/ResponsiveWrapper';

describe('ResponsiveWrapper', () => {
  it('renders children correctly', () => {
    render(
      <ResponsiveWrapper>
        <div>Test content</div>
      </ResponsiveWrapper>
    );
    
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(
      <ResponsiveWrapper className="custom-class">
        <div>Test content</div>
      </ResponsiveWrapper>
    );
    
    const wrapper = screen.getByText('Test content').parentElement;
    expect(wrapper).toHaveClass('custom-class');
  });
});

describe('ResponsiveGrid', () => {
  it('renders children in grid layout', () => {
    render(
      <ResponsiveGrid>
        <div>Item 1</div>
        <div>Item 2</div>
      </ResponsiveGrid>
    );
    
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
  });
});

describe('MobileCard', () => {
  it('renders card with content', () => {
    render(
      <MobileCard>
        <div>Card content</div>
      </MobileCard>
    );
    
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });
});

describe('MobileButton', () => {
  it('renders button with text', () => {
    render(
      <MobileButton>
        Click me
      </MobileButton>
    );
    
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(
      <MobileButton loading>
        Click me
      </MobileButton>
    );
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });
});