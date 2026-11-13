import { createFeatureGate } from '@armada/ui-kit';
import { SlicerFeature } from '../gen/print_preparation/v1/slicer_feature_pb';

const gate = createFeatureGate<SlicerFeature>();

/** Wraps an app's slicer UI with the slicer features that app supports. */
export const SlicerFeatureProvider = gate.FeatureProvider;
/** Shows its children only where the app supports the feature, or any of the features. */
export const SlicerFeatureGate = gate.FeatureGate;
/** Whether the app supports the feature, or any of the features. */
export const useSlicerFeature = gate.useFeature;

export { SlicerFeature };
