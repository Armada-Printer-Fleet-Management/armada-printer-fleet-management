import * as React from 'react';

import { cn } from '../lib/utils';
import { useTheme } from '../theme/theme-provider';

// Vite bundles a file named this way and rewrites the URL, so no import type is needed.
const armadaLogoDark = new URL(
  '../assets/armada-logo-dark.svg',
  import.meta.url,
).href;
const armadaLogoLight = new URL(
  '../assets/armada-logo-light.svg',
  import.meta.url,
).href;

export type OrganizationLogoProps = Omit<
  React.ImgHTMLAttributes<HTMLImageElement>,
  'src'
>;

/** The logo drawn for the current theme. Needs a ThemeProvider above it. */
const OrganizationLogo = React.forwardRef<
  HTMLImageElement,
  OrganizationLogoProps
>(({ className, alt = 'Organization logo', ...props }, ref) => {
  const { theme } = useTheme();
  return (
    <img
      ref={ref}
      src={theme === 'dark' ? armadaLogoDark : armadaLogoLight}
      alt={alt}
      className={cn('size-10 shrink-0', className)}
      {...props}
    />
  );
});
OrganizationLogo.displayName = 'OrganizationLogo';

export { OrganizationLogo };
