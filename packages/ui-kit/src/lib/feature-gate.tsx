import * as React from 'react';

export interface FeatureProviderProps<F> {
  /** The features this client offers. Anything else is hidden by its gates. */
  supported: readonly F[];
  children?: React.ReactNode;
}

export interface FeatureGateProps<F> {
  /** Shown when the client supports this feature, or any of these. */
  feature: F | readonly F[];
  /** Shown instead when it does not. Nothing by default. */
  fallback?: React.ReactNode;
  children?: React.ReactNode;
}

/**
 * Makes a provider, hook and gate for one family of features, such as slicer features. Each app
 * wraps its UI in the provider with the features it supports, and shared components show
 * themselves only where their feature is supported, so one component serves every client.
 */
export function createFeatureGate<F>() {
  const Supported = React.createContext<ReadonlySet<F>>(new Set());

  function FeatureProvider({ supported, children }: FeatureProviderProps<F>) {
    const set = React.useMemo(() => new Set(supported), [supported]);
    return <Supported.Provider value={set}>{children}</Supported.Provider>;
  }

  function useFeature(feature: F | readonly F[]): boolean {
    const supported = React.useContext(Supported);
    const wanted: readonly F[] = isList(feature) ? feature : [feature];
    return wanted.some((each) => supported.has(each));
  }

  function FeatureGate({
    feature,
    fallback = null,
    children,
  }: FeatureGateProps<F>) {
    return <>{useFeature(feature) ? children : fallback}</>;
  }

  function isList(feature: F | readonly F[]): feature is readonly F[] {
    return Array.isArray(feature);
  }

  return { FeatureProvider, useFeature, FeatureGate };
}
