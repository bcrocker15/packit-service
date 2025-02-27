# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import hashlib
import logging
from typing import Optional, Union

import github
import gitlab

from ogr.abstract import CommitStatus, GitProject
from ogr.services.gitlab import GitlabProject
from ogr.services.pagure import PagureProject

logger = logging.getLogger(__name__)


class StatusReporter:
    def __init__(
        self,
        project: GitProject,
        commit_sha: str,
        pr_id: Optional[int] = None,
    ):
        logger.debug(
            f"Status reporter will report for {project}, commit={commit_sha}, pr={pr_id}"
        )
        self.project = project
        self._project_with_commit = None
        self.commit_sha = commit_sha
        self.pr_id = pr_id

    @property
    def project_with_commit(self) -> GitProject:
        """
        Returns GitProject from which we can set commit status.
        """
        if self._project_with_commit is None:
            self._project_with_commit = (
                self.project.get_pr(self.pr_id).source_project
                if isinstance(self.project, GitlabProject) and self.pr_id is not None
                else self.project
            )

        return self._project_with_commit

    def report(
        self,
        state: CommitStatus,
        description: str,
        url: str = "",
        check_names: Union[str, list, None] = None,
    ) -> None:
        """
        set commit check status

        :param state: state accepted by github
        :param description: the long text
        :param url: url to point to (logs usually)
        :param check_names: those in bold
        """

        if not check_names:
            logger.warning("No checks to set status for.")
            return

        elif isinstance(check_names, str):
            check_names = [check_names]

        for check in check_names:
            self.set_status(
                state=state, description=description, check_name=check, url=url
            )

    def __set_pull_request_status(
        self, check_name: str, description: str, url: str, state: CommitStatus
    ):
        if self.pr_id is None:
            return
        pr = self.project.get_pr(self.pr_id)
        if hasattr(pr, "set_flag") and pr.head_commit == self.commit_sha:
            logger.debug("Setting the PR status (pagure only).")
            pr.set_flag(
                username=check_name,
                comment=description,
                url=url,
                status=state,
                # For Pagure: generate a custom uid from the check_name,
                # so that we can update flags we set previously,
                # instead of creating new ones.
                uid=hashlib.md5(check_name.encode()).hexdigest(),
            )

    def report_status_by_comment(
        self,
        state: CommitStatus,
        url: str,
        check_names: Union[str, list, None],
        description: str,
    ):
        """
        Reporting build status with MR comment if no permission to the fork project
        """

        if isinstance(check_names, str):
            check_names = [check_names]

        comment_table_rows = [
            "| Job | Result |",
            "| ------------- | ------------ |",
        ] + [f"| [{check}]({url}) | {state.name.upper()} |" for check in check_names]

        table = "\n".join(comment_table_rows)
        self.comment(table + f"\n### Description\n\n{description}")

    def __add_commit_comment_with_status(
        self, state: CommitStatus, description: str, check_name: str, url: str = ""
    ):
        body = (
            "\n".join(
                [
                    f"- name: {check_name}",
                    f"- state: {state.name}",
                    f"- url: {url if url else 'not provided'}",
                ]
            )
            + f"\n\n{description}"
        )
        self.project.commit_comment(
            commit=self.commit_sha,
            body=body,
        )

    def set_status(
        self,
        state: CommitStatus,
        description: str,
        check_name: str,
        url: str = "",
    ):
        # Required because Pagure API doesn't accept empty url.
        if not url and isinstance(self.project, PagureProject):
            url = "https://wiki.centos.org/Manuals/ReleaseNotes/CentOSStream"

        logger.debug(
            f"Setting status '{state.name}' for check '{check_name}': {description}"
        )

        try:
            self.project_with_commit.set_commit_status(
                self.commit_sha, state, url, description, check_name, trim=True
            )
        except gitlab.exceptions.GitlabCreateError as e:
            # Ignoring Gitlab 'enqueue' error
            # https://github.com/packit-service/packit-service/issues/741
            if e.response_code != 400:
                # 403: No permissions to set status, falling back to comment
                # 404: Commit has not been found, e.g. used target project on GitLab
                logger.debug(
                    f"Failed to set status for {self.commit_sha}, commenting on"
                    f" commit as a fallback: {str(e)}"
                )
                self.__add_commit_comment_with_status(
                    state, description, check_name, url
                )
            if e.response_code not in {400, 403, 404}:
                raise
        except github.GithubException:
            self.__add_commit_comment_with_status(state, description, check_name, url)

        # Also set the status of the pull-request for forges which don't do
        # this automatically based on the flags on the last commit in the PR.
        self.__set_pull_request_status(check_name, description, url, state)

    def get_statuses(self):
        self.project_with_commit.get_commit_statuses(commit=self.commit_sha)

    def comment(self, body: str):
        if self.pr_id:
            self.project.get_pr(pr_id=self.pr_id).comment(body=body)
        else:
            self.project.commit_comment(commit=self.commit_sha, body=body)
