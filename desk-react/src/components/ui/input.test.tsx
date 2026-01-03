import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import { Input } from './input';
import userEvent from '@testing-library/user-event';

describe('Input', () => {
  it('should render input element', () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
  });

  it('should accept user input', async () => {
    const user = userEvent.setup();
    render(<Input placeholder="Type here" />);

    const input = screen.getByPlaceholderText('Type here');
    await user.type(input, 'Hello World');

    expect(input).toHaveValue('Hello World');
  });

  it('should call onChange handler', async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();

    render(<Input onChange={handleChange} placeholder="Type" />);

    const input = screen.getByPlaceholderText('Type');
    await user.type(input, 'Hi');

    expect(handleChange).toHaveBeenCalled();
  });

  it('should be disabled when disabled prop is true', () => {
    render(<Input disabled placeholder="Disabled" />);
    expect(screen.getByPlaceholderText('Disabled')).toBeDisabled();
  });

  it('should render with different input types', () => {
    const { rerender } = render(<Input type="text" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveAttribute('type', 'text');

    rerender(<Input type="email" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveAttribute('type', 'email');

    rerender(<Input type="password" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveAttribute('type', 'password');
  });

  it('should merge custom className', () => {
    render(<Input className="custom-class" data-testid="input" />);
    const input = screen.getByTestId('input');
    expect(input.className).toContain('custom-class');
    expect(input.className).toContain('rounded-md');
  });

  it('should forward ref correctly', () => {
    const ref = vi.fn();
    render(<Input ref={ref} />);
    expect(ref).toHaveBeenCalled();
  });

  it('should accept controlled value', () => {
    render(<Input value="controlled" onChange={() => {}} data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveValue('controlled');
  });

  it('should accept uncontrolled defaultValue', () => {
    render(<Input defaultValue="uncontrolled" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveValue('uncontrolled');
  });

  it('should accept placeholder', () => {
    render(<Input placeholder="Enter your name" />);
    expect(screen.getByPlaceholderText('Enter your name')).toBeInTheDocument();
  });

  it('should accept required attribute', () => {
    render(<Input required data-testid="input" />);
    expect(screen.getByTestId('input')).toBeRequired();
  });

  it('should accept maxLength attribute', () => {
    render(<Input maxLength={10} data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveAttribute('maxLength', '10');
  });

  it('should accept pattern attribute', () => {
    render(<Input pattern="[0-9]*" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveAttribute('pattern', '[0-9]*');
  });

  it('should handle readonly attribute', () => {
    render(<Input readOnly value="readonly text" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveAttribute('readonly');
  });
});
