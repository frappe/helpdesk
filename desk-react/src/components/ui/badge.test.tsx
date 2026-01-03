import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Badge } from './badge';

describe('Badge', () => {
  it('should render badge with children', () => {
    render(<Badge>New</Badge>);
    expect(screen.getByText('New')).toBeInTheDocument();
  });

  it('should apply default variant classes', () => {
    const { container } = render(<Badge>Default</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('bg-primary');
  });

  it('should apply secondary variant classes', () => {
    const { container } = render(<Badge variant="secondary">Secondary</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('bg-secondary');
  });

  it('should apply destructive variant classes', () => {
    const { container } = render(<Badge variant="destructive">Error</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('bg-destructive');
  });

  it('should apply outline variant classes', () => {
    const { container } = render(<Badge variant="outline">Outline</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('text-foreground');
  });

  it('should apply success variant classes', () => {
    const { container } = render(<Badge variant="success">Success</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('bg-green-100');
    expect(badge.className).toContain('text-green-800');
  });

  it('should apply warning variant classes', () => {
    const { container } = render(<Badge variant="warning">Warning</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('bg-yellow-100');
    expect(badge.className).toContain('text-yellow-800');
  });

  it('should merge custom className with variant classes', () => {
    const { container } = render(<Badge className="custom-class">Custom</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('custom-class');
    expect(badge.className).toContain('bg-primary');
  });

  it('should accept additional HTML div attributes', () => {
    const { container } = render(<Badge data-testid="test-badge" id="badge-1">Test</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge).toHaveAttribute('data-testid', 'test-badge');
    expect(badge).toHaveAttribute('id', 'badge-1');
  });

  it('should render as a div element', () => {
    const { container } = render(<Badge>Content</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.tagName.toLowerCase()).toBe('div');
  });

  it('should render children content correctly', () => {
    render(
      <Badge>
        <span>Badge</span> Content
      </Badge>
    );
    expect(screen.getByText('Badge')).toBeInTheDocument();
    expect(screen.getByText(/Content/)).toBeInTheDocument();
  });
});
