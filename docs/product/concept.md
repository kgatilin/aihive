Intro

AI coding agents, such as Crusor AI and Claude Code, are rapidly improving in their capabilities. It is only a matter of time before they can generate code consistently with minimal to no human oversight. However, to fully integrate these AI agents into our workflows, we must rethink our approach to software development. The transition to this new methodology may take longer than it will for the industry to produce more reliable coding agents, so it is essential to begin this transformation now. Below are some reflections on this topic.

Delegation instead of oversight

Currently, all AI coding agents are positioned as "co-pilots" rather than complete substitutes for engineers. While this positioning is understandable, the industry is clearly moving towards the development of fully autonomous agents. Therefore, it is essential to embrace this shift and design our workflows to integrate autonomous agents, rather than merely viewing them as "co-pilots."

The key question we must address is: “What must be established to trust these agents?” This is equally relevant for human engineers, although we generally place more trust in people. If we consider the perspective of product managers, they often validate outcomes without reviewing the underlying code. Therefore, I suggest that our focus should shift towards validating end results rather than scrutinizing the code itself. Essentially, the operators of these AI agents will function as product-oriented QA engineers.

Principles

AI-driven workflows introduce new risks, particularly around hallucinations, prompt injection, and misinterpretation of requirements. To mitigate these risks, several foundational safeguards must be in place:

AI agents must operate in isolated environments (e.g., Docker) to contain potential failures.

Application security testing must be embedded in the pipeline to detect AI-induced vulnerabilities.

Instructions fed into AI must be structured, explicit, and free from ambiguity to reduce misinterpretation.

Documentation, including architecture, must be comprehensive, AI-readable, and continuously updated.

All changes and decisions must be recorded in a human-readable format to maintain traceability.

Practically, this means:

Running AI agents in sandboxed environments (e.g. Docker containers) to prevent unintended side effects.

Storing product requirements and AI-generated outputs in a version-controlled repository to enable audits.

Using a two-step process: first, the AI generates an execution plan (WBS, ADRs) for human validation before proceeding with code generation.

Maintaining a human-curated integration test suite to validate AI-generated application contracts.

While many of these tasks can be partially automated by AI (e.g., structuring requirements, writing documentation), the challenge lies in ensuring AI-generated outputs are reliable, interpretable, and verifiable before they are trusted in production workflows.

Architecture

With AI-built applications becoming part of the software landscape, architectural discipline becomes more critical than ever. Unlike human engineers who can reason about unintended side effects, AI agents operate within predefined boundaries. This makes principles like separation of concerns, modularity, and strictly enforced contracts essential to prevent cascading failures and unpredictable behaviors.

A microservices approach is particularly useful in AI-driven development, as it helps limit AI context exposure and allows agents to generate isolated, self-contained components. This can improve efficiency and reduce cost by preventing AI from making assumptions beyond its scope. However, increased modularity also adds complexity in managing dependencies, enforcing compatibility, and ensuring service interoperability. The trade-offs between AI efficiency and maintainability overhead must be carefully managed.

Development methodologies like BDD (Behavior-Driven Development) and TDD (Test-Driven Development) serve as essential guardrails rather than just efficiency boosters. BDD allows teams to define clear acceptance criteria in structured scenarios that AI can use as development guidelines. TDD provides immediate feedback loops, ensuring that AI-generated code remains testable, verifiable, and aligned with business logic. Without these mechanisms, AI risks producing technically correct but unverified implementations that may fail in real-world usage.

By reinforcing strict architectural boundaries, limiting AI decision scope, and embedding automated validation mechanisms, AI-driven development can be made more predictable, maintainable, and resilient.

AI Development pipeline

For AI-driven development to work in practice, multiple AI agents must operate in a coordinated, structured workflow with well-defined responsibilities and validation mechanisms. The key components of this system include:

Product Requirements Writer – A conversational AI that transforms unstructured requirements into structured, AI-readable product specifications. It clarifies ambiguities, requests missing details, and generates a structured document that is stored in a product requirements repository. The structured requirements serve as the single source of truth for development tasks.

AI Software Engineer – A scalable pool of agents responsible for writing code based on structured requirements. To ensure consistency as the pool scales, standardized development guidelines, enforced architectural patterns, and automated validation mechanisms must be in place. AI-generated code is continuously evaluated against predefined standards, ensuring alignment with functional and architectural expectations while maintaining efficiency and scalability.

