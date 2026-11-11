import * as React from 'react';

import { cn } from '../lib/utils';

interface DialogContextValue {
  titleId: string;
  descriptionId: string;
}

const DialogContext = React.createContext<DialogContextValue | null>(null);

function useDialogContext(part: string): DialogContextValue {
  const context = React.useContext(DialogContext);
  if (!context) throw new Error(`${part} must be inside a Dialog`);
  return context;
}

export interface DialogProps extends Omit<
  React.DialogHTMLAttributes<HTMLDialogElement>,
  'open'
> {
  open: boolean;
  /** Called when the user closes it with Escape. Leave it out for a decision the user must make. */
  onDismiss?: () => void;
}

/**
 * A modal dialog on the native <dialog>: while it is open, the page behind it cannot be reached,
 * focus stays inside, and it is announced by its DialogTitle. Without onDismiss, Escape does not
 * close it.
 */
const Dialog = React.forwardRef<HTMLDialogElement, DialogProps>(
  ({ open, onDismiss, onCancel, className, children, ...props }, ref) => {
    const element = React.useRef<HTMLDialogElement | null>(null);
    const titleId = React.useId();
    const descriptionId = React.useId();
    const context = React.useMemo(
      () => ({ titleId, descriptionId }),
      [titleId, descriptionId],
    );

    const setElement = React.useCallback(
      (node: HTMLDialogElement | null) => {
        element.current = node;
        if (typeof ref === 'function') ref(node);
        else if (ref) ref.current = node;
      },
      [ref],
    );

    React.useEffect(() => {
      const dialog = element.current;
      if (!dialog) return;
      if (open && !dialog.open) dialog.showModal();
      if (!open && dialog.open) dialog.close();
    }, [open]);

    return (
      <DialogContext.Provider value={context}>
        <dialog
          ref={setElement}
          aria-labelledby={titleId}
          aria-describedby={descriptionId}
          onCancel={(event) => {
            onCancel?.(event);
            event.preventDefault();
            onDismiss?.();
          }}
          className={cn(
            'm-auto flex max-h-[90vh] w-[min(42rem,calc(100vw-2rem))] flex-col gap-4 rounded-lg border bg-card p-6 text-card-foreground shadow-sm backdrop:bg-foreground/40 [&:not([open])]:hidden',
            className,
          )}
          {...props}
        >
          {children}
        </dialog>
      </DialogContext.Provider>
    );
  },
);
Dialog.displayName = 'Dialog';

const DialogHeader = React.forwardRef<
  HTMLElement,
  React.HTMLAttributes<HTMLElement>
>(({ className, ...props }, ref) => (
  <header
    ref={ref}
    className={cn('flex flex-col gap-1', className)}
    {...props}
  />
));
DialogHeader.displayName = 'DialogHeader';

const DialogTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => {
  const { titleId } = useDialogContext('DialogTitle');
  return (
    <h2
      ref={ref}
      id={titleId}
      className={cn('text-lg font-semibold', className)}
      {...props}
    />
  );
});
DialogTitle.displayName = 'DialogTitle';

const DialogDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => {
  const { descriptionId } = useDialogContext('DialogDescription');
  return (
    <p
      ref={ref}
      id={descriptionId}
      className={cn('text-sm text-foreground/70', className)}
      {...props}
    />
  );
});
DialogDescription.displayName = 'DialogDescription';

/** The dialog's content. It scrolls when taller than the space left. */
const DialogBody = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex min-h-0 flex-1 flex-col gap-3 text-sm', className)}
    {...props}
  />
));
DialogBody.displayName = 'DialogBody';

/** The dialog's actions, primary last, where the eye ends. */
const DialogFooter = React.forwardRef<
  HTMLElement,
  React.HTMLAttributes<HTMLElement>
>(({ className, ...props }, ref) => (
  <footer
    ref={ref}
    className={cn('flex justify-end gap-3', className)}
    {...props}
  />
));
DialogFooter.displayName = 'DialogFooter';

export {
  Dialog,
  DialogBody,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
};
