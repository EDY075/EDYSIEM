/**
 * Design System — barrel (UI 3.1 + 3.3 + 3.4)
 * Componentes e tokens exportados publicamente.
 */

// Tokens
export { colors } from "./tokens/colors";
export type { SeverityColor } from "./tokens/colors";
export { density, elevation, motion, radii, shadows, spacing, typography, zIndex } from "./tokens";
export { tokensCss } from "./tokens/tokensCss";

// Componentes base (UI 3.1)
export { Button } from "./components/Button";
export { BrandMark } from "./components/BrandMark";
export { Badge } from "./components/Badge";
export { Card, Input, Table } from "./components/primitives";
export type { TableColumn, TableProps } from "./components/primitives";

// Layout (UI 3.3)
export { Breadcrumb } from "../shell/Breadcrumb";
export { GlobalSearch } from "../shell/GlobalSearch";
export { Sidebar } from "../shell/Sidebar";
export { Topbar } from "../shell/Topbar";
export { AppShell, Layout } from "../shell/AppShell";

// Badges (UI 3.4)
export { SeverityBadge, StatusBadge } from "./components/badges";
export type { SeverityBadgeProps, StatusBadgeProps, StatusTone } from "./components/badges";

// Cards (UI 3.4)
export { KpiCard, MetricCard } from "./components/cards";

// Data Table (UI 3.4)
export { DataTable } from "./components/DataTable";
export type { DataTableProps, DataColumn } from "./components/DataTable";

// Feedback (UI 3.4)
export { EmptyState, LoadingSkeleton, Toolbar } from "./components/feedback";

// Overlays (UI 3.4)
export { Drawer, Modal } from "./components/overlays";
export type { DrawerProps, ModalProps } from "./components/overlays";

// Timeline / Activity (UI 3.4)
export { Timeline, ActivityFeed } from "./components/Timeline";
export type { TimelineItem, TimelineProps, ActivityItem, ActivityFeedProps } from "./components/Timeline";