Orchestrator – A governance agent that oversees AI development activities, ensures integration test compliance, and maintains architectural documentation. Beyond coordination, the Orchestrator must act as a failure detection and correction mechanism, ensuring that inconsistencies between different AI agents do not accumulate.

Several human oversight checkpoints must be built into the AI development pipeline to ensure reliability, security, and maintainability:

Product Requirements Validation – Reviewing structured specifications before coding begins to catch ambiguities and missing details.

Execution Plan Review – Assessing AI-generated work breakdown structures and architectural decisions to prevent flawed designs.

Code Security & Compliance Checks – Ensuring AI-generated code meets security standards through automated scanning, static analysis, and policy enforcement, with human oversight on critical vulnerabilities and exceptions.

Integration Test Validation – Verifying system-wide compatibility to prevent breaking changes before deployment.

Production Monitoring & Incident Escalation – Continuously observing AI-built services for unexpected behavior, with human intervention available for critical failures.

Applicability of Autonomous AI Agents

The effectiveness of AI agents in software development depends on the availability of public domain knowledge for a given field. Areas with extensive open-source projects, well-documented patterns, and standardized best practices are the most suitable for automation. These include:

UI development – Frontend frameworks, component libraries, and common design patterns are well-documented.

Basic APIs – Simple data access layers and CRUD operations follow predictable structures.

Infrastructure management – Infrastructure-as-Code (IaC) tools for cloud provisioning are widely used and documented.

Data pipeline setup – Building data ingestion and transformation pipelines is a structured, repeatable process.

Conversely, domains with limited publicly available knowledge, high uncertainty, or proprietary business logic will continue to rely on human expertise. These include:

Business logic-heavy applications – AI lacks context and reasoning for company-specific rules and decision-making.

State-of-the-art software development – Areas like AI model research and deep system optimization require innovation beyond existing knowledge.

Competitive advantage domains – Proprietary algorithms, domain-specific optimizations, and strategic software cannot be effectively trained on public data.

The goal is not to replace engineers but to shift their focus to tasks where human decision-making, creativity, and adaptability outperform AI. Humans will continue to lead in areas with high uncertainty, strategic importance, and limited training data, while AI automates well-documented, repetitive tasks.

How to start

At the start, AI-built applications must remain non-critical and isolated from human-built systems. This isolation is enforced by restricting access to repositories (e.g., dedicated AI-specific repositories) and deploying AI-built applications in separate clusters with controlled access to Criteo APIs.

To assess AI efficiency, a set of key metrics must be tracked via an AI Dev Dashboard, including:

Total cost – Overall expense of AI-driven development.

Iteration time – Speed of each development cycle.

Number of iterations – Adjustments required from start to deployment.

Change failure rate – Frequency of production issues.

Time to restore – Speed of resolving AI-introduced bugs.

Lead time – Time from finalized product requirements to deployment.

These metrics will provide clear visibility into AI development performance and guide next steps.

Potential drawbacks

It is important to acknowledge that the description above relies heavily on the assumption, that an AI agent can eventually, through multiple iterations, generate working application. This assumption is something to be validated. Even though I strongly believe in the long-run it will be valid, the current state might be different and it is not clear how long would it take for the industry to produce reliable agents. Below are some concerns that might be raised about the approach:

Lack of Code Oversight – AI-generated code might be functional but inefficient, insecure, or difficult to maintain. Focusing solely on validating the end result shifts the burden of debugging and long-term maintenance onto engineers without clear ownership.

AI Hallucinations & Security Risks – Execution plans and generated code can introduce flawed logic or security vulnerabilities. Even with isolated environments, undetected prompt injections or hidden backdoors pose a significant risk to system integrity.

Ambiguity in Structured Requirements – AI may misinterpret structured requirements, leading to incorrect implementations. Errors in converting unstructured input into structured specifications can propagate through the development pipeline, making early validation critical.

Microservices Overhead vs. AI Efficiency – While modularity benefits AI agents, excessive microservices introduce operational complexity. Managing dependencies, ensuring interoperability, and debugging distributed AI-generated components require additional effort that may outweigh the gains.

Long-Term Viability – Faster iterations can lead to fragile, hard-to-maintain systems. Metrics focused on speed and cost do not capture long-term technical debt, making sustainability a key concern for AI-driven development.