# Contributing

First off, thanks for taking the time!
If you are interested in contributing to Opta, we'd love to hear from you! Drop us a line in our [Slack](https://slack.opta.dev/).

## Orientation

Here's a list of repositories that contain Opta-related code:

- [opta](https://github.com/run-x/opta)
  is the main repository containing the `Opta` core code and modules.
- [opta-docs](https://github.com/run-x/opta-docs) contains all the documentation and the Opta installation script.

## Types of Contributions

### Report Bug

The best way to report a bug is to file an issue on GitHub. Please make sure there is an open issue discussing your contribution. Before opening a new issue, please check for [existing issues](https://github.com/run-x/opta/issues). If you find an existing issue that matches closely with yours, please thumbs-up or comment on it, so we know that the issue is relevant to many people. For any new issue please include:

- Your operating system name and version.
- Opta version.
- Detailed steps to reproduce the bug.
- Any details about your local setup that might be helpful in troubleshooting.
- When posting Python stack traces, please quote them using
[Markdown blocks](https://help.github.com/articles/creating-and-highlighting-code-blocks/).
- Label the issue with `bug`
- Remember that this is a volunteer-driven project, and that contributions are welcome :)

### Submit Ideas or Feature Requests

The best way is to file an issue on GitHub:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Label the issue with `feature-request`

### Improve Documentation

Opta could always use better documentation, so feel free to open a Pull Request in our [docs repo](https://github.com/run-x/opta-docs)

### Ask Questions

Please come and hangout in our [Slack](https://slack.opta.dev/).

## Bugfix resolution time expectations

- We will respond to all new issues within 24 hours
- For any serious (production breaking) bug we will try to resolve ASAP and do a hotfix release
- For other bugs we will try to resolve them within the next 2 releases (There is a release every 2 weeks).


## Pull Request Guidelines

A philosophy we would like to strongly encourage is

> Before creating a PR, create an issue.

The purpose is to separate problem from possible solutions.

**Bug fixes:** If you’re only fixing a small bug, it’s fine to submit a pull request right away but we highly recommend to file an issue detailing what you’re fixing. This is helpful in case we don’t accept that specific fix but want to keep track of the issue. Please keep in mind that the project maintainers reserve the rights to accept or reject incoming PRs, so it is better to separate the issue and the code to fix it from each other. In some cases, project maintainers may request you to create a separate issue from PR before proceeding.

**Feature/Large changes:** If you intend to change the public API, or make any non-trivial changes to the implementation, we require you to file a new issue. This lets us reach an agreement on your proposal before you put significant effort into it. You are welcome to submit a PR along with the issue (sometimes necessary for demonstration), but we will not review/merge the code until there is an agreement on the issue.

In general, small PRs are always easier to review than large PRs. The best practice is to break your work into smaller independent PRs and refer to the same issue. This will greatly reduce turnaround time.

If you wish to share your work which is not ready to merge yet, create a [Draft PR](https://github.blog/2019-02-14-introducing-draft-pull-requests/). This will enable maintainers and the CI runner to prioritize mature PR's.

Finally, never submit a PR that will put the main branch in broken state. If the PR is part of multiple PRs to complete a large feature and cannot work on its own, you can create a feature branch and merge all related PRs into the feature branch before creating a PR from feature branch to main.

## Community
Everyone is welcome to come and hangout in our [Slack](https://slack.opta.dev/).

Please maintain appropriate, professional conduct while participating in our community. This includes all channels of communication. We take reports of harassment or unwelcoming behavior very seriously. To report such behavior, please contact us via [email](mailto:info@runx.dev).
