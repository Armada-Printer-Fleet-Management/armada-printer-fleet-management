/** The measured values the checks share, each named for why it is that size. */
export const limits = {
  /** Browsers round layout to fractions of a pixel; a difference this small is never visible. */
  tolerancePx: 1,
  /** Tailwind's sr-only draws a 1px box that clips its content: text hidden on purpose. */
  screenReaderOnlyPx: 1,
  /**
   * How far outside an element its focus ring can draw. ui-kit draws focus as `outline-2` with
   * `outline-offset-2`: a 2px outline starting 2px out.
   */
  focusRingReachPx: 4,
  /** How much of an element's text a problem line quotes, enough to find it on the page. */
  excerptLength: 40,
  /** HTTP statuses from 400 up are client or server errors. */
  firstErrorStatus: 400,
} as const;

export type Limits = typeof limits;
