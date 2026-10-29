import {
  BookOpenIcon,
  HelpCircleIcon,
  HomeIcon,
  PrinterIcon,
} from '@armada/ui-kit';

// `nav` places a route in the sidebar: `main` for the main list and `none` for routes reached
// another way.
export const routePaths = {
  home: { path: '/', label: 'Home', nav: 'main', icon: HomeIcon },
  myPrints: {
    path: '/prints',
    label: 'My prints',
    nav: 'main',
    icon: PrinterIcon,
  },
  training: {
    path: '/training',
    label: 'Training',
    nav: 'main',
    icon: BookOpenIcon,
  },
  help: { path: '/help', label: 'Help', nav: 'main', icon: HelpCircleIcon },
  temp: { path: '/temp', label: 'Dev tools', nav: 'none' },
} as const;

export const navRoutes = Object.values(routePaths).filter(
  (route) => route.nav !== 'none',
);
