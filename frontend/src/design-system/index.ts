/**
 * Design System — barrel (UI 3.1)
 * Componentes e tokens exportados publicamente.
 */

// Tokens
export { colors } from "./tokens/colors";
export type { SeverityColor } from "./tokens/colors";
export { density, motion, radii, shadows, spacing, typography, zIndex } from "./tokens";
export { tokensCss } from "./tokens/tokensCss";

// Componentes base
export { Button } from "./components/Button";
export { Badge } from "./components/Badge";
export { Card, Input, Table } from "./components/primitives";
export type { TableColumn, TableProps } from "./components/primitives";
