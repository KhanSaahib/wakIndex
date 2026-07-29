# Enterprise identity and access inventory

## Description

This design defines wakindex's account-aware inventory and enterprise dashboard. It maps explicit
human, service, and shared operating-system accounts to configured agent surfaces, model choices,
authentication contexts, effective static permissions, and policy decisions without contacting
an identity provider or executing an agent.

## Operator outcome

The inventory answers six concrete questions:

1. Which operating-system or service account owns an agent configuration?
2. Which agent product and configuration source create the access?
3. Which model and model provider are statically configured?
4. Which provider-account alias or authentication mechanism is expected to be used?
5. Which tools, processes, files, hosts, and credential names are reachable?
6. Which relationships violate policy or lack enough attribution to review confidently?

The result is an evidence-backed configuration inventory. It is not a claim about a currently
running process, live login session, or final cloud entitlement.

## Identity boundary

wakindex never enumerates every local profile automatically. An operator either:

- omits `--accounts` to inventory the current account and its normal home directory; or
- supplies a trusted TOML account catalog containing explicit profile roots and business labels.

Example:

```toml
# Description: Explicit endpoint accounts approved for wakindex inventory.
version = 1

[organization]
name = "Example Corporation"
environment = "production"

[[accounts]]
id = "alice"
display_name = "Alice Chen"
kind = "human"
home = "C:/Users/alice"
department = "Platform Engineering"
endpoint = "ENG-LT-042"
tags = ["developer", "production-support"]

[accounts.provider_accounts]
codex = "openai-enterprise/alice"
claude = "anthropic-team/alice"
gemini = "google-workspace/alice"

[[accounts]]
id = "release-bot"
display_name = "Release automation"
kind = "service"
department = "Platform Engineering"
endpoint = "github-actions"
tags = ["ci", "non-human"]
```

`home` is used only as a scan boundary and is not serialized. Provider-account aliases are
operator assertions: wakindex does not open token stores, browser profiles, keychains, or vendor
sessions to discover email addresses.

## Normalized relationship model

The new identity inventory has schema `identity-1.0` and does not change manifest schema `1.0`.

```text
Account
  |
  +-- AgentInstance
        |-- configured model(s)
        |-- model provider
        |-- provider-account alias
        |-- safe authentication context(s)
        |
        +-- AccessRecord
              |-- normalized permission and resource
              |-- source and bounded evidence
              |-- risk
              +-- policy decision and reason
```

### Account

- stable operator-controlled `id`;
- display name and `human`, `service`, or `shared` kind;
- optional department, endpoint, environment, and tags;
- provider-account aliases keyed by configuration provider;
- no serialized home-directory path.

### Agent instance

An agent instance is one account plus one supported configuration source. Its deterministic ID is
derived from endpoint, workspace identifier, account ID, provider, and stable source label. It
records:

- product/provider and `workspace` or `user` scope;
- configuration source;
- configured primary and fallback model identifiers;
- configured model provider;
- provider-account alias when supplied;
- safe authentication contexts such as an authentication type, AWS profile name, or credential
  environment-variable name;
- model resolution status: `configured` or `runtime-selected`.

Model settings can be overridden by command-line flags, environment variables, managed
configuration, or an active session. Therefore the UI always labels them as configured values.

### Access record

Each normalized `Finding` becomes an account- and agent-attributed access record. If a policy is
provided, the record contains `allowed` or `denied` plus the deterministic policy reason.
Otherwise it is `unreviewed`.

## Safe vendor extraction

Only documented, non-secret identity hints are extracted:

| Provider | Model/provider hints | Authentication hints |
| --- | --- | --- |
| Codex | `model`, `model_provider`, default subagent model | provider env-key name, OpenAI login requirement, AWS profile name |
| Claude Code | `model`, `fallbackModel` | operator provider-account alias |
| Gemini CLI | `model.name` | selected/enforced authentication type |
| Cursor, VS Code, Claude Desktop, generic MCP | runtime-selected | inherited credential names already present in findings |
| GitHub Actions and skills | runtime-selected | normalized workflow/skill findings |

Values from API-key, token, password, cookie, credential, and authorization fields are never
included. Full hook arguments and MCP credential values remain excluded.

## CLI workflows

### Personal workstation

```bash
wakindex inventory ~/work/project --format text
wakindex dashboard ~/work/project
```

### Managed endpoint

```bash
wakindex inventory /workspace \
  --accounts enterprise-accounts.toml \
  --workspace-id payments-api \
  --policy corporate-wakindex-policy.toml \
  --output identity-access.json

wakindex dashboard /workspace \
  --accounts enterprise-accounts.toml \
  --workspace-id payments-api \
  --policy corporate-wakindex-policy.toml \
  --no-browser
```

The inventory JSON is suitable for collection by endpoint management, SIEM, asset inventory, or
governance pipelines. Fleet transport and centralized storage remain deployment concerns outside
the local scanner.

## Dashboard information architecture

The dashboard is a read-only loopback application with no remote assets:

1. posture summary: accounts, agent surfaces, configured models, high-risk access, policy denials;
2. attribution coverage: runtime-selected models and unmapped provider accounts;
3. identity map: account, endpoint, department, agent, configured model, provider account, and
   authentication context;
4. access explorer: searchable/filterable permission, resource, source, risk, and policy table;
5. machine export at `/inventory.json`.

All untrusted values are HTML escaped or returned as JSON. The page fetches inventory from the
same loopback origin rather than embedding hostile configuration data in executable JavaScript.
Responses set a restrictive Content Security Policy, deny framing, prevent MIME sniffing, and
disable caching.

## Enterprise value and limitations

This milestone gives security and platform teams a deployable endpoint evidence source and an
operator UI without requiring vendor APIs. It supports offline and restricted environments and
can identify shared accounts, unknown model attribution, broad access, and missing provider
account mappings.

It deliberately does not:

- prove which model handled a past or currently active session;
- validate that a provider-account alias matches a live vendor login;
- enumerate operating-system accounts or cloud IAM;
- read keychains, browser profiles, credentials files, chat transcripts, or telemetry;
- expose the loopback dashboard as a multi-user network service;
- replace identity-provider, EDR, SIEM, PAM, or cloud authorization data.

Future integrations can merge this deterministic local evidence with those systems using stable
account, endpoint, workspace, agent, source, and provider-account identifiers. Agent IDs include
the endpoint, workspace identifier, account ID, provider, and source to avoid fleet collisions.
`--workspace-id` supplies an organization-controlled project label; otherwise the scan directory
name is used.

## Compatibility

- existing manifest schema `1.0`, `scan`, `audit`, `check`, `ui`, SARIF, and policies remain
  unchanged;
- identity output is a separate `identity-1.0` schema;
- existing findings are reused rather than redefined;
- the policy editor remains available through `wakindex ui`;
- `inventory` and `dashboard` are additive commands.

## Acceptance criteria

1. Two explicit synthetic user profiles produce separate account-to-agent-to-access mappings.
2. Codex, Claude, and Gemini configured models are attributed without emitting credential values.
3. Provider-account aliases and homes from the trusted catalog are handled separately; home paths
   never appear in output.
4. Missing model or provider-account attribution is visibly marked rather than guessed.
5. Policy decisions are attached to each access relationship with deny precedence preserved.
6. Dashboard values are escaped, inventory JSON is same-origin, and loopback security headers are
   present.
7. Existing tests, Docker tests, package builds, and CLI behavior remain compatible.
