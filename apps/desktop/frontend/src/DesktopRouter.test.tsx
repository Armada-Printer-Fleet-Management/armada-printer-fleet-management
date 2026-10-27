// @vitest-environment jsdom

import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router';
import { afterEach, expect, it, vi } from 'vitest';

import { DesktopRoutes } from './DesktopRouter';
import { navRoutes, routePaths } from './routes';

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
});

function LocationProbe() {
  return <output data-testid="location">{useLocation().pathname}</output>;
}

function renderApp() {
  render(
    <MemoryRouter>
      <DesktopRoutes />
      <LocationProbe />
    </MemoryRouter>,
  );
}

function location() {
  return screen.getByTestId('location').textContent;
}

function currentLinks() {
  return screen
    .getAllByRole('link')
    .filter((link) => link.getAttribute('aria-current') === 'page');
}

it('starts on the dashboard', () => {
  renderApp();

  expect(location()).toBe(routePaths.dashboard.path);
  expect(currentLinks().map((link) => link.textContent)).toEqual([
    routePaths.dashboard.label,
  ]);
});

it('moves to each rail link and marks only that link as current', async () => {
  const user = userEvent.setup();
  renderApp();

  for (const route of navRoutes) {
    const link = screen.getByRole('link', { name: route.label });
    await user.click(link);

    expect(location()).toBe(route.path);
    expect(currentLinks()).toEqual([link]);
  }
});

it('hides the dev tools link when dev tools are off', () => {
  vi.stubEnv('VITE_ARMADA_DEV_TOOLS', '');
  renderApp();

  expect(
    screen.queryByRole('link', { name: routePaths.temp.label }),
  ).toBeNull();
});

it('shows the dev tools link when dev tools are on', async () => {
  vi.stubEnv('VITE_ARMADA_DEV_TOOLS', '1');
  const user = userEvent.setup();
  renderApp();

  await user.click(screen.getByRole('link', { name: routePaths.temp.label }));

  expect(location()).toBe(routePaths.temp.path);
});
