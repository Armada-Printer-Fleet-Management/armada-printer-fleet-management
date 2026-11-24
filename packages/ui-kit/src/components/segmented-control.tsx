import * as React from 'react';

import type { IconProps } from '../icons/create-icon';
import { cn } from '../lib/utils';
import { Tooltip } from './tooltip';

export interface SegmentedControlOption<V extends string> {
  value: V;
  label: string;
  icon?: React.ComponentType<IconProps>;
}

export interface SegmentedControlProps<V extends string> extends Omit<
  React.FieldsetHTMLAttributes<HTMLFieldSetElement>,
  'onChange'
> {
  /** The group's accessible name, such as "Theme". */
  label: string;
  /** Shared by the group's radio inputs; unique on the page. */
  name: string;
  options: readonly SegmentedControlOption<V>[];
  value: V;
  onValueChange: (value: V) => void;
  orientation?: 'horizontal' | 'vertical';
  iconOnly?: boolean;
  ref?: React.Ref<HTMLFieldSetElement>;
}

/**
 * One choice from a few, all visible at once. Built on native radio inputs, so arrow keys move
 * between options and screen readers announce the group without extra ARIA.
 */
export function SegmentedControl<V extends string>({
  label,
  name,
  options,
  value,
  onValueChange,
  orientation = 'horizontal',
  iconOnly = false,
  className,
  ref,
  ...props
}: SegmentedControlProps<V>) {
  return (
    <fieldset
      ref={ref}
      className={cn(
        // A fieldset will not shrink below its content unless its minimum width is reset.
        'inline-flex min-w-0 gap-0.5 rounded-lg border border-border bg-secondary p-0.5',
        orientation === 'vertical' && 'flex-col',
        className,
      )}
      {...props}
    >
      <legend className="sr-only">{label}</legend>
      {options.map((option) => {
        const Icon = option.icon;
        const segment = (
          <label className="flex flex-1">
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={option.value === value}
              onChange={() => onValueChange(option.value)}
              className="peer sr-only"
            />
            <span
              className={cn(
                'flex flex-1 cursor-pointer items-center justify-center gap-1 rounded-sm text-sm font-medium text-muted-foreground',
                'hover:bg-secondary-hover hover:text-foreground',
                'peer-checked:bg-card peer-checked:text-foreground peer-checked:shadow-sm',
                'peer-focus-visible:outline-2 peer-focus-visible:outline-offset-1 peer-focus-visible:outline-ring',
                iconOnly ? 'size-9' : 'h-9 px-2',
              )}
            >
              {Icon && <Icon className="size-4" />}
              {iconOnly ? (
                <span className="sr-only">{option.label}</span>
              ) : (
                option.label
              )}
            </span>
          </label>
        );
        return iconOnly ? (
          <Tooltip key={option.value} label={option.label}>
            {segment}
          </Tooltip>
        ) : (
          <React.Fragment key={option.value}>{segment}</React.Fragment>
        );
      })}
    </fieldset>
  );
}
