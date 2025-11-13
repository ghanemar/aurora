# Documentation Architecture

This project uses a **3-tier documentation system** that organizes knowledge by stability and scope, enabling efficient AI context loading and scalable development.

## How the 3-Tier System Works

**Tier 1 (Foundation)**: Stable, system-wide documentation that rarely changes - architectural principles, technology decisions, cross-component patterns, and core development protocols.

**Tier 2 (Component)**: Architectural charters for major components - high-level design principles, integration patterns, and component-wide conventions without feature-specific details.

**Tier 3 (Feature-Specific)**: Granular documentation co-located with code - specific implementation patterns, technical details, and local architectural decisions that evolve with features.

This hierarchy allows AI agents to load targeted context efficiently while maintaining a stable foundation of core knowledge.

## Documentation Principles
- **Co-location**: Documentation lives near relevant code
- **Smart Extension**: New documentation files created automatically when warranted
- **AI-First**: Optimized for efficient AI context loading and machine-readable patterns

## Tier 1: Foundational Documentation (System-Wide)

- **[Master Context](/CLAUDE.md)** - *Essential for every session.* Coding standards, security requirements, MCP server integration patterns, and development protocols
- **[Project Structure](/docs/ai-context/project-structure.md)** - *REQUIRED reading.* Complete technology stack, file tree, and system architecture. Must be attached to Gemini consultations
- **[Database Schema](/docs/database-schema.md)** - *Data model reference.* Complete database schema specification with table definitions, relationships, and constraints
- **[Migration Guide](/docs/migration-guide.md)** - *Database workflows.* Alembic migration management, best practices, troubleshooting, and multi-environment deployment
- **[System Integration](/docs/ai-context/system-integration.md)** - *For cross-component work.* Communication patterns, data flow, testing strategies, and performance optimization
- **[Deployment Infrastructure](/docs/ai-context/deployment-infrastructure.md)** - *Infrastructure patterns.* Containerization, monitoring, CI/CD workflows, and scaling strategies
- **[Task Management](/docs/ai-context/handoff.md)** - *Session continuity.* Current tasks, documentation system progress, and next session goals

## Tier 2: Component-Level Documentation

### Backend Services
- **[Service Layer](/src/core/services/CONTEXT.md)** - *Business logic patterns.* Commission calculation architecture, withdrawer-based attribution, stake-weighted distribution, and service design patterns

## Tier 3: Feature-Specific Documentation

Granular CONTEXT.md files co-located with code for minimal cascade effects:

### API & Routes
- **[API Layer](/src/api/CONTEXT.md)** - *API patterns.* FastAPI authentication system, JWT tokens, endpoint design, Pydantic validation, and dependency injection patterns
- **[API Routers](/src/api/routers/CONTEXT.md)** - *Endpoint organization.* Sample commissions endpoints, response structures, query parameters, and frontend integration patterns

### Frontend Pages
- **[Page Components](/frontend/src/pages/CONTEXT.md)** - *React pages.* SampleCommissionsPage structure, data flow, UI components, and Material-UI integration



## Adding New Documentation

### New Component
1. Create `/new-component/CONTEXT.md` (Tier 2)
2. Add entry to this file under appropriate section
3. Create feature-specific Tier 3 docs as features develop

### New Feature
1. Create `/component/src/feature/CONTEXT.md` (Tier 3)
2. Reference parent component patterns
3. Add entry to this file under component's features

### Deprecating Documentation
1. Remove obsolete CONTEXT.md files
2. Update this mapping document
3. Check for broken references in other docs

---

*This documentation architecture template should be customized to match your project's actual structure and components. Add or remove sections based on your architecture.*