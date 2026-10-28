import { routePaths } from '../routes';

export function MyPrintsPage() {
  return (
    <h1 className="p-8 text-3xl font-bold">{routePaths.myPrints.label}</h1>
  );
}
