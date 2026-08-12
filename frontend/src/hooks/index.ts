/**
 * Hooks barrel - exports all hooks
 */
export { useMetrics } from "./useMetrics";
export { useAlerts } from "./useAlerts";
export { useIncidents } from "./useIncidents";
export { useCases } from "./useCases";
export { useHealth } from "./useHealth";

// Re-export types for convenience
export type { DashboardMetrics } from "./useMetrics";
export { useShieldEvents } from "./useShieldEvents";
export type { ShieldDecisionEvent, SlaSnapshotDto } from "./useShieldEvents";
export type { SystemHealth } from "./useHealth";
export type { RecentAlert } from "./useAlerts";
export type { Incident } from "./useIncidents";
export type { Case } from "./useCases";
