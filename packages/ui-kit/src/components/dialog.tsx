import * as React from 'react';

import { cn } from '../lib/utils';

export interface DialogProps extends Omit<
  React.ComponentPropsWithoutRef<'dialog'>,
  'open'
> {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const Dialog = React.forwardRef<HTMLDialogElement, DialogProps>(
  ({ open, onOpenChange, className, onCancel, onClose, ...props }, ref) => {
    const dialogRef = React.useRef<HTMLDialogElement | null>(null);

    const setRef = React.useCallback(
      (element: HTMLDialogElement | null) => {
        dialogRef.current = element;
        if (typeof ref === 'function') ref(element);
        else if (ref) ref.current = element;
      },
      [ref],
    );

    React.useEffect(() => {
      const dialog = dialogRef.current;
      if (!dialog) return;
      if (open && !dialog.open) dialog.showModal();
      if (!open && dialog.open) dialog.close();
    }, [open]);

    return (
      <dialog
        ref={setRef}
        className={cn(
          'm-auto max-h-[calc(100vh-2rem)] w-[calc(100%-2rem)] max-w-2xl overflow-y-auto rounded-lg border border-border bg-card text-card-foreground shadow-lg backdrop:bg-foreground/50',
          className,
        )}
        onCancel={(event) => {
          // File inputs also emit a bubbling cancel event when their picker is dismissed.
          if (event.target !== event.currentTarget) return;
          onCancel?.(event);
          if (event.defaultPrevented) return;
          event.preventDefault();
          onOpenChange(false);
        }}
        onClose={(event) => {
          onClose?.(event);
          if (open) onOpenChange(false);
        }}
        {...props}
      />
    );
  },
);
Dialog.displayName = 'Dialog';

const DialogHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('grid gap-2', className)} {...props} />
));
DialogHeader.displayName = 'DialogHeader';

const DialogTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h2
    ref={ref}
    className={cn('text-2xl font-semibold', className)}
    {...props}
  />
));
DialogTitle.displayName = 'DialogTitle';

const DialogDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-foreground/70', className)}
    {...props}
  />
));
DialogDescription.displayName = 'DialogDescription';

export { Dialog, DialogDescription, DialogHeader, DialogTitle };
