import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import { Button } from './button';
import userEvent from '@testing-library/user-event';

describe('Button', () => {
  it('should render button with children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Click me');
  });

  it('should handle click events', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(<Button onClick={handleClick}>Click me</Button>);

    await user.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('should apply default variant classes', () => {
    render(<Button>Default</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('bg-primary');
  });

  it('should apply destructive variant classes', () => {
    render(<Button variant="destructive">Delete</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('bg-destructive');
  });

  it('should apply outline variant classes', () => {
    render(<Button variant="outline">Outline</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('border');
  });

  it('should apply secondary variant classes', () => {
    render(<Button variant="secondary">Secondary</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('bg-secondary');
  });

  it('should apply ghost variant classes', () => {
    render(<Button variant="ghost">Ghost</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('hover:bg-accent');
  });

  it('should apply link variant classes', () => {
    render(<Button variant="link">Link</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('underline-offset-4');
  });

  it('should apply small size classes', () => {
    render(<Button size="sm">Small</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('h-8');
    expect(button.className).toContain('text-xs');
  });

  it('should apply large size classes', () => {
    render(<Button size="lg">Large</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('h-10');
  });

  it('should apply icon size classes', () => {
    render(<Button size="icon">🔍</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('h-9');
    expect(button.className).toContain('w-9');
  });

  it('should merge custom className with variant classes', () => {
    render(<Button className="custom-class">Custom</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('custom-class');
    expect(button.className).toContain('bg-primary');
  });

  it('should forward ref correctly', () => {
    const ref = vi.fn();
    render(<Button ref={ref}>With Ref</Button>);
    expect(ref).toHaveBeenCalled();
  });

  it('should accept additional HTML button attributes', () => {
    render(<Button type="submit" name="submit-btn">Submit</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('type', 'submit');
    expect(button).toHaveAttribute('name', 'submit-btn');
  });

  it('should not call onClick when disabled', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(<Button disabled onClick={handleClick}>Disabled</Button>);

    await user.click(screen.getByRole('button'));
    expect(handleClick).not.toHaveBeenCalled();
  });
});
