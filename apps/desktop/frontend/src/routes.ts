import {
  ActivityIcon,
  DashboardIcon,
  FleetIcon,
  QueuesIcon,
  SettingsIcon,
  StatisticsIcon,
  UsersIcon,
} from '@armada/ui-kit';

// `nav` places a route in the rail: `main` at the top, `footer` beside the profile menu, and
// `none` for routes reached another way.
export const routePaths = {
  dashboard: {
    path: '/',
    label: 'Dashboard',
    nav: 'main',
    icon: DashboardIcon,
  },
  fleet: { path: '/fleet', label: 'Fleet', nav: 'main', icon: FleetIcon },
  queues: { path: '/queues', label: 'Queues', nav: 'main', icon: QueuesIcon },
  users: { path: '/users', label: 'Users', nav: 'main', icon: UsersIcon },
  statistics: {
    path: '/statistics',
    label: 'Statistics',
    nav: 'main',
    icon: StatisticsIcon,
  },
  activity: {
    path: '/activity',
    label: 'Activity',
    nav: 'main',
    icon: ActivityIcon,
  },
  settings: {
    path: '/settings',
    label: 'Settings',
    nav: 'footer',
    icon: SettingsIcon,
  },
  account: { path: '/account', label: 'Account details', nav: 'none' },
  about: { path: '/about', label: 'About', nav: 'none' },
  login: { path: '/login', label: 'Log in', nav: 'none' },
  temp: { path: '/temp', label: 'Dev tools', nav: 'none' },
} as const;

export const navRoutes = Object.values(routePaths).filter(
  (route) => route.nav !== 'none',
);
