# MCP Assistant Rules - Aurora

## Project Context
Aurora computes per-period validator revenue and partner commissions across multiple blockchain networks (Solana, Ethereum) with a provider-agnostic architecture. The system maintains stable intermediary schemas regardless of data provider changes, ensuring deterministic and auditable calculations with full RBAC enforcement.

### Core Vision & Architecture
- **Product Goal**: Deterministic, auditable multi-chain validator P&L and partner commission computation with provider swappability
- **Target Platform**: On-premise Python backend with FastAPI REST API and web-based UI (internal + partner portals)
- **Architecture**: Chain-agnostic ingestion → staging → normalization → canonical layer → commission engine → RBAC API → UI
- **Key Technologies**: Python 3.11+, FastAPI, PostgreSQL 15+, Pydantic, SQLAlchemy, Alembic, JWT auth, Nginx

### Key Technical Principles
- **Chain-Agnostic Core**: Business logic independent of specific blockchain implementations
- **Provider Pluggability**: Data sources swappable via config without downstream impact
- **Deterministic Computation**: All calculations reproducible from source data with full audit trail
- **Security by Default**: RBAC enforced at all layers, partner data isolation via RLS
- **Audit Trail First**: Every operation logged with immutable snapshots and hash verification
- **Observable Systems**: Structured JSON logging with correlation IDs for distributed tracing

**Note:** The complete project structure and technology stack are provided in the attached `project-structure.md` file.

## Key Project Standards

### Core Principles
[List your fundamental development principles]
- Follow KISS, YAGNI, and DRY - prefer proven solutions over custom implementations
- Never mock, use placeholders, or omit code - always implement fully
- Be brutally honest about whether an idea is good or bad
- [Add project-specific principles]

### Code Organization
[Define your code organization standards]
- Keep files under [X] lines - split by extracting utilities, constants, types
- Single responsibility per file with clear purpose
- Prefer composition over inheritance
- [Add language/framework specific organization rules]

### [Language] Standards
[Replace with your primary language and its standards]
- Type safety requirements
- Naming conventions (classes, functions, constants)
- Documentation requirements (docstring style, required elements)
- Error handling patterns

### Error Handling & Logging
- Use specific exceptions with helpful messages
- Structured logging only - define your logging approach
- [Specify logging categories or patterns]
- Every request needs correlation ID for tracing

### API Design
[If applicable - define API standards]
- RESTful with consistent URL patterns
- Version from day one (/v1/, /v2/)
- Consistent response format
- Proper HTTP status codes

### Security & State
- Never trust external inputs - validate at boundaries
- [Define session/state management approach]
- [Specify data retention policies]
- Keep secrets in environment variables only

## Project-Specific Guidelines
[Add any project-specific guidelines that AI assistants should know]

### Domain-Specific Rules
[Add rules specific to your problem domain]

### Integration Points
[List key integration points or external services]

### Performance Considerations
[Add any performance-critical aspects]

## Important Constraints
- You cannot create, modify, or execute code
- You operate in a read-only support capacity
- Your suggestions are for the primary AI (Claude Code) to implement
- Focus on analysis, understanding, and advisory support

## Quick Reference
[Add frequently needed information]
- Key commands: [List common commands]
- Important paths: [List critical file paths]
- Documentation links: [Add links to detailed docs]