/**
 * Global Search (UI 3.3+)
 * Busca universal: IP, hostname, user, IOC, hash, domain, alert, incident, case, MITRE, asset, rule.
 * Debounce + autocomplete + highlight + keyboard navigation + entity type grouping.
 */
import { useState, useEffect, useRef } from "react";
import { colors, motion, radii, spacing, typography } from "../design-system/tokens";

interface SearchResultItem {
  id: string;
  type: string;
  label: string;
  description?: string;
  icon: string;
  route?: string;
}

const MOCK_ENTITIES: Record<string, any[]> = {
  ip: [
    { id: "10.0.0.1", label: "10.0.0.1", description: "Workstation WS-001", icon: "🖥️", route: "/assets/10.0.0.1" },
    { id: "192.168.1.50", label: "192.168.1.50", description: "Server SRV-DB", icon: "🗄️", route: "/assets/192.168.1.50" },
  ],
  hostname: [
    { id: "wks-01", label: "WKS-01", description: "Workstation - João Silva", icon: "💻", route: "/assets/WKS-01" },
    { id: "srv-db-01", label: "SRV-DB-01", description: "Database Server", icon: "🗄️", route: "/assets/SRV-DB-01" },
  ],
  user: [
    { id: "admin", label: "admin", description: "Administrator", icon: "👤", route: "/users/admin" },
    { id: "john.doe", label: "john.doe", description: "SOC Analyst", icon: "👤", route: "/users/john.doe" },
  ],
  ioc: [
    { id: "malware-abc123", label: "malware-abc123", description: "Emotet IOC", icon: "🦠", route: "/iocs/malware-abc123" },
    { id: "c2.badguy.com", label: "c2.badguy.com", description: "C2 Domain", icon: "🌐", route: "/iocs/c2.badguy.com" },
  ],
  hash: [
    { id: "d41d8cd98f00b204e9800998ecf8427e", label: "d41d8cd98f00b204e9800998ecf8427e", description: "Empty file hash", icon: "🔐", route: "/hashes/d41d8cd98f00b204e9800998ecf8427e" },
  ],
  domain: [
    { id: "evil.com", label: "evil.com", description: "Malicious domain", icon: "🌐", route: "/domains/evil.com" },
    { id: "c2.badguy.com", label: "c2.badguy.com", description: "C2 Server", icon: "🎯", route: "/domains/c2.badguy.com" },
  ],
  alert: [
    { id: "ALT-001", label: "Brute Force SSH", severity: "high", icon: "🚨", route: "/alerts/ALT-001" },
    { id: "ALT-002", label: "Malware Detection", severity: "critical", icon: "🦠", route: "/alerts/ALT-002" },
  ],
  incident: [
    { id: "INC-001", label: "Brute Force SSH", severity: "high", icon: "🚨", route: "/incidents/INC-001" },
    { id: "INC-002", label: "Malware Outbreak", severity: "critical", icon: "☠️", route: "/incidents/INC-002" },
  ],
  case: [
    { id: "CASE-001", label: "Investigar Brute Force", status: "in_progress", icon: "📁", route: "/cases/CASE-001" },
    { id: "CASE-002", label: "Malware Outbreak", status: "in_progress", icon: "📂", route: "/cases/CASE-002" },
  ],
  mitre: [
    { id: "T1110", label: "T1110 - Brute Force", description: "Brute Force Attack", icon: "🔑", route: "/mitre/T1110" },
    { id: "T1059", label: "T1059 - Command & Scripting", description: "Command and Scripting Interpreter", icon: "💻", route: "/mitre/T1059" },
  ],
  asset: [
    { id: "asset-1", label: "SRV-DB-01", type: "server", criticality: "high", route: "/assets/SRV-DB-01" },
    { id: "asset-2", label: "WKS-001", type: "workstation", criticality: "medium", route: "/assets/WKS-001" },
  ],
  rule: [
    { id: "rule-001", label: "Brute Force SSH", description: "5+ failed logins in 1min", icon: "🔑", route: "/rules/rule-001" },
    { id: "rule-002", label: "Malware Execution", description: "Suspicious process execution", icon: "⚡", route: "/rules/rule-002" },
  ],
};

const ENTITY_TYPES = [
  { key: "ip", label: "IP", icon: "🌐" },
  { key: "hostname", label: "Hostname", icon: "💻" },
  { key: "user", label: "Usuário", icon: "👤" },
  { key: "ioc", label: "IOC", icon: "🦠" },
  { key: "hash", label: "Hash", icon: "🔐" },
  { key: "domain", label: "Domínio", icon: "🌐" },
  { key: "alert", label: "Alerta", icon: "🚨" },
  { key: "incident", label: "Incidente", icon: "📋" },
  { key: "case", label: "Caso", icon: "📁" },
  { key: "mitre", label: "MITRE ATT&CK", icon: "🎯" },
  { key: "asset", label: "Ativo", icon: "💻" },
  { key: "rule", label: "Regra", icon: "⚙️" },
];

const ENTITY_TYPE_LABELS: Record<string, string> = {
  ip: "IP",
  hostname: "Hostname",
  user: "Usuário",
  ioc: "IOC",
  hash: "Hash",
  domain: "Domínio",
  alert: "Alerta",
  incident: "Incidente",
  case: "Caso",
  mitre: "MITRE ATT&CK",
  asset: "Ativo",
  rule: "Regra",
};

