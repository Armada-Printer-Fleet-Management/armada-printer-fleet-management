/** The kitchen sink, with an optional modal dialog open over it. */
function kitchenSinkPath(dialog?: string): string {
  return dialog ? `/?dialog=${dialog}` : '/';
}

/** The kitchen sink's three states: the page alone, and each modal dialog over it. */
export const kitchenSinkStates = [
  { name: 'page', path: kitchenSinkPath() },
  { name: 'sign-in dialog', path: kitchenSinkPath('sign-in') },
  { name: 'legal dialog', path: kitchenSinkPath('legal') },
] as const;
