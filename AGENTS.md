# NEMWatch Working Rules

- Read the approved specification and implementation plan before changing a milestone.
- Explain the purpose, file list, and verification strategy before implementation.
- Use test-driven development for domain logic, parsing, repositories, APIs, and UI behaviour.
- Run the milestone's complete verification before reporting completion.
- Record one project example in `LEARNING_LOG.md` after every milestone.
- Commit completed checkpoints with a subject containing the milestone number and a descriptive body.
- Do not commit `.env`, credentials, employer data, generated build output, caches, or local volumes.
- Do not run `terraform apply`, provision AWS resources, create an EKS cluster, or deploy the project without a separate direct instruction from Stephen.
- Diagnose failures and report the observed evidence; never hide or skip a failing check.