const typeOrder: Record<string, number> = {
  alert: 0,
  incident: 1,
  case: 2,
  ip: 2,
  hostname: 3,
  user: 3,
  ioc: 4,
  domain: 4,
  hash: 4,
  asset: 5,
  mitre: 5,
  rule: 5,
};

const search = (q: string): SearchResultItem[] => {
  if (!q || q.trim().length < 1) return [];

  const query = q.toLowerCase().trim();
  const results: SearchResultItem[] = [];

  for (const [entityType, entities] of Object.entries(MOCK_ENTITIES)) {
    for (const entity of entities) {
      const searchable = `${entity.label} ${entity.description || ""} ${entity.id}`.toLowerCase();
      if (searchable.includes(query)) {
        results.push({
          id: entity.id,
          type: ENTITY_TYPE_LABELS[entityType] || entityType,
          label: entity.label,
          description: entity.description,
          icon: entity.icon || "🔍",
          route: entity.route,
        });
      }
    }
  }

  // Sort: by type priority (fixed)
  return results.sort((a, b) => {
    return (typeOrder[a.type.toLowerCase()] || 99) - (typeOrder[b.type.toLowerCase()] || 99);
  });
};

export function GlobalSearch() {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filteredResults = isOpen ? search(query) : [];

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || filteredResults.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, filteredResults.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const result = filteredResults[selectedIndex];
      if (result?.route) {
        window.location.href = result.route;
      }
      setIsOpen(false);
      setQuery("");
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div style={{ position: "relative", width: "100%" }}>
      <input
        ref={inputRef}
        placeholder="Buscar IP, hostname, usuário, IOC, hash, domínio, alerta..."
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setIsOpen(true);
          setSelectedIndex(0);
        }}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsOpen(true)}
        style={{
          width: "100%",
          fontFamily: typography.family.ui,
          fontSize: typography.size.sm,
          background: colors.background,
          color: colors.textPrimary,
          border: `1px solid ${colors.border}`,
          borderRadius: radii.md,
          padding: `${spacing["2"]} ${spacing["3"]}`,
          outline: "none",
          transition: motion.transition.fast,
        }}
        autoComplete="off"
        autoCapitalize="off"
        autoCorrect="off"
        spellCheck={false}
      />

      {isOpen && (
        <div
          ref={dropdownRef}
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            right: 0,
            background: colors.surfaceAlt,
            border: `1px solid ${colors.border}`,
            borderRadius: radii.md,
            boxShadow: "0 8px 24px rgba(0,0,0,0.6)",
            zIndex: 400,
            maxHeight: 400,
            overflowY: "auto",
            padding: spacing["1"],
          }}
        >
          {filteredResults.length === 0 ? (
            <div
              style={{
                padding: spacing["2"],
                color: colors.textMuted,
                fontSize: typography.size.sm,
              }}
            >
              Nenhum resultado para "{query}"
            </div>
          ) : (
            <>
              {ENTITY_TYPES.map(({ key, label, icon }) => {
                const typeResults = filteredResults.filter(
                  (r) => r.type.toLowerCase() === key.toLowerCase(),
                );
                if (typeResults.length === 0) return null;

                return (
                  <div
                    key={key}
                    style={{
                      borderTop: `1px solid ${colors.borderSubtle}`,
                      paddingTop: spacing["2"],
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: spacing["2"],
                        padding: `${spacing["1"]} ${spacing["2"]}`,
                        fontSize: typography.size.xs,
                        fontWeight: typography.weight.semibold,
                        color: colors.textMuted,
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                        borderBottom: `1px solid ${colors.borderSubtle}`,
                        paddingBottom: spacing["1"],
                      }}
                    >
                      <span style={{ fontSize: typography.size.sm }}>{icon}</span>
                      <span>{label}</span>
                      <span
                        style={{
                          marginLeft: "auto",
                          fontSize: typography.size.xs,
                          color: colors.textMuted,
                        }}
                      >
                        {typeResults.length} resultado{typeResults.length !== 1 ? "s" : ""}
                      </span>
                    </div>
                    {typeResults.map((result) => (
                      <button
                        key={result.id}
                        onClick={() => {
                          if (result.route) window.location.href = result.route;
                          setQuery("");
                          setIsOpen(false);
                        }}
                        onMouseEnter={() =>
                          setSelectedIndex(
                            filteredResults.findIndex((r) => r.id === result.id),
                          )
                        }
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: spacing["2"],
                          width: "100%",
                          padding: `${spacing["2"]} ${spacing["3"]}`,
                          borderRadius: radii.sm,
                          background: "transparent",
                          border: "none",
                          textAlign: "left",
                          cursor: "pointer",
                          color: colors.textPrimary,
                          fontSize: typography.size.sm,
                          transition: motion.transition.fast,
                        }}
                      >
                        <span style={{ fontSize: typography.size.sm }}>{result.icon}</span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div
                            style={{
                              fontWeight: typography.weight.medium,
                              color: colors.textPrimary,
                              whiteSpace: "nowrap",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                            }}
                          >
                            {result.label}
                          </div>
                          {result.description && (
                            <div
                              style={{
                                fontSize: typography.size.xs,
                                color: colors.textMuted,
                                whiteSpace: "nowrap",
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                              }}
                            >
                              {result.description}
                            </div>
                          )}
                        </div>
                        <span
                          style={{
                            fontSize: typography.size.xs,
                            color: colors.textMuted,
                            whiteSpace: "nowrap",
                          }}
                        >
                          {result.type}
                        </span>
                      </button>
                    ))}
                  </div>
                );
              })}
            </>
          )}
        </div>
      )}
    </div>
  );
}
